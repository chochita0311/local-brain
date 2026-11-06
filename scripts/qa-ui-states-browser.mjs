// Repeat the initial-state regressions against an owned synthetic backend only.
// node scripts/qa-ui-states-browser.mjs [outside-repository evidence directory]
import {spawn} from 'node:child_process';
import {mkdir, mkdtemp, readFile, writeFile, rm} from 'node:fs/promises';
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
const checks = [], exceptions = [];
const assert = (value, name) => {if (!value) throw new Error(name); checks.push(name);};
const backend = spawn(process.env.LOCALBRAIN_QA_PYTHON || join(repository, '.venv/bin/python'),
  [join(repository, 'tests/ui_state_fixture.py'), runtime], {cwd:repository, stdio:['ignore','ignore','pipe']});
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
  const base = `http://127.0.0.1:${port}`;
  let marker;
  for (let i=0; i<200 && !marker; i++) {
    try {marker = await (await fetch(base + '/__qa__/fixture')).json();} catch {await delay(50);}
  }
  assert(marker?.fixture === 'synthetic-ui-states-v1', 'owned synthetic backend');
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
  await send('Page.addScriptToEvaluateOnNewDocument',{source:`
    window.__qa={id:Math.random(),hold:false,release:[],searchHold:false,searchRelease:[],storageHold:false,storageRelease:[],settingsResolved:false,fail:false,ready:false,modelRunning:false,mockModelPost:false,modelPosts:0,modelSnapshot:null,frames:[],calls:[],patchDelay:0};
    const original=fetch.bind(window);
    window.fetch=async(...args)=>{
      const path=new URL(typeof args[0]==='string'?args[0]:args[0].url,location.href).pathname;
      __qa.calls.push({path,method:args[1]?.method||'GET'});
      if(path.startsWith('/api/settings/model/')){
        if(path!=='/api/settings/model/install'||!__qa.mockModelPost)throw new Error('Unexpected QA model action');
        __qa.modelPosts++;__qa.modelRunning=true;
        return new Response(JSON.stringify({...__qa.modelSnapshot,running:true,active_key:'embedding',phase:'downloading'}));
      }
      if(path==='/api/settings'){
        if(__qa.hold)await new Promise(resolve=>__qa.release.push(resolve));
        if(__qa.fail)return new Response(JSON.stringify({detail:'Synthetic read failed'}),{status:500});
        const response=await original(...args);
        __qa.settingsResolved=true;
        if(__qa.ready){const data=await response.json();data.model={...data.model,installed:true,running:__qa.modelRunning,active_key:'embedding',phase:__qa.modelRunning?'downloading':'ready',runtime_missing:[]};__qa.modelSnapshot=data.model;return new Response(JSON.stringify(data));}
        return response;
      }
      if(path==='/api/natural-search/status'&&__qa.searchHold)await new Promise(resolve=>__qa.searchRelease.push(resolve));
      if(path==='/api/natural-search/status'&&__qa.ready)return new Response(JSON.stringify({state:'ready',title:'Ready',description:'Synthetic ready state'}));
      if(path==='/api/settings/storage'&&__qa.storageHold)await new Promise(resolve=>__qa.storageRelease.push(resolve));
      if(path==='/api/settings/preferences'&&__qa.patchDelay)await new Promise(resolve=>setTimeout(resolve,__qa.patchDelay));
      return original(...args);
    };
    let phase=0;
    __qa.watch=()=>{const own=++phase,start=performance.now();__qa.frames=[];const tick=()=>{
      if(own!==phase)return;
      const d=document.querySelector('#settings-dialog'),heading=document.querySelector('[data-settings-panel="general"] h3');
      if(d?.open&&heading?.getClientRects().length)__qa.frames.push({t:performance.now()-start,y:heading.getBoundingClientRect().y,pending:document.querySelector('#settings-startup').disabled,labels:[...document.querySelectorAll('[data-general-form] [data-select-value]')].map(n=>n.textContent)});
      requestAnimationFrame(tick);
    };requestAnimationFrame(tick);};
    __qa.stopWatch=()=>{phase++;};
  `});

  await navigate('/sessions');
  await evaluate('__qa.searchHold=true;__qa.ready=true'); await click('.settings-gear');
  await wait('__qa.settingsResolved && __qa.searchRelease.length>0 && !document.querySelector("#settings-startup").disabled');
  const searchDependency = await evaluate(`({startupDisabled:document.querySelector('#settings-startup').disabled,syncDisabled:document.querySelector('#settings-session-sync').disabled,sourceAddDisabled:document.querySelector('[data-source-add]').disabled,contextAddDisabled:document.querySelector('[data-context-add]').disabled,modelInstallDisabled:document.querySelector('[data-model-action="install"]').disabled,modelPrepareDisabled:document.querySelector('[data-model-action="prepare"]').disabled})`);
  assert(!searchDependency.startupDisabled&&!searchDependency.syncDisabled&&!searchDependency.sourceAddDisabled&&!searchDependency.contextAddDisabled&&!searchDependency.modelInstallDisabled,'confirmed settings actions usable while only search readiness is pending');
  assert(searchDependency.modelPrepareDisabled,'search-dependent preparation waits for search readiness');
  await click('[data-settings-tab="search"]');
  const searchPending = await evaluate(`({text:document.querySelector('[data-search-state]').textContent,retryHidden:document.querySelector('[data-onboarding-retry]').hidden})`);
  assert(searchPending.text.includes('검색 상태를 확인하고 있습니다.')&&searchPending.retryHidden,'pending search is not presented as a failed read');
  await evaluate('__qa.searchHold=false;__qa.searchRelease.splice(0).forEach(resolve=>resolve())');
  await wait(`!document.querySelector('[data-model-action="prepare"]').disabled`);
  assert(await evaluate(`!document.querySelector('[data-model-action="prepare"]').disabled`),'search readiness enables dependent preparation');

  await navigate('/sessions');
  await evaluate('__qa.ready=true;__qa.modelRunning=true;__qa.storageHold=true'); await click('.settings-gear');
  await wait('!document.querySelector("#settings-startup").disabled');
  await click('[data-settings-tab="storage"]'); await wait('__qa.storageRelease.length>0');
  await click('[data-settings-tab="search"]');
  const storageDependency = await evaluate(`({cancelHidden:document.querySelector('[data-model-action="cancel"]').hidden,cancelDisabled:document.querySelector('[data-model-action="cancel"]').disabled})`);
  assert(!storageDependency.cancelHidden&&!storageDependency.cancelDisabled,'confirmed model cancellation remains usable during unrelated storage read');
  await evaluate('__qa.storageHold=false;__qa.storageRelease.splice(0).forEach(resolve=>resolve())');

  await navigate('/sessions');
  await evaluate('__qa.ready=true'); await click('.settings-gear'); await click('[data-settings-tab="search"]');
  await wait(`!document.querySelector('[data-model-action="prepare"]').disabled`);
  await evaluate('__qa.mockModelPost=true;__qa.searchHold=true'); await click('[data-model-action="install"]');
  await wait(`__qa.modelPosts===1 && __qa.searchRelease.length>0 && !document.querySelector('[data-model-action="cancel"]').hidden && !document.querySelector('[data-model-action="cancel"]').disabled`);
  const acknowledgedModel = await evaluate(`({posts:__qa.modelPosts,searchPending:__qa.searchRelease.length>0,cancelDisabled:document.querySelector('[data-model-action="cancel"]').disabled})`);
  assert(acknowledgedModel.posts===1&&acknowledgedModel.searchPending&&!acknowledgedModel.cancelDisabled,'acknowledged synthetic model action can be cancelled before search refresh settles');
  await evaluate('__qa.searchHold=false;__qa.searchRelease.splice(0).forEach(resolve=>resolve())');

  await navigate('/sessions');
  await evaluate('__qa.ready=true'); await click('.settings-gear'); await click('[data-settings-tab="search"]');
  await wait(`!document.querySelector('[data-model-action="prepare"]').disabled`);
  await evaluate('__qa.fail=true;__qa.searchHold=true');
  await wait(`__qa.searchRelease.length>0 && document.querySelector('[data-model-action="install"]').disabled && document.querySelector('[data-model-action="prepare"]').disabled`);
  assert(await evaluate(`document.querySelector('[data-model-status]').textContent.includes('확인하지 못했습니다')`),'failed model poll clears readiness before unrelated search response');
  await evaluate('__qa.fail=false;__qa.searchHold=false;__qa.searchRelease.splice(0).forEach(resolve=>resolve())');
  await wait(`!document.querySelector('[data-model-action="prepare"]').disabled`);
  assert(await evaluate(`!document.querySelector('[data-model-action="install"]').disabled`),'independent model poll recovers after its read succeeds');

  await navigate('/sessions');
  await evaluate('__qa.hold=true;__qa.watch()'); await click('.settings-gear');
  await wait('__qa.release.length>0 && __qa.frames.some(f=>f.pending)');
  assert(await evaluate(`JSON.stringify([...document.querySelectorAll('[data-general-form] [data-select-value]')].map(n=>n.textContent))===JSON.stringify(['Local Context','Europe/Paris'])`),'resolved labels before settings read');
  await capture('settings-pending');
  await evaluate('__qa.hold=false;__qa.release.splice(0).forEach(resolve=>resolve())');
  await wait('__qa.frames.some(f=>!f.pending) && __qa.frames.length>1');
  await evaluate('__qa.stopWatch()');
  const frames = await evaluate('__qa.frames');
  assert(frames.length>1 && frames.some(f=>f.pending) && frames.some(f=>!f.pending) && Math.max(...frames.map(f=>f.y))-Math.min(...frames.map(f=>f.y))<1,'stable content anchor through first load');
  assert(frames.every(f=>f.labels.every(Boolean)),'no blank preference frame');
  await click('[data-settings-close]'); await evaluate('__qa.watch()'); await click('.settings-gear');
  await wait('__qa.frames.length>1 && __qa.frames.some(f=>!f.pending)');
  await evaluate('__qa.stopWatch()');
  const warmFrames = await evaluate('__qa.frames');
  assert(warmFrames.length>1 && Math.max(...warmFrames.map(f=>f.y))-Math.min(...warmFrames.map(f=>f.y))<1,'stable warm reopen');
  await click('[data-settings-close]');
  await send('Emulation.setCPUThrottlingRate',{rate:4});
  await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]});
  await evaluate('__qa.hold=true;__qa.watch()');
  await send('Input.dispatchKeyEvent',{type:'keyDown',key:',',code:'Comma',modifiers:4,windowsVirtualKeyCode:188});
  await send('Input.dispatchKeyEvent',{type:'keyUp',key:',',code:'Comma',windowsVirtualKeyCode:188});
  await wait('__qa.release.length>0 && __qa.frames.some(f=>f.pending)');
  await evaluate('__qa.hold=false;__qa.release.splice(0).forEach(resolve=>resolve())');
  await wait('__qa.frames.some(f=>!f.pending) && __qa.frames.length>1');
  await evaluate('__qa.stopWatch()');
  const shortcutFrames = await evaluate('__qa.frames');
  assert(shortcutFrames.length>1 && shortcutFrames.some(f=>f.pending) && shortcutFrames.some(f=>!f.pending) && Math.max(...shortcutFrames.map(f=>f.y))-Math.min(...shortcutFrames.map(f=>f.y))<1,'shortcut and CPU4 reduced-motion read retain anchor');
  await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});
  await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});
  assert(await evaluate('!document.querySelector("#settings-dialog").open&&document.activeElement.matches(".settings-gear")'),'Escape restores settings trigger focus');
  await send('Emulation.setCPUThrottlingRate',{rate:1});
  await send('Emulation.setEmulatedMedia',{features:[]});

  const sourceFile=join(runtime,'data/session-sources.toml'), sourceBackup=await readFile(sourceFile,'utf8');
  try {
    await writeFile(sourceFile,'schema_version = [broken\n'); await navigate('/settings');
    await wait('!document.querySelector("[data-settings-loading]").getClientRects().length');
    await click('[data-settings-tab="sessions"]');
    assert(await evaluate('document.querySelector("[data-settings-message]").textContent.includes("읽지 못했습니다")'),'read failure survives category change');
    assert(await evaluate('!document.querySelector("[data-source-list]").textContent.includes("연결한 프로필이 없습니다")'),'unreadable profiles are not empty');
    assert(await evaluate('!document.querySelector("[data-onboarding-retry]").hidden'),'read failure has retry');
    await capture('profile-error'); await writeFile(sourceFile,sourceBackup); await click('[data-onboarding-retry]');
    await wait('document.querySelectorAll("[data-profile-row]").length===1');
    assert(await evaluate('document.querySelector("[data-settings-message]").textContent===""'),'retry recovers registered profile and error state');
  } finally {await writeFile(sourceFile,sourceBackup);}

  await navigate('/sessions'); await evaluate('__qa.hold=true'); await click('.settings-gear'); await wait('__qa.release.length>0');
  await click('[data-settings-tab="search"]');
  assert(await evaluate('[...document.querySelectorAll("[data-model-action]")].every(b=>b.disabled)'),'model actions locked during initial read');
  await evaluate('__qa.fail=true;__qa.hold=false;__qa.release.splice(0).forEach(resolve=>resolve())');
  await wait('document.querySelector("[data-settings-message]").textContent.includes("Synthetic read failed")');
  assert(await evaluate('[...document.querySelectorAll("[data-model-action]")].every(b=>b.disabled)'),'model actions locked after failed read');
  await evaluate('__qa.fail=false;__qa.ready=true'); await click('[data-onboarding-retry]');
  await wait('!document.querySelector("[data-model-action=prepare]").disabled');
  assert(await evaluate('!document.querySelector("[data-model-action=disable]").disabled'),'confirmed ready actions restored');
  assert(await evaluate('!__qa.calls.some(r=>r.path.startsWith("/api/settings/model/")&&r.method==="POST")'),'readiness checks execute no model action');
  await evaluate('__qa.fail=true');
  await wait('document.querySelector("[data-model-status]").textContent.includes("확인하지 못했습니다")');
  assert(await evaluate('[...document.querySelectorAll("[data-model-action],[data-generation-action]")].every(b=>b.disabled)'),'failed model poll removes action readiness');
  await evaluate('__qa.fail=false');
  await wait('!document.querySelector("[data-model-action=prepare]").disabled');
  assert(await evaluate('!document.querySelector("[data-model-action=disable]").disabled'),'successful poll restores action readiness');

  await navigate('/settings'); await wait('!document.querySelector("#settings-timezone").disabled');
  await evaluate('__qa.patchDelay=500'); await click('#settings-timezone'); await click('#settings-timezone-utc');
  await click('[data-settings-close]'); await click('.settings-gear'); await wait('!document.querySelector("#settings-timezone").disabled');
  assert(await evaluate('document.querySelector("[name=timezone]").value==="UTC"'),'pending save survives close and reopen');
  for(let i=0;i<12;i++){
    await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Tab',code:'Tab',windowsVirtualKeyCode:9});
    await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Tab',code:'Tab'});
    assert(await evaluate('document.querySelector("#settings-dialog").contains(document.activeElement)'),'focus remains in settings '+i);
  }

  await send('Fetch.enable',{patterns:[{urlPattern:'*/static/settings.js*'}]}); failSetupScript=true;
  await navigate('/sessions?setup=1&source=1');
  assert(await evaluate('document.querySelector(".app-shell").inert&&!document.querySelector("#settings-dialog").open'),'failed script preserves background isolation');
  assert(await evaluate('document.querySelector("[data-settings-startup] a").href.includes("setup=1&source=1")'),'script failure exposes scope-preserving reload');
  await capture('setup-script-failure'); failSetupScript=false; await click('[data-settings-startup] a');
  await wait('!!document.querySelector("#settings-dialog")?.open');
  assert(await evaluate('!document.querySelector("[data-settings-startup]")'),'initialized modal owns setup handoff');
  await send('Fetch.disable');
  await wait('!document.querySelector("[data-onboarding-next]").disabled'); await click('[data-onboarding-next]');
  await wait('!document.querySelector("[data-onboarding-back]").disabled'); await click('[data-source-add]');
  await evaluate('document.querySelector("[data-source-form] [name=display_label]").value="Synthetic draft"');
  await click('[data-onboarding-back]'); await wait('!document.querySelector("[data-onboarding-next]").disabled');
  await click('[data-onboarding-next]'); await wait('!document.querySelector("[data-onboarding-back]").disabled');
  assert(await evaluate('document.querySelector("[data-source-form] [name=display_label]").value==="Synthetic draft"'),'wizard Back retains source draft');
  await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]});
  await click('[data-onboarding-skip]'); await wait('!document.querySelector("[data-onboarding-next]").disabled');
  assert(await evaluate('document.getAnimations().filter(a=>a.playState==="running").length===0'),'reduced-motion wizard has no decorative transition');
  assert(await evaluate('document.querySelector(".app-shell").inert'),'wizard continues to isolate background');

  for(const width of [1440,920,700,320]){
    await send('Emulation.setDeviceMetricsOverride',{width,height:900,deviceScaleFactor:1,mobile:false});
    await navigate('/sessions');
    assert(await evaluate('document.documentElement.scrollWidth===document.documentElement.clientWidth'),'long pinned path contained at '+width);
    assert(await evaluate('(()=>{const p=document.querySelector("[data-pinned-sessions-panel]").getBoundingClientRect();return p.left>=0&&p.right<=innerWidth;})()'),'pinned panel stays inside viewport at '+width);
    await navigate('/settings'); await wait('!document.querySelector("#settings-startup").disabled');
    assert(await evaluate('document.documentElement.scrollWidth===document.documentElement.clientWidth'),'settings contained at '+width);
    await click('#settings-timezone');
    assert(await evaluate('(()=>{const r=document.querySelector("#settings-timezone-options").getBoundingClientRect(),d=document.querySelector("#settings-dialog").getBoundingClientRect();return r.width>0&&r.left>=d.left&&r.right<=d.right;})()'),'expanded preference menu contained at '+width);
    await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});
    await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});
    assert(await evaluate('document.querySelector("#settings-dialog").open&&document.querySelector("#settings-timezone-options").hidden'),'menu Escape preserves settings at '+width);
  }
  await send('Emulation.setDeviceMetricsOverride',{width:701,height:400,deviceScaleFactor:1,mobile:false});
  await navigate('/settings'); await wait('!document.querySelector("#settings-startup").disabled');
  assert(await evaluate('(()=>{const d=document.querySelector("#settings-dialog").getBoundingClientRect();return d.top>=0&&d.bottom<=innerHeight&&innerWidth===701&&document.documentElement.scrollWidth===document.documentElement.clientWidth;})()'),'short settings frame remains contained');
  assert(await evaluate('(()=>{const b=document.querySelector(".settings-body");b.scrollTop=b.scrollHeight;return b.clientHeight>0&&document.querySelector("#settings-timezone-help").getBoundingClientRect().bottom<=b.getBoundingClientRect().bottom;})()'),'short settings body reaches final help text');
  await navigate('/runs/qa-completed');
  assert(await evaluate('document.querySelector("[data-run-output]").textContent==="표시할 실행 출력이 없습니다."'),'completed Run has neutral missing-output text');
  await navigate('/runs/qa-queued');
  await evaluate(`fetch=async(...args)=>String(args[0]).includes('/api/runs/')?new Response(JSON.stringify({ok:true,run:{status:'completed',status_label:'완료',output:'',output_placeholder:'표시할 실행 출력이 없습니다.'}})):original(...args)`);
  await wait('document.querySelector("[data-run-status]").textContent==="완료"');
  assert(await evaluate('!document.querySelector("[data-run-output]").textContent.includes("준비")'),'polling clears queued placeholder at completion');
  await navigate('/runs/qa-queued');
  await evaluate(`fetch=async(...args)=>String(args[0]).includes('/api/runs/')?new Response(JSON.stringify({ok:true,run:{status:'running',status_label:'실행 중',output:'Synthetic preserved output',output_placeholder:'아직 표시할 실행 출력이 없습니다.'}})):original(...args)`);
  await wait('document.querySelector("[data-run-output]").textContent==="Synthetic preserved output"');
  await evaluate(`fetch=async(...args)=>String(args[0]).includes('/api/runs/')?new Response(JSON.stringify({ok:true,run:{status:'completed',status_label:'완료',output:'',output_placeholder:'표시할 실행 출력이 없습니다.'}})):original(...args)`);
  await wait('document.querySelector("[data-run-status]").textContent==="완료"');
  assert(await evaluate('document.querySelector("[data-run-output]").textContent==="Synthetic preserved output"'),'empty terminal poll preserves already displayed output');
  assert(exceptions.length===0,'no application Runtime exception');
  await writeFile(join(output,'result.json'),JSON.stringify({result:'PASS',checks,searchDependency,searchPending,storageDependency,acknowledgedModel,firstLoadFrames:frames,warmReopenFrames:warmFrames,shortcutFrames,exceptions},null,2));
  console.log(JSON.stringify({result:'PASS',checks:checks.length,evidence:process.argv[2]?output:'removed after verification'}));
} catch(error) {
  await writeFile(join(output,'failure.json'),JSON.stringify({error:error.message,checks,exceptions},null,2));
  throw error;
} finally {
  socket?.close();
  for(const waiter of pending.values())clearTimeout(waiter.timer);
  await stop(chrome,'SIGTERM'); await stop(backend,'SIGINT');
  await rm(profile,{recursive:true,force:true}); await rm(runtime,{recursive:true,force:true});
  if(!process.argv[2])await rm(output,{recursive:true,force:true});
}
