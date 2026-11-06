// Verify public desktop entries against an owned synthetic backend only.
// node scripts/qa-trial-delivery-browser.mjs [outside-repository evidence directory]
import {spawn} from 'node:child_process';
import {mkdir, mkdtemp, readFile, writeFile, rm, rename, realpath} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {dirname, join, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

const repository = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const destination = process.argv[2] ? resolve(process.argv[2]) : tmpdir();
if (destination === repository || destination.startsWith(repository + '/')) throw new Error('Evidence must stay outside the repository');
if (typeof WebSocket === 'undefined') throw new Error('Browser QA requires Node with the built-in WebSocket API (Node 22+)');
await mkdir(destination, {recursive:true});
const output = await mkdtemp(join(destination, 'localbrain-ui-state-'));
const runtime = join(output, 'runtime'), profile = join(output, 'chrome-profile');
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const checks = [], exceptions = [], failedRequests = [];
let base;
const assert = (value, name) => {if (!value) throw new Error(name); checks.push(name);};
const backend = spawn(process.env.LOCALBRAIN_QA_PYTHON || join(repository, '.venv/bin/python'),
  [join(repository, 'tests/ui_state_fixture.py'), runtime, 'desktop'], {cwd:repository, stdio:['ignore','ignore','pipe']});
let backendError = '';
backend.stderr.on('data', chunk => {backendError = (backendError + chunk.toString()).slice(-4000);});
backend.on('error', error => {backendError = error.message;});
let chrome, socket, send, evaluate;
const pending = new Map();
async function stop(child, signal) {
  if (!child?.pid || child.exitCode !== null || child.signalCode !== null) return;
  const ended = new Promise(resolve => child.once('exit', resolve));
  child.kill(signal); await Promise.race([ended, delay(3000)]);
  if (child.exitCode === null && child.signalCode === null) {child.kill('SIGKILL'); await ended;}
}
try {
  let port;
  for (let i=0; i<200 && !port; i++) {
    try {port = JSON.parse(await readFile(join(runtime,'port.json'),'utf8')).port;} catch {}
    if (backend.exitCode !== null || backend.signalCode !== null) throw new Error('Synthetic backend failed: ' + backendError);
    if (!port) await delay(50);
  }
  if (!port) throw new Error('Synthetic backend did not start: ' + backendError);
  base = `http://127.0.0.1:${port}`;
  let marker;
  for (let i=0; i<200 && !marker; i++) {
    try {marker = await (await fetch(base + '/api/health',{headers:{Authorization:'Bearer synthetic-qa-token'}})).json();} catch {await delay(50);}
  }
  assert(marker?.edition === 'desktop', 'owned synthetic backend');
  chrome = spawn(process.env.LOCALBRAIN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', [
    '--headless=new','--disable-gpu','--disable-background-networking','--disable-component-update',
    '--no-first-run','--no-default-browser-check','--remote-debugging-port=0',`--user-data-dir=${profile}`,
    '--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1, EXCLUDE localhost','about:blank',
  ], {stdio:'ignore'});
  let browserError, debugPort;
  chrome.on('error', error => {browserError = error.message;});
  for (let i=0; i<150 && !debugPort; i++) {
    if (browserError) throw new Error(browserError);
    try {debugPort = Number((await readFile(join(profile,'DevToolsActivePort'),'utf8')).split('\n')[0]);} catch {await delay(50);}
  }
  if (!debugPort) throw new Error('Chrome did not start');
  const target = await (await fetch(`http://127.0.0.1:${debugPort}/json/new?about:blank`,{method:'PUT'})).json();
  socket = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve,reject) => {socket.addEventListener('open',resolve,{once:true}); socket.addEventListener('error',reject,{once:true});});
  let sequence = 0, failSetupScript = false;
  send = (method, params={}) => new Promise((resolve,reject) => {
    const id = ++sequence, timer = setTimeout(() => {pending.delete(id); reject(new Error('CDP timeout: '+method));},20000);
    pending.set(id,{resolve,reject,timer}); socket.send(JSON.stringify({id,method,params}));
  });
  socket.addEventListener('message', event => {
    const value = JSON.parse(event.data);
    if (value.id) {
      const waiter = pending.get(value.id); if (!waiter) return;
      pending.delete(value.id); clearTimeout(waiter.timer);
      value.error ? waiter.reject(new Error(JSON.stringify(value.error))) : waiter.resolve(value.result);
    } else if (value.method === 'Runtime.exceptionThrown') exceptions.push(value.params.exceptionDetails.text);
    else if(value.method==='Network.responseReceived' && value.params.response.status>=400) failedRequests.push({url:value.params.response.url,status:value.params.response.status});
    else if (value.method === 'Fetch.requestPaused') {
      const requestId = value.params.requestId;
      void send(failSetupScript ? 'Fetch.failRequest' : 'Fetch.continueRequest',
        failSetupScript ? {requestId,errorReason:'Failed'} : {requestId}).catch(() => {});
    }
  });
  evaluate = async expression => {
    const response = await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});
    if (response.exceptionDetails) throw new Error(response.exceptionDetails.exception?.description || response.exceptionDetails.text);
    return response.result.value;
  };
  const wait = async expression => {
    for (let i=0; i<250; i++) {if (await evaluate(expression)) return; await delay(30);}
    throw new Error('State timeout: '+expression);
  };
  const navigate = async path => {
    const old = await evaluate('window.__qa?.id ?? null');
    await send('Page.navigate',{url:base+path});
    await wait(`window.__qa && __qa.id!==${JSON.stringify(old)} && document.readyState==='complete' && !!document.querySelector('.app-shell')`);
  };
  const click = async selector => {
    const point = await evaluate(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(!e)throw new Error('Missing control');e.scrollIntoView({block:'nearest'});const r=e.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})()`);
    await send('Input.dispatchMouseEvent',{type:'mouseMoved',...point});
    await send('Input.dispatchMouseEvent',{type:'mousePressed',button:'left',clickCount:1,...point});
    await send('Input.dispatchMouseEvent',{type:'mouseReleased',button:'left',clickCount:1,...point});
  };
  const capture = async name => {
    const image = await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
    await writeFile(join(output,name+'.png'),Buffer.from(image.data,'base64'));
  };
  await send('Page.enable'); await send('Runtime.enable'); await send('Network.enable');
  await send('Network.setCacheDisabled',{cacheDisabled:true});
  await send('Emulation.setDeviceMetricsOverride',{width:1440,height:900,deviceScaleFactor:1,mobile:false});
  await send('Network.setExtraHTTPHeaders',{headers:{Authorization:'Bearer synthetic-qa-token'}});
  await send('Page.addScriptToEvaluateOnNewDocument',{source:`
    window.__qa={id:Math.random(),storageHold:false,storageRelease:[],storageFail:false,storageOverride:null};
    const originalFetch=fetch.bind(window);
    window.fetch=async(...args)=>{
      if(new URL(String(args[0]),location.href).pathname==='/api/settings/storage') {
        if(__qa.storageHold) await new Promise(resolve=>__qa.storageRelease.push(resolve));
        if(__qa.storageFail) return new Response(JSON.stringify({detail:'Synthetic storage read failure'}),{status:500});
        if(__qa.storageOverride) return new Response(JSON.stringify(__qa.storageOverride));
      }
      return originalFetch(...args);
    };
  `});
  for(const mode of ['', '?display=chart']) {
    await navigate('/sessions'+mode);
    assert(await evaluate(`!document.querySelector('a[href^="/workstreams"],a[href^="/sources"],a[href*="/workflow"]')`),'no hidden links '+mode);
    const selector=mode?'[data-settings-open]':'[data-settings-open="sessions"]';
    await click(selector); await wait('document.querySelector("#settings-dialog").open');
    if(mode) await click('[data-settings-tab="sessions"]');
    await wait('document.querySelector("[data-source-add]")?.disabled===false');
    assert(await evaluate(`document.querySelector('[data-settings-panel="sessions"]')?.hidden===false`),'source settings opens '+mode);
    await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});
    await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});
    await wait('!document.querySelector("#settings-dialog").open');
    assert(await evaluate('location.pathname+location.search')==='/sessions'+mode,'dialog retains session view '+mode);
  }
  for(const path of ['/sessions/1','/sessions-dashboard','/projects','/context','/documents/1','/natural-search?mode=keyword&q=synthetic','/help']) {
    await navigate(path);
    assert(await evaluate(`!document.querySelector('a[href^="/workstreams"],a[href^="/sources"],a[href*="/workflow"],a[href^="/atlassian"]')`),'public-only links '+path);
  }
  for(const outcome of ['complete','partial','failed']) {
    await navigate('/sessions?display=chart&sync='+outcome);
    assert(await evaluate(`!!document.querySelector('#session-sync-result [data-settings-open="sessions"]') && !document.querySelector('a[href="/sources"]')`),'Chart sync recovery uses available settings '+outcome);
    await click('#session-sync-result [data-settings-open="sessions"]');
    await wait('document.querySelector("#settings-dialog").open && !document.querySelector("[data-source-add]").disabled');
    await click('[data-settings-close]');
    await wait('!document.querySelector("#settings-dialog").open');
  }
  const canonicalRuntime=await realpath(runtime);
  const recordRoot=join(canonicalRuntime,'codex/sessions');
  await writeFile(join(recordRoot,'qa.jsonl'),[
    {type:'session_meta',timestamp:'2026-11-01T00:00:00Z',payload:{id:'synthetic-ui-qa',cwd:join(canonicalRuntime,'workspaces','long-synthetic-path-'.repeat(9))}},
    {type:'event_msg',timestamp:'2026-11-01T00:01:00Z',payload:{type:'user_message',message:'Synthetic trial synchronization'}}
  ].map(row=>JSON.stringify(row)).join('\n')+'\n');
  for(const outcome of ['complete','partial','failed']) {
    const profiles=[{source_id:1,provider_kind:'codex',display_label:'Synthetic QA',root:recordRoot,agent_home:join(canonicalRuntime,'codex'),color:'green'}];
    if(outcome!=='complete')profiles.push({source_id:99,provider_kind:'codex',display_label:'Synthetic unavailable',root:join(canonicalRuntime,'missing-profile'),color:'blue'});
    await writeFile(join(runtime,'data/session-sources.toml'),'schema_version = 2\n'+profiles.map(profile=>'\n[[session_sources]]\n'+Object.entries(profile).map(([key,value])=>key+' = '+JSON.stringify(value)).join('\n')).join('\n'));
    if(outcome==='failed') await rename(recordRoot,recordRoot+'-offline');
    await navigate('/sessions?display=chart');
    await wait('!document.querySelector("#session-sync-button").disabled');
    const generation=await evaluate('(async()=>Number((await(await fetch("/api/sessions/sync/status")).json()).generation||0))()');
    await click('#session-sync-button');
    await wait(`(async()=>{const value=await(await fetch('/api/sessions/sync/status')).json();return !value.running&&!value.queued&&Number(value.generation||0)>${generation};})()`);
    const actual=await evaluate('(async()=>(await(await fetch("/api/sessions/sync/status")).json()).outcome)()');
    if(actual!==outcome) await writeFile(join(output,'sync-failure.json'),JSON.stringify(await evaluate('(async()=>(await(await fetch("/api/sessions/sync/status")).json()))()'),null,2));
    assert(actual===outcome,'actual synchronization transition '+outcome+' observed '+actual);
    assert(await evaluate('location.pathname+location.search')==='/sessions?display=chart','background completion retains Chart '+outcome);
    if(outcome==='failed')await rename(recordRoot+'-offline',recordRoot);
  }
  for(const slug of ['', 'settings','sessions-dashboard','sessions','local-contexts','search']) {
    for(const lang of ['ko','en']) {
      await navigate('/help'+(slug?'/'+slug:'')+'?lang='+lang);
      assert(await evaluate(`document.querySelector('.app-docs').lang===${JSON.stringify(lang)} && !!document.querySelector('.app-docs-body')`),'bundled guide '+slug+' '+lang);
      assert(await evaluate(`document.querySelectorAll('.app-docs-contents [data-docs-language]').length===1 && !document.querySelector('.app-docs-article [data-docs-language]')`),'shared Docs language option '+slug+' '+lang);
      assert(await evaluate(`Array.from(document.querySelectorAll('.app-docs a[href^="/help"]')).every(a=>new URL(a.href).searchParams.has('lang'))`),'guide links keep language '+slug+' '+lang);
    }
  }
  await navigate('/help/settings');
  assert(await evaluate('document.querySelector(".app-docs")?.lang==="ko"'),'bare Docs defaults Korean');
  assert(await evaluate('!document.querySelector("[data-docs-language]").open'),'language options initially collapsed');
  await click('[data-docs-language] summary');
  await wait('document.querySelector("[data-docs-language]").open');
  await capture('docs-language-menu-wide');
  await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});
  await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});
  assert(await evaluate('!document.querySelector("[data-docs-language]").open && document.activeElement===document.querySelector("[data-docs-language] summary")'),'language Escape closes and returns focus');
  await click('[data-docs-language] summary'); await click('#guide-title');
  assert(await evaluate('!document.querySelector("[data-docs-language]").open'),'outside click dismisses language options');
  const shellLanguage=await evaluate('document.querySelector(".lnb").innerText');
  await click('[data-docs-language] summary');
  await click('.app-docs-language a[lang="en"]');
  await wait('location.search==="?lang=en" && document.readyState==="complete" && document.querySelector(".app-docs")?.lang==="en"');
  assert(await evaluate('location.pathname==="/help/settings"'),'language retains topic');
  assert(await evaluate('document.querySelector(".lnb").innerText')===shellLanguage,'Docs option preserves surrounding app language');
  await click('.app-docs-topic[href="/help/search?lang=en"]');
  await wait('location.pathname==="/help/search" && document.readyState==="complete" && document.querySelector("#guide-title").textContent==="Search"');
  await evaluate('history.back()');
  await wait('location.pathname==="/help/settings" && document.readyState==="complete" && document.querySelector("#guide-title").textContent==="Settings" && document.querySelector(".app-docs")?.lang==="en"');
  assert(true,'guide history returns to same language and topic');
  await evaluate(`document.querySelector('[data-docs-language] summary').focus()`);
  await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Enter',code:'Enter',windowsVirtualKeyCode:13,text:'\r',unmodifiedText:'\r'});
  await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Enter',code:'Enter',windowsVirtualKeyCode:13});
  await wait('document.querySelector("[data-docs-language]").open');
  await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Tab',code:'Tab',windowsVirtualKeyCode:9});
  await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Tab',code:'Tab',windowsVirtualKeyCode:9});
  assert(await evaluate('document.activeElement.lang==="ko"'),'keyboard reaches first language option');
  await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Enter',code:'Enter',windowsVirtualKeyCode:13,text:'\r',unmodifiedText:'\r'});
  await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Enter',code:'Enter',windowsVirtualKeyCode:13});
  await wait('location.search==="?lang=ko" && document.querySelector(".app-docs")?.lang==="ko"');
  assert(true,'keyboard language switch');
  await send('Fetch.enable',{patterns:[{urlPattern:'*/static/app-docs.js*'}]}); failSetupScript=true;
  await navigate('/help/settings?lang=en');
  await click('[data-docs-language] summary'); await click('.app-docs-language a[lang="ko"]');
  await wait('document.querySelector(".app-docs")?.lang==="ko"');
  assert(true,'native language disclosure and links survive controller failure');
  failSetupScript=false;await send('Fetch.disable');
  await navigate('/settings'); await wait('!document.querySelector("#settings-startup").disabled');
  await evaluate('__qa.storageHold=true');
  await click('[data-settings-tab="storage"]');
  await wait('document.querySelector("[data-storage-summary]").getAttribute("aria-busy")==="true"');
  assert(await evaluate('document.querySelector("[data-storage-pending]").textContent.includes("확인")'),'storage pending is explicit');
  await evaluate('__qa.storageHold=false;__qa.storageRelease.splice(0).forEach(resolve=>resolve())');
  await wait('!!document.querySelector("[data-storage-summary] .settings-group")');
  assert(await evaluate('document.querySelector("[data-storage-summary]").textContent.includes("GiB") && document.querySelector("[data-storage-summary]").textContent.includes("다른 앱")'),'storage units and shared cache scope');
  await capture('storage-ready');
  await evaluate('__qa.storageFail=true'); await click('[data-storage-reload]');
  await wait('!!document.querySelector("[data-storage-error]")');
  assert(await evaluate('!!document.querySelector("[data-storage-summary] .settings-group")'),'failed refresh preserves confirmed sizes');
  await click('[data-settings-tab="general"]'); await click('[data-settings-tab="storage"]');
  await wait('!document.querySelector("[data-storage-reload]").disabled');
  assert(await evaluate('!!document.querySelector("[data-storage-error]")'),'storage failure survives category change');
  await evaluate('__qa.storageFail=false'); await click('[data-storage-reload]');
  await wait('!document.querySelector("[data-storage-error]") && !document.querySelector("[data-storage-reload]").disabled');
  assert(true,'storage retry recovers');
  await evaluate(`(async()=>{const data=await (await fetch('/api/settings/storage')).json();
    data.locations.cache={bytes:null,state:'unavailable',volume:{id:'app',free_bytes:1024**3,state:'complete'}};
    data.locations.data.volume={id:'app',free_bytes:1024**3,state:'complete'};
    data.locations.models={bytes:1024**3,state:'partial',volume:{id:'models',free_bytes:2*1024**3,state:'complete'}};
    __qa.storageOverride=data;})()`);
  await click('[data-storage-reload]');
  await wait('document.querySelector("[data-storage-summary]").textContent.includes("일부만 집계")');
  assert(await evaluate('document.querySelector("[data-storage-summary]").textContent.includes("확인 불가")'),'unavailable size is not zero');
  assert(await evaluate('Array.from(document.querySelectorAll("[data-storage-summary] p")).filter(p=>p.textContent.includes("위치의 사용 가능한 공간")).length===2'),'distinct volumes shown once each');
  await capture('storage-partial');
  for(const width of [1440,920,700,320]) {
    await send('Emulation.setDeviceMetricsOverride',{width,height:900,deviceScaleFactor:1,mobile:false});
    await navigate('/sessions');
    assert(await evaluate('document.documentElement.scrollWidth===document.documentElement.clientWidth'),'session containment '+width);
    await capture('sessions-'+width);
    await navigate('/help/settings');
    assert(await evaluate('document.documentElement.scrollWidth===document.documentElement.clientWidth'),'Docs containment '+width);
    await capture('docs-'+width);
    await click('[data-docs-language] summary');
    assert(await evaluate(`(()=>{const trigger=document.querySelector('[data-docs-language] summary').getBoundingClientRect(), menu=document.querySelector('.app-docs-language-options').getBoundingClientRect(), link=document.querySelector('.app-docs-language a').getBoundingClientRect(), hit=document.elementFromPoint(link.x+link.width/2,link.y+link.height/2);return menu.top>=trigger.bottom && menu.left>=0 && menu.right<=innerWidth && !!hit?.closest('.app-docs-language-options');})()`),'language menu belongs below trigger and remains reachable '+width);
    await capture('docs-language-open-'+width);
    await click('[data-docs-language] summary');
    await navigate('/settings'); await wait('!document.querySelector("#settings-startup").disabled');
    await click('[data-settings-tab="storage"]');
    await wait('!!document.querySelector("[data-storage-summary] .settings-group")');
    assert(await evaluate('document.documentElement.scrollWidth===document.documentElement.clientWidth'),'storage containment '+width);
    await capture('storage-'+width);
  }
  await delay(1600);
  assert(exceptions.length===0,'no runtime exceptions');
  assert(failedRequests.length===0,'no failing background or navigation requests');
  await writeFile(join(output,'result.json'),JSON.stringify({result:'PASS',checks,exceptions,failedRequests},null,2));
  console.log(JSON.stringify({result:'PASS',checks:checks.length,evidence:output}));
} catch(error) {
  await writeFile(join(output,'failure.json'),JSON.stringify({error:error.message,checks,exceptions,failedRequests},null,2));
  throw error;
} finally {
  socket?.close();
  for(const waiter of pending.values())clearTimeout(waiter.timer);
  await stop(chrome,'SIGTERM'); await stop(backend,'SIGINT');
  await rm(profile,{recursive:true,force:true}); await rm(runtime,{recursive:true,force:true});
  if(!process.argv[2])await rm(output,{recursive:true,force:true});
}
