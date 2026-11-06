// Verify public desktop entries against an owned synthetic backend only.
// node scripts/qa-navigation-browser.mjs [outside-repository evidence directory]
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
  [join(repository, 'tests/ui_state_fixture.py'), runtime, 'desktop', 'navigation'], {cwd:repository, stdio:['ignore','ignore','pipe']});
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
  let sequence = 0, failSetupScript = false, failChartPreference = false;
  const visibilityWrites = [], traversalSamples = [];
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
    } else if (value.method === 'Runtime.consoleAPICalled' && value.params.args?.[0]?.value === '__navigation_sample__') traversalSamples.push(JSON.parse(value.params.args[1].value));
    else if (value.method === 'Network.requestWillBeSent' && value.params.request.method === 'PUT' && value.params.request.url.includes('/sessions/chart/project-visibility')) visibilityWrites.push(value.params.request.url);
    else if (value.method === 'Runtime.exceptionThrown') exceptions.push(value.params.exceptionDetails.text);
    else if(value.method==='Network.responseReceived' && value.params.response.status>=400) failedRequests.push({url:value.params.response.url,status:value.params.response.status});
    else if (value.method === 'Fetch.requestPaused') {
      const requestId = value.params.requestId;
      if (failChartPreference && value.params.responseStatusCode) {
        void (async () => {
          const response = await send('Fetch.getResponseBody', {requestId});
          const html = response.base64Encoded ? Buffer.from(response.body, 'base64').toString() : response.body;
          const unavailable = JSON.stringify({available:false,hidden_projects:null});
          const body = html.replace(/(<script[^>]*data-chart-project-preference[^>]*>)[\s\S]*?(<\/script>)/, (_all,start,end) => start + unavailable + end);
          if (body === html) throw new Error('Missing synthetic Chart preference target');
          const responseHeaders = value.params.responseHeaders.filter(header => !['content-length','content-encoding'].includes(header.name.toLowerCase()));
          await send('Fetch.fulfillRequest', {requestId,responseCode:200,responseHeaders,body:Buffer.from(body).toString('base64')});
        })().catch(error => exceptions.push(error.message));
      } else {
        void send(failSetupScript ? 'Fetch.failRequest' : 'Fetch.continueRequest',
          failSetupScript ? {requestId,errorReason:'Failed'} : {requestId}).catch(() => {});
      }
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
    window.__qa={id:Math.random(),holdDocument:null,releases:[]};
    const originalFetch=fetch.bind(window);
    window.fetch=async(...args)=>{
      const destination=new URL(String(args[0]),location.href);
      if(__qa.holdDocument && destination.pathname==='/context' && destination.searchParams.get('document')===__qa.holdDocument) {
        await new Promise((resolve,reject)=>{
          __qa.releases.push(resolve);
          const signal=args[1]?.signal;
          if(signal?.aborted)reject(new DOMException('Aborted','AbortError'));
          else signal?.addEventListener('abort',()=>reject(new DOMException('Aborted','AbortError')),{once:true});
        });
      }
      return originalFetch(...args);
    };
  `});
  const back=async(expected)=>{
    await click('[data-app-back]');
    await wait(`location.pathname+location.search+location.hash===${JSON.stringify(expected)} && document.readyState==='complete'`);
    await delay(160);
  };
  await navigate('/sessions?source=1');
  assert(await evaluate('document.querySelector("[data-app-back]").disabled'),'first deep link has no app predecessor');
  assert(await evaluate('(()=>{const b=document.querySelector("[data-app-back]");b.focus();return document.activeElement!==b;})()'),'disabled Back is excluded from keyboard focus');
  assert(await evaluate('!document.querySelector(".page-location") && !!document.querySelector("h1")'),'toolbar replaces location label and retains body heading');
  const sessionHref=await evaluate(`Array.from(document.querySelectorAll('a[href^="/sessions/"]')).find(a=>new URL(a.href).pathname==='/sessions/1').getAttribute('href')`);
  await click(`a[href=${JSON.stringify(sessionHref)}]`);
  await wait('location.pathname==="/sessions/1" && document.readyState==="complete"');
  assert(await evaluate('!document.querySelector("[data-app-back]").disabled'),'detail can go back');
  await evaluate('document.querySelector("[data-app-back]").focus()');
  await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Enter',code:'Enter',windowsVirtualKeyCode:13,nativeVirtualKeyCode:13,text:'\r'});
  await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Enter',code:'Enter',windowsVirtualKeyCode:13,nativeVirtualKeyCode:13});
  await wait('location.pathname+location.search==="/sessions?source=1" && document.readyState==="complete"');
  assert(true,'keyboard Enter activates chronological Back');
  await evaluate('history.forward()');
  await wait('location.pathname==="/sessions/1" && document.readyState==="complete"');
  await evaluate('document.fonts.ready.then(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))))');

  await evaluate('window.scrollTo(0,600)'); await delay(160);
  const detailScroll=await evaluate('scrollY');
  assert(detailScroll>300,'Session fixture supports real window scroll');
  await click('.lnb a[href="/context"]'); await wait('location.pathname==="/context" && document.readyState==="complete"');
  const contextStart=await evaluate('location.pathname+location.search');
  const documentLinks=await evaluate(`Array.from(document.querySelectorAll('[data-context-document-link]')).map(a=>({href:a.getAttribute('href'),id:new URL(a.href).searchParams.get('document')}))`);
  assert(documentLinks.length>=3,'fixture has multiple documents');
  const first=documentLinks[0], second=documentLinks[1];
  await click(`[data-context-document-link][href=${JSON.stringify(first.href)}]`);
  await wait(`new URL(location.href).searchParams.get('document')===${JSON.stringify(first.id)} && document.querySelector('[data-context-preview]').getAttribute('aria-busy')==='false'`);
  await evaluate(`document.querySelector('[data-context-preview]').scrollTop=480`);await delay(160);
  const paneScroll=await evaluate(`document.querySelector('[data-context-preview]').scrollTop`);
  assert(paneScroll>200,'preview fixture supports real pane scroll');
  await click(`[data-context-document-link][href=${JSON.stringify(second.href)}]`);
  await wait(`new URL(location.href).searchParams.get('document')===${JSON.stringify(second.id)} && document.querySelector('[data-context-preview]').getAttribute('aria-busy')==='false'`);
  await back(first.href);
  assert(await evaluate(`document.querySelector('[data-context-preview]').dataset.contextDocumentId===${JSON.stringify(first.id)}`),'Back restores selected preview');
  assert(Math.abs((await evaluate(`document.querySelector('[data-context-preview]').scrollTop`))-paneScroll)<3,'Back restores preview pane scroll');
  await back(contextStart);await back(sessionHref);
  assert(Math.abs((await evaluate('scrollY'))-detailScroll)<3,'cross-screen Back restores Session scroll');
  await back('/sessions?source=1');
  assert(await evaluate('document.querySelector("[data-app-back]").disabled'),'returned first app entry disables Back');
  await send('Page.reload');await wait('document.readyState==="complete" && !!document.querySelector("[data-app-back]")');await delay(150);
  assert(await evaluate('document.querySelector("[data-app-back]").disabled'),'reload adds no history point');
  await click('.lnb a[href="/context"]');await wait('location.pathname==="/context" && document.readyState==="complete"');
  await click('.lnb a[href="/help"]');await wait('location.pathname==="/help" && document.readyState==="complete"');
  assert(await evaluate('document.querySelector(".app-docs-tools .eyebrow").textContent==="목차"'),'Docs contents label replaces brand repetition');
  await back('/context');
  await click('.lnb a[href="/sessions-dashboard"]');await wait('location.pathname==="/sessions-dashboard" && document.readyState==="complete"');
  await back('/context');
  assert(await evaluate(`!JSON.parse(sessionStorage.getItem('localbrain:navigation:1')).entries.some(e=>e.href.endsWith('/help'))`),'new visit truncates forward branch');
  await evaluate('history.forward()');await wait('location.pathname==="/sessions-dashboard" && document.readyState==="complete"');
  assert(true,'browser Forward remains usable');
  await click('.lnb a[href="/sessions"]');await wait('location.pathname==="/sessions" && document.readyState==="complete"');
  await click('[data-inventory-view="projects"]');await wait('location.pathname==="/projects"');
  assert(await evaluate('!!history.state.inventory && !!history.state.localbrainNavigation'),'partial inventory preserves feature state and marker');
  await back('/sessions');
  assert(await evaluate('document.querySelector("[data-inventory-panel=sessions]").hidden===false'),'partial inventory Back renders correct pane');
  await navigate('/help?lang=en');
  assert(await evaluate('document.querySelector(".app-docs-tools .eyebrow").textContent==="Contents"'),'English contents label');
  await navigate(first.href);
  await evaluate(`__qa.holdDocument=${JSON.stringify(second.id)}`);
  await click(`[data-context-document-link][href=${JSON.stringify(second.href)}]`);
  await wait('document.querySelector("[data-context-preview]").getAttribute("aria-busy")==="true"');
  await click('.lnb a[href="/sessions"]');await wait('location.pathname==="/sessions" && document.readyState==="complete"');
  await back(first.href);
  await wait(`document.querySelector('[data-context-preview]').dataset.contextDocumentId===${JSON.stringify(first.id)} && document.querySelector('[data-context-preview]').getAttribute('aria-busy')==='false'`);
  await evaluate('__qa.holdDocument=null;__qa.releases.splice(0).forEach(resolve=>resolve())');await delay(180);
  assert(await evaluate('location.pathname+location.search')===first.href,'abandoned preview cannot commit after cross-screen Back');
  const readerHref=await evaluate(`document.querySelector('[data-context-preview] a[href^="/documents/"]').getAttribute('href')`);
  await click(`[data-context-preview] a[href=${JSON.stringify(readerHref)}]`);
  await wait(`location.pathname==='/documents/'+${JSON.stringify(first.id)} && document.readyState==='complete'`);
  const firstReaderUrl=await evaluate('location.pathname+location.search');
  const nextReader=await evaluate(`Array.from(document.querySelectorAll('[data-document-reader-link]')).find(a=>new URL(a.href).pathname==='/documents/'+${JSON.stringify(second.id)}).getAttribute('href')`);
  await click(`[data-document-reader-link][href=${JSON.stringify(nextReader)}]`);
  await wait(`document.querySelector('[data-document-reader-content]').dataset.documentId===${JSON.stringify(second.id)} && document.querySelector('[data-document-reader-content]').getAttribute('aria-busy')==='false'`);
  await back(firstReaderUrl);
  await wait(`document.querySelector('[data-document-reader-content]').dataset.documentId===${JSON.stringify(first.id)} && document.querySelector('[data-document-reader-content]').getAttribute('aria-busy')==='false'`);
  assert(true,'full reader partial Back restores its document');
  await navigate('/sessions-dashboard');
  const usageStart=await evaluate('location.pathname+location.search');
  const metricHref=await evaluate(`Array.from(document.querySelectorAll('[data-usage-control="metric"]')).find(a=>!a.hasAttribute('aria-current')).getAttribute('href')`);
  await click(`[data-usage-control="metric"][href=${JSON.stringify(metricHref)}]`);
  await wait(`location.pathname+location.search===${JSON.stringify(metricHref)} && document.querySelector('[data-usage-dashboard]').getAttribute('aria-busy')==='false'`);
  assert(await evaluate('history.state.usageDashboard && !!history.state.localbrainNavigation'),'usage payload survives shared marker');
  await back(usageStart);
  await wait('document.querySelector("[data-usage-dashboard]").getAttribute("aria-busy")==="false"');
  assert(true,'Dashboard filter Back settles target view');
  await navigate('/sessions?display=chart');
  await wait('!!document.querySelector(".session-chart-node")');
  await click('.session-chart-node');await delay(120);
  const chartView=await evaluate('LocalBrainNavigation.getView("sessionChart")');
  assert(chartView?.selected>0,'Chart captures entry selection');
  assert(await evaluate('!document.querySelector("[data-inventory-switch]")'),'Chart excludes same-document inventory switching');
  const chartDocument=await evaluate('__qa.id');
  await click('[data-inventory-view="projects"]');
  await wait(`location.pathname==='/projects' && document.readyState==='complete' && __qa.id!==${JSON.stringify(chartDocument)}`);
  assert(true,'Chart to Projects is a full document visit');
  await back('/sessions?display=chart');
  await wait('!!document.querySelector(".session-chart-node")');
  assert(await evaluate('LocalBrainNavigation.getView("sessionChart").selected')===chartView.selected,'Chart state restores after native Projects visit');
  await click('.lnb a[href="/context"]');await wait('location.pathname==="/context" && document.readyState==="complete"');
  await back('/sessions?display=chart');
  await wait('!!document.querySelector(".session-chart-node")');
  assert(await evaluate('LocalBrainNavigation.getView("sessionChart").selected')===chartView.selected,'Chart selection survives cross-screen Back');
  await click('[data-chart-project-filter] summary');
  const hiddenProject = await evaluate("document.querySelector('[data-chart-project-options] input').dataset.projectKey");
  await click('[data-chart-project-options] input');await delay(300);
  const visibilityKey = await evaluate("Object.keys(sessionStorage).find(key=>key.startsWith('localbrain:session-chart:4:'))");
  assert(await evaluate(`JSON.parse(sessionStorage.getItem(${JSON.stringify(visibilityKey)})).hiddenProjects.includes(${JSON.stringify(hiddenProject)}) && !!LocalBrainNavigation.getView('sessionChart')`),'Chart fixture has distinct saved visibility and entry camera');
  const writesBeforeFailure = visibilityWrites.length;
  const reloadChart = async () => {
    const id = await evaluate('__qa.id');await send('Page.reload');
    await wait(`__qa.id!==${JSON.stringify(id)} && document.readyState==='complete' && document.querySelectorAll('[data-chart-project-options] input').length===2`);await delay(180);
  };
  failChartPreference = true;
  await send('Fetch.enable',{patterns:[{urlPattern:'*/sessions?display=chart*',requestStage:'Response'}]});
  await reloadChart();
  assert(await evaluate(`!document.querySelector('[data-chart-project-save-error]').hidden && [...document.querySelectorAll('[data-chart-project-options] input')].filter(i=>!i.checked).map(i=>i.dataset.projectKey).includes(${JSON.stringify(hiddenProject)}) && JSON.parse(sessionStorage.getItem(${JSON.stringify(visibilityKey)})).hiddenProjects.includes(${JSON.stringify(hiddenProject)})`),'unavailable Chart preference preserves scope visibility beside entry camera');
  assert(visibilityWrites.length===writesBeforeFailure,'failed preference read never automatically writes visibility');
  failChartPreference = false;await send('Fetch.disable');await reloadChart();
  await click('[data-chart-project-filter] summary');await click('[data-chart-project-all]');await delay(300);
  const staleVisibility = await send('Page.addScriptToEvaluateOnNewDocument',{source:`
    const key=${JSON.stringify(visibilityKey)},value=JSON.parse(sessionStorage.getItem(key));
    value.hiddenProjects=[${JSON.stringify(hiddenProject)}];sessionStorage.setItem(key,JSON.stringify(value));
    __qa.incomingHiddenProjects=JSON.parse(sessionStorage.getItem(key)).hiddenProjects;
  `});
  await reloadChart();await send('Page.removeScriptToEvaluateOnNewDocument',{identifier:staleVisibility.identifier});
  assert(await evaluate(`__qa.incomingHiddenProjects.includes(${JSON.stringify(hiddenProject)})`),'incoming Chart actually reads a nonempty stale visibility fallback');
  assert(await evaluate("JSON.parse(document.querySelector('[data-chart-project-preference]').textContent).hidden_projects.length===0 && [...document.querySelectorAll('[data-chart-project-options] input')].every(i=>i.checked)"),'authoritative empty DB visibility overrides stale tab fallback');

  // Hold a real response, not the debugger: outgoing-page timers must remain observable.
  const delayedEntry='/help?navigation_delay=1';
  await navigate(delayedEntry);await click('.lnb a[href="/sessions"]');
  await wait("location.pathname==='/sessions' && document.readyState==='complete'");
  await writeFile(join(runtime,'hold-navigation'),'owned synthetic delay');
  await evaluate(`(()=>{
    __qa.traversalCalls=0;const back=history.back.bind(history);history.back=()=>{__qa.traversalCalls++;return back();};
    setTimeout(()=>document.querySelector('[data-inventory-view=projects]').click(),300);
    setTimeout(()=>{const back=document.querySelector('[data-app-back]'),forward=document.querySelector('[data-app-forward]');const sample={url:location.pathname+location.search,backDisabled:back.disabled,forwardDisabled:forward.disabled};back.click();sample.calls=__qa.traversalCalls;console.log('__navigation_sample__',JSON.stringify(sample));},1300);
  })()`);
  await click('[data-app-back]');await delay(2200);await rm(join(runtime,'hold-navigation'),{force:true});
  await wait(`location.pathname+location.search===${JSON.stringify(delayedEntry)} && document.readyState==='complete'`);
  assert(traversalSamples.length===1&&traversalSamples[0].url==='/projects'&&traversalSamples[0].backDisabled&&traversalSamples[0].forwardDisabled&&traversalSamples[0].calls===1,'slow traversal stays locked across partial updates and cannot cross its retained boundary');
  await click('[data-app-forward]');await wait("location.pathname==='/sessions'&&document.readyState==='complete'");
  await writeFile(join(runtime,'hold-navigation'),'owned synthetic delay');
  await click('[data-app-back]');await delay(120);await send('Page.stopLoading');await rm(join(runtime,'hold-navigation'),{force:true});await delay(150);
  if(await evaluate('!!window.navigation'))assert(await evaluate("!document.querySelector('[data-app-back]').disabled"),'host cancellation releases only the current traversal');
  await click('.lnb a[href="/context"]');await wait("location.pathname==='/context'&&document.readyState==='complete'");
  assert(await evaluate("!document.querySelector('[data-app-back]').disabled"),'ordinary navigation remains a cancellation recovery path');
  await navigate('/natural-search?mode=keyword&q=navigation');
  const searchUrl=await evaluate('location.pathname+location.search');
  const searchResult=await evaluate(`Array.from(document.querySelectorAll('.search-result h2 a')).find(a=>new URL(a.href).pathname.startsWith('/sessions/'))?.getAttribute('href')`);
  assert(!!searchResult,'keyword query has a real Session result');
  await click(`.search-result h2 a[href=${JSON.stringify(searchResult)}]`);
  await wait('location.pathname.startsWith("/sessions/") && document.readyState==="complete"');
  await back(searchUrl);
  assert(await evaluate('document.querySelector("#global-query").value')==='navigation','Back preserves global search query');
  await navigate('/help?lang=en');
  for(let i=0;i<55;i++) {
    const topic=i%2?'search':'settings';
    await click('.app-docs-topic[href="/help/'+topic+'?lang=en"]');
    await wait(`location.pathname==='/help/${topic}' && document.readyState==='complete' && document.querySelector('#guide-title').textContent===${JSON.stringify(topic==='settings'?'Settings':'Search')}`);
  }
  const capped=await evaluate(`JSON.parse(sessionStorage.getItem('localbrain:navigation:1'))`);
  assert(capped.entries.length===50&&capped.cursor===49,'latest50 points bound includes current');
  const beforeReload=await evaluate('history.state.localbrainNavigation.id');
  await send('Page.reload');await wait('document.readyState==="complete" && !!window.LocalBrainNavigation');await delay(150);
  assert(await evaluate('history.state.localbrainNavigation.id')===beforeReload,'reload preserves entry identity');
  for(let i=0;i<49;i++) {
    const target=new URL(capped.entries[48-i].href);
    await back(target.pathname+target.search+target.hash);
  }
  assert(await evaluate('document.querySelector("[data-app-back]").disabled'),'oldest retained point disables Back at49 steps');
  const deniedScript=await send('Page.addScriptToEvaluateOnNewDocument',{source:`
    const get=Storage.prototype.getItem,set=Storage.prototype.setItem;
    Storage.prototype.getItem=function(key){if(key==='localbrain:navigation:1')throw new DOMException('Synthetic storage denial','SecurityError');return get.call(this,key)};
    Storage.prototype.setItem=function(key,value){if(key==='localbrain:navigation:1')throw new DOMException('Synthetic storage denial','SecurityError');return set.call(this,key,value)};
  `});
  await navigate('/sessions');
  await click('[data-inventory-view="projects"]');await wait('location.pathname==="/projects"');
  assert(await evaluate('document.querySelector("[data-inventory-panel=projects]").hidden===false'),'storage denial preserves partial navigation');
  await send('Page.removeScriptToEvaluateOnNewDocument',{identifier:deniedScript.identifier});
  await send('Fetch.enable',{patterns:[{urlPattern:'*/static/navigation.js*'}]});failSetupScript=true;
  await navigate('/sessions');await click('[data-inventory-view="projects"]');await wait('location.pathname==="/projects"');
  assert(await evaluate('!window.LocalBrainNavigation && document.querySelector("[data-inventory-panel=projects]").hidden===false'),'controller failure preserves legacy History fallback');
  failSetupScript=false;await send('Fetch.disable');
  for(const width of [1440,920,700,320]) {
    await send('Emulation.setDeviceMetricsOverride',{width,height:900,deviceScaleFactor:1,mobile:false});
    await navigate('/sessions');
    assert(await evaluate('document.documentElement.scrollWidth===document.documentElement.clientWidth'),'contained toolbar '+width);
    assert(await evaluate(`(()=>{const b=document.querySelector('[data-app-back]').getBoundingClientRect(),s=document.querySelector('#global-query').getBoundingClientRect();return b.width>0&&s.width>0&&b.right<=s.left;})()`),'Back and search remain separate/reachable '+width);
    await capture('navigation-'+width);
  }
  assert(exceptions.length===0,'no runtime exception');assert(failedRequests.length===0,'no unexpected request failure');
  await writeFile(join(output,'result.json'),JSON.stringify({result:'PASS',checks,exceptions,failedRequests},null,2));
  console.log(JSON.stringify({result:'PASS',checks:checks.length,evidence:output}));
} catch(error) {
  await writeFile(join(output,'failure.json'),JSON.stringify({error:error.message,checks,exceptions,failedRequests},null,2));throw error;
} finally {
  socket?.close();for(const waiter of pending.values())clearTimeout(waiter.timer);
  await stop(chrome,'SIGTERM');await stop(backend,'SIGINT');
  await rm(profile,{recursive:true,force:true});await rm(runtime,{recursive:true,force:true});
  if(!process.argv[2])await rm(output,{recursive:true,force:true});
}
