// Verify web and macOS titlebar presentation against an owned synthetic backend only.
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
  [join(repository, 'tests/ui_state_fixture.py'), runtime, 'web', 'navigation'], {cwd:repository, stdio:['ignore','ignore','pipe']});
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
  assert(marker?.edition === 'web', 'owned synthetic backend');
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
    window.__qa={id:Math.random(),holdDocument:null,releases:[],visibleOriginMeasures:0};
    const originalRect=Element.prototype.getBoundingClientRect;
    Element.prototype.getBoundingClientRect=function(){
      if(this.id==='shell-tooltip'&&!this.hidden&&this.style.left==='0px'&&this.style.top==='0px'&&getComputedStyle(this).visibility!=='hidden')__qa.visibleOriginMeasures++;
      return originalRect.call(this);
    };
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
  const layout = async () => {
    await send('Page.bringToFront');
    await wait('!document.querySelector("[data-sidebar-toggle]").disabled');
    await evaluate('document.fonts.ready.then(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))))');
  };
  const key = async (value, code, modifiers, number) => {
    await send('Input.dispatchKeyEvent',{type:'keyDown',key:value,code,modifiers,windowsVirtualKeyCode:number,nativeVirtualKeyCode:number,...(value==='Enter'?{text:'\r'}:{})});
    await send('Input.dispatchKeyEvent',{type:'keyUp',key:value,code,modifiers:0,windowsVirtualKeyCode:number,nativeVirtualKeyCode:number});
  };
  const metrics = [];
  await send('Network.setUserAgentOverride',{userAgent:await evaluate('navigator.userAgent'),platform:'MacIntel'});
  await navigate('/sessions');await layout();
  assert(await evaluate('document.querySelector("[data-app-back]").disabled && document.querySelector("[data-app-forward]").disabled'),'initial directions disabled');
  assert(await evaluate('!document.documentElement.classList.contains("native-window-toolbar")'),'web edition alone does not imply native chrome');
  await writeFile(join(output,'icon-rendering.json'),JSON.stringify(await evaluate(`(async()=>{const e=document.querySelector('[data-icon="chat_bubble"]');const r=e.getBBox();const u=e.querySelector('use');const response=await fetch(u.getAttribute('href').split('#')[0]);return {svg:e.outerHTML,bounds:{x:r.x,y:r.y,width:r.width,height:r.height},fill:getComputedStyle(e).fill,status:response.status,mime:response.headers.get('Content-Type'),source:(await response.text()).slice(0,400)};})()`),null,2));
  assert(await evaluate(`(()=>{const r=document.querySelector('[data-icon="chat_bubble"]').getBBox();const v=document.querySelector('[data-icon="chat_bubble"]').viewBox.baseVal;return r.width>0&&r.height>0&&r.x>=v.x&&r.y>=v.y&&r.x+r.width<=v.x+v.width&&r.y+r.height<=v.y+v.height;})()`),'navigation glyph geometry fits its visible viewport');
  const webPosition=await evaluate('document.querySelector(".workspace-header").getBoundingClientRect().left');
  assert(webPosition>150,'web toolbar stays in workspace');
  assert(await evaluate('document.querySelector("[data-app-back]").dataset.shortcutKeys===JSON.stringify(["⌘","["]) && document.querySelector("[data-app-forward]").dataset.shortcutKeys===JSON.stringify(["⌘","]"])'),'Mac direction shortcut tooltips');
  const move = async (selector, fraction=.5) => {
    const point=await evaluate(`(()=>{const e=document.querySelector(${JSON.stringify(selector)}),r=e.getBoundingClientRect();return {x:r.left+r.width*${fraction},y:r.top+r.height/2};})()`);
    await send('Input.dispatchMouseEvent',{type:'mouseMoved',...point});
  };
  assert(await evaluate(`(()=>{const t=document.querySelector('[data-sidebar-toggle]'),b=document.querySelector('.brand');return !b.contains(t)&&t.parentElement===b.parentElement&&t.getBoundingClientRect().left>=b.getBoundingClientRect().right;})()`),'toggle beside brand outside home link');
  assert(await evaluate(`Array.from(document.querySelectorAll('.lnb-item')).every(e=>!!e.querySelector('svg use')&&!/^\d+$/.test(e.querySelector('.nav-symbol')?.textContent||'icon'))`),'Google navigation icons replace numeric marks');
  assert(await evaluate(`document.querySelector('.lnb a[href="/help"] [data-icon="menu_book"]')!==null`),'Docs uses book icon');
  await move('[data-sidebar-toggle]');await delay(300);
  await wait('!document.querySelector("#shell-tooltip").hidden');
  assert(await evaluate(`JSON.stringify(Array.from(document.querySelectorAll('#shell-tooltip kbd'),e=>e.textContent))===JSON.stringify(['⌘','⇧','S']) && !document.querySelector('#shell-tooltip').textContent.includes('(')`),'tooltip separates action and individual shortcut keys');
  const anchorTip=await evaluate(`(()=>{const r=document.querySelector('#shell-tooltip').getBoundingClientRect();return [r.x,r.y];})()`);
  await capture('expanded-sidebar-help');
  await move('[data-sidebar-toggle]',.15);await delay(80);await move('[data-sidebar-toggle]',.85);await delay(80);
  assert(await evaluate(`(()=>{const r=document.querySelector('#shell-tooltip').getBoundingClientRect();return Math.abs(r.x-${anchorTip[0]})<.1&&Math.abs(r.y-${anchorTip[1]})<.1;})()`),'pointer movement inside control does not move help');
  await key('Escape','Escape',0,27);await delay(20);
  assert(await evaluate('document.querySelector("#shell-tooltip").hidden'),'Escape dismisses help');
  await move('[data-sidebar-toggle]',.5);await delay(300);
  assert(await evaluate('document.querySelector("#shell-tooltip").hidden'),'dismissed help stays closed within same hover');
  await send('Input.dispatchMouseEvent',{type:'mouseMoved',x:600,y:300});
  await move('[data-sidebar-toggle]');await wait('!document.querySelector("#shell-tooltip").hidden');
  await move('#shell-tooltip');await delay(300);
  assert(await evaluate('!document.querySelector("#shell-tooltip").hidden'),'tooltip stays readable while hovered');
  await send('Input.dispatchMouseEvent',{type:'mouseMoved',x:600,y:300});await delay(160);
  assert(await evaluate('document.querySelector("#shell-tooltip").hidden'),'leaving control and help dismisses it');
  await evaluate('document.querySelector(".brand").focus()');await key('Tab','Tab',0,9);
  await wait('!document.querySelector("#shell-tooltip").hidden');
  assert(await evaluate(`document.activeElement===document.querySelector('[data-sidebar-toggle]')&&document.activeElement.getAttribute('aria-describedby').includes('shell-tooltip')`),'keyboard focus exposes anchored help without focus transfer');
  await key('Escape','Escape',0,27);
  for(const [selector,label,keycap] of [['[data-app-back]','뒤로','['],['[data-app-forward]','앞으로',']']]) {
    await move(selector);await wait('!document.querySelector("#shell-tooltip").hidden');
    assert(await evaluate(`(()=>{const a=document.querySelector(${JSON.stringify(selector)}),t=document.querySelector('#shell-tooltip');return a.disabled&&t.querySelector('.shell-tooltip-label').textContent===${JSON.stringify(label)}&&JSON.stringify(Array.from(t.querySelectorAll('kbd'),k=>k.textContent))===JSON.stringify(['⌘',${JSON.stringify(keycap)}])&&getComputedStyle(a.parentElement).cursor==='not-allowed';})()`),'disabled direction keeps short action and key help '+label);
    const beforeDisabled=await evaluate('location.href');
    await click(selector);await delay(80);
    assert(await evaluate('location.href')===beforeDisabled,'disabled direction remains non-actionable '+label);
  }
  for(const selector of ['#global-query','.search-link']) {
    await move(selector);await delay(300);
    assert(await evaluate('document.querySelector("#shell-tooltip").hidden'),'no redundant search hint '+selector);
  }
  assert(await evaluate(`getComputedStyle(document.querySelector('[data-app-back]')).cursor==='not-allowed'&&getComputedStyle(document.querySelector('[data-app-forward]')).cursor==='not-allowed'`),'disabled directions use not-allowed cursor');
  assert(await evaluate(`!document.querySelector('.lnb-footer').textContent.includes('Local index online')&&!document.querySelector('.lnb-footer').textContent.includes('Private on this Mac')`),'footer omits status/privacy slogans');
  await send('Emulation.setDeviceMetricsOverride',{width:1439,height:900,deviceScaleFactor:1,mobile:false});await delay(80);
  assert(await evaluate('document.querySelector("#shell-tooltip").hidden'),'resize dismisses help');
  await send('Emulation.setDeviceMetricsOverride',{width:1440,height:900,deviceScaleFactor:1,mobile:false});
  await move('[data-sidebar-toggle]');await wait('!document.querySelector("#shell-tooltip").hidden');
  const composing=await evaluate(`(()=>{const input=document.querySelector('#global-query');let received=false;input.addEventListener('keydown',()=>{received=true;},{once:true});const e=new KeyboardEvent('keydown',{key:'Escape',isComposing:true,bubbles:true,cancelable:true});input.dispatchEvent(e);return {prevented:e.defaultPrevented,received};})()`);
  assert(!composing.prevented&&composing.received,'composing Escape remains owned by input');
  await key('Escape','Escape',0,27);
  await click('[data-sidebar-toggle]');
  assert(await evaluate('Math.abs(document.querySelector(".lnb").getBoundingClientRect().width-64)<1 && document.querySelector("[data-sidebar-toggle]").getAttribute("aria-expanded")==="false" && Array.from(document.querySelectorAll(".lnb-item")).every(e=>e.getBoundingClientRect().width>0 && !!e.getAttribute("aria-label"))'),'collapse retains accessible compact menu rail');
  await navigate('/context');await layout();
  assert(await evaluate('document.documentElement.classList.contains("sidebar-collapsed")'),'sidebar state follows document navigation');
  await send('Page.reload');await wait('document.readyState==="complete"');await layout();
  assert(await evaluate('document.documentElement.classList.contains("sidebar-collapsed")'),'sidebar state follows reload');
  await evaluate(`document.documentElement.classList.remove('sidebar-collapsed');window.dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true}));`);
  assert(await evaluate('document.documentElement.classList.contains("sidebar-collapsed")'),'BFCache lifecycle reapplies current window sidebar state');
  await key('S','KeyS',12,83);
  assert(await evaluate('!document.documentElement.classList.contains("sidebar-collapsed")'),'Mac sidebar shortcut expands rail');
  await evaluate('document.querySelector(".lnb a").focus()');
  await key('S','KeyS',12,83);
  assert(await evaluate('document.activeElement===document.querySelector(".lnb a")'),'collapse preserves focus on retained home button');
  await click('[data-sidebar-toggle]');
  await key('k','KeyK',4,75);
  assert(await evaluate('document.activeElement===document.querySelector("#global-query")'),'Cmd K focuses search');
  await send('Input.insertText',{text:'navigation'});
  await key('Enter','Enter',0,13);
  await wait('location.pathname==="/natural-search" && document.readyState==="complete"');await layout();
  assert(await evaluate('new URL(location.href).searchParams.get("q")==="navigation" && new URL(location.href).searchParams.get("mode")==="keyword"'),'search keeps native GET query and mode');
  assert(await evaluate(`(()=>{const e=new KeyboardEvent('keydown',{key:'Enter',isComposing:true,bubbles:true,cancelable:true});document.querySelector('#global-query').dispatchEvent(e);return e.defaultPrevented;})()`),'composing Enter retains IME guard');
  await navigate('/sessions');await layout();
  const firstUrl=await evaluate('location.pathname+location.search');
  const sessionHref=await evaluate(`Array.from(document.querySelectorAll('a[href^="/sessions/"]')).find(a=>new URL(a.href).pathname==='/sessions/1').getAttribute('href')`);
  await click('a[href='+JSON.stringify(sessionHref)+']');await wait('location.pathname==="/sessions/1" && document.readyState==="complete"');await layout();
  await click('[data-sidebar-toggle]');
  await key('[','BracketLeft',4,219);
  await wait(`location.pathname+location.search===${JSON.stringify(firstUrl)} && document.readyState==='complete'`);await layout();
  assert(await evaluate('document.documentElement.classList.contains("sidebar-collapsed")'),'history restoration keeps latest window sidebar state');
  await click('[data-sidebar-toggle]');
  assert(await evaluate('!document.querySelector("[data-app-forward]").disabled'),'Back enables known Forward');
  await key(']','BracketRight',4,221);
  await wait('location.pathname==="/sessions/1" && document.readyState==="complete"');await layout();
  assert(await evaluate('document.querySelector("[data-app-forward]").disabled'),'Forward shortcut reaches newest entry');
  await move('[data-app-back]');await wait('!document.querySelector("#shell-tooltip").hidden');
  assert(await evaluate(`(()=>{const a=document.querySelector('[data-app-back]').getBoundingClientRect(),t=document.querySelector('#shell-tooltip').getBoundingClientRect();return t.y>=a.bottom&&t.x>=8&&t.right<=document.documentElement.clientWidth-8&&document.querySelector('#shell-tooltip .shell-tooltip-label').textContent==='뒤로'&&__qa.visibleOriginMeasures===0;})()`),'enabled Back is positioned before becoming visible');
  await capture('enabled-back-help');
  await back(firstUrl);await layout();
  await move('[data-app-forward]');await wait('!document.querySelector("#shell-tooltip").hidden');
  assert(await evaluate(`document.querySelector('#shell-tooltip .shell-tooltip-label').textContent==='앞으로'&&__qa.visibleOriginMeasures===0`),'enabled Forward retains name/key help');
  await capture('enabled-forward-help');
  await click('[data-app-forward]');await wait('location.pathname==="/sessions/1" && document.readyState==="complete"');await layout();
  assert(await evaluate('document.querySelector("[data-app-back]").dataset.shortcutKeys===JSON.stringify(["⌘","["]) && !document.querySelector("[data-app-back]").hasAttribute("title")'),'repeated updates do not duplicate shortcut hints');
  await back(firstUrl);await layout();
  await click('.lnb a[href="/help"]');await wait('location.pathname==="/help" && document.readyState==="complete"');await layout();
  assert(await evaluate('document.querySelector("[data-app-forward]").disabled'),'new branch disables Forward');
  await key(']','BracketRight',4,221);await delay(150);
  assert(await evaluate('location.pathname')==='/help','disabled Forward shortcut cannot escape app');
  await click('.settings-gear');await wait('document.querySelector("#settings-dialog").open');
  assert(await evaluate('document.querySelector("#shell-tooltip").hidden'),'modal opening dismisses shell hint');
  const modalUrl=await evaluate('location.href');const sidebarState=await evaluate('document.documentElement.classList.contains("sidebar-collapsed")');
  await key('[','BracketLeft',4,219);await key('k','KeyK',4,75);await key('S','KeyS',12,83);
  assert(await evaluate('location.href')===modalUrl&&await evaluate('document.documentElement.classList.contains("sidebar-collapsed")')===sidebarState,'modal owns shell navigation and sidebar shortcuts');
  assert(await evaluate('document.querySelector("#settings-dialog").contains(document.activeElement)'),'modal keeps keyboard focus');
  await key('Escape','Escape',0,27);await wait('!document.querySelector("#settings-dialog").open');
  for(const width of [1440,920,700,320]) {
    await send('Emulation.setDeviceMetricsOverride',{width,height:900,deviceScaleFactor:1,mobile:false});await delay(80);
    assert(await evaluate('document.documentElement.scrollWidth===document.documentElement.clientWidth'),'web containment '+width);
    await capture('web-toolbar-'+width);
    await click('[data-sidebar-toggle]');await layout();
    assert(await evaluate('document.documentElement.scrollWidth===document.documentElement.clientWidth && document.querySelector(".lnb").getBoundingClientRect().width===64'),'compact rail containment '+width);
    await move('.lnb a[href="/sessions"]');await wait('!document.querySelector("#shell-tooltip").hidden');
    assert(await evaluate(`(()=>{const r=document.querySelector('#shell-tooltip').getBoundingClientRect();return r.left>=0&&r.right<=innerWidth&&r.top>=0&&r.bottom<=innerHeight;})()`),'compact menu hint stays inside viewport '+width);
    await capture('compact-rail-'+width);
    await click('[data-sidebar-toggle]');await layout();
  }
  await send('Emulation.setDeviceMetricsOverride',{width:1440,height:900,deviceScaleFactor:1,mobile:false});
  await send('Emulation.setDeviceMetricsOverride',{width:900,height:900,deviceScaleFactor:1,mobile:false});
  await navigate('/atlassian');await layout();
  await click('[data-atlassian-item-link]');await wait('!!document.querySelector("[data-atlassian-preview][aria-modal=true]")');await layout();
  const sheetUrl=await evaluate('location.href'), sheetSidebar=await evaluate('document.documentElement.classList.contains("sidebar-collapsed")');
  await key('S','KeyS',12,83);await key('[','BracketLeft',4,219);await key(']','BracketRight',4,221);await key('k','KeyK',4,75);await delay(120);
  assert(await evaluate('location.href')===sheetUrl&&await evaluate('document.documentElement.classList.contains("sidebar-collapsed")')===sheetSidebar,'custom modal sheet owns all shell shortcuts');
  assert(await evaluate('document.querySelector("[data-atlassian-preview][aria-modal=true]").contains(document.activeElement)'),'custom sheet retains focus');
  await key('Escape','Escape',0,27);await wait('!document.querySelector("[data-atlassian-preview][aria-modal=true]")');await layout();
  assert(await evaluate('!document.querySelector("#global-query") && !!document.querySelector("a.search-link")'),'optional web explorer retains local search scope');
  await key('k','KeyK',4,75);await wait('location.pathname==="/natural-search" && document.readyState==="complete"');
  assert(true,'search shortcut uses explorer Search destination');

  const bootstrap=await readFile(join(repository,'desktop/ui/window-shell.js'),'utf8');
  const dragPath=process.env.LOCALBRAIN_QA_TAURI_DRAG_SCRIPT;
  const drag=dragPath?(await readFile(dragPath,'utf8')).replaceAll('__TEMPLATE_os_name__',"'macos'"):'';
  const native=await send('Page.addScriptToEvaluateOnNewDocument',{source:bootstrap+`\nwindow.__qa.nativeCalls=[];window.__TAURI_INTERNALS__={invoke:command=>{__qa.nativeCalls.push(command);return Promise.resolve();}};\n`+drag});
  await evaluate('sessionStorage.removeItem("localbrain:sidebar:1")');
  await navigate('/sessions?source=1');await layout();
  assert(await evaluate('document.documentElement.classList.contains("native-window-toolbar")'),'host bootstrap selects native titlebar layout');
  for(const width of [1440,920,700,640]) {
    await send('Emulation.setDeviceMetricsOverride',{width,height:900,deviceScaleFactor:1,mobile:false});await delay(80);
    const m=await evaluate(`(()=>{const h=document.querySelector('.workspace-header').getBoundingClientRect(),b=document.querySelector('[data-app-back]').getBoundingClientRect(),i=document.querySelector('#global-query').getBoundingClientRect();return {width:innerWidth,left:h.left,top:h.top,height:h.height,reserved:b.left,input:i.left,inputRight:i.right,overflow:document.documentElement.scrollWidth>document.documentElement.clientWidth};})()`);metrics.push(m);
    assert(m.left===0&&m.top===0&&m.height===58&&m.reserved>=90&&!m.overflow,'native titlebar containment and OS-control inset '+width);
    await capture('native-toolbar-'+width);
  }
  await send('Emulation.setDeviceMetricsOverride',{width:1440,height:900,deviceScaleFactor:1,mobile:false});
  await click('[data-sidebar-toggle]');await delay(80);
  const mainTop=await evaluate('document.querySelector("main.app-main").getBoundingClientRect().top');
  assert(Math.abs(mainTop-58)<1,'native body has no duplicate content-header row');
  await capture('native-collapsed');
  await navigate('/help/settings?lang=en');await layout();
  assert(await evaluate('document.documentElement.classList.contains("sidebar-collapsed") && document.querySelector(".app-docs").lang==="en"'),'native sidebar state and Docs locale survive navigation');
  await click('[data-sidebar-toggle]');
  if(drag) {
    await evaluate('__qa.nativeCalls=[]');
    await click('[data-app-forward]');
    assert((await evaluate('__qa.nativeCalls.length'))===0,'disabled direction wrapper blocks native drag');
    await click('[data-sidebar-toggle]');await click('[data-sidebar-toggle]');
    await click('#global-query');
    assert((await evaluate('__qa.nativeCalls.length'))===0,'native buttons and input are excluded from drag');
    const point=await evaluate(`(()=>{const b=document.querySelector('[data-app-forward]').getBoundingClientRect(),q=document.querySelector('#global-query').getBoundingClientRect(),h=document.querySelector('.workspace-header').getBoundingClientRect();return {x:(b.right+q.left)/2,y:h.top+h.height/2};})()`);
    for(const count of [1,2]) {
      await send('Input.dispatchMouseEvent',{type:'mousePressed',button:'left',clickCount:count,...point});
      await send('Input.dispatchMouseEvent',{type:'mouseReleased',button:'left',clickCount:count,...point});
    }
    const calls=await evaluate('__qa.nativeCalls');
    assert(calls.includes('plugin:window|start_dragging')&&calls.includes('plugin:window|internal_toggle_maximize'),'installed Tauri dispatches drag and double-click commands');
  }
  const denied=await send('Page.addScriptToEvaluateOnNewDocument',{source:`const get=Storage.prototype.getItem,set=Storage.prototype.setItem;Storage.prototype.getItem=function(k){if(k==='localbrain:sidebar:1')throw new DOMException('Denied','SecurityError');return get.call(this,k)};Storage.prototype.setItem=function(k,v){if(k==='localbrain:sidebar:1')throw new DOMException('Denied','SecurityError');return set.call(this,k,v)};`});
  await navigate('/sessions?denied=1');await layout();
  await click('[data-sidebar-toggle]');
  assert(await evaluate('document.documentElement.classList.contains("sidebar-collapsed")'),'storage denial retains sidebar controls');
  await send('Page.removeScriptToEvaluateOnNewDocument',{identifier:denied.identifier});
  failSetupScript=true;await send('Fetch.enable',{patterns:[{urlPattern:'*/static/shell.js*',requestStage:'Request'}]});
  await navigate('/sessions?shell-failed=1');
  assert(await evaluate('document.querySelector("[data-sidebar-toggle]").disabled && getComputedStyle(document.querySelector(".lnb")).display!=="none"'),'shell failure leaves navigation rail accessible');
  const fallbackHref=await evaluate(`Array.from(document.querySelectorAll('a[href^="/sessions/"]')).find(a=>new URL(a.href).pathname==='/sessions/1').getAttribute('href')`);
  await click('a[href='+JSON.stringify(fallbackHref)+']');await wait('location.pathname==="/sessions/1" && document.readyState==="complete"');
  await click('[data-app-back]');await wait('location.search==="?shell-failed=1" && document.readyState==="complete"');
  assert(true,'shell failure retains independent history controls');
  failSetupScript=false;await send('Fetch.disable');await send('Page.removeScriptToEvaluateOnNewDocument',{identifier:native.identifier});
  await send('Network.setUserAgentOverride',{userAgent:await evaluate('navigator.userAgent'),platform:'Win32'});
  await navigate('/sessions?platform=windows');await layout();
  assert(await evaluate('document.querySelector("[data-app-back]").dataset.shortcutKeys===JSON.stringify(["Alt","←"]) && document.querySelector("#global-query").getAttribute("aria-keyshortcuts")==="Control+K"'),'other-browser shortcut mapping');
  await key('k','KeyK',2,75);
  assert(await evaluate('document.activeElement===document.querySelector("#global-query")'),'Ctrl K focuses search on other desktop browsers');
  await key('S','KeyS',10,83);
  assert(await evaluate('document.documentElement.classList.contains("sidebar-collapsed")'),'Ctrl Shift S toggles other-browser sidebar');
  await click('[data-sidebar-toggle]');
  const altRoot=await evaluate('location.pathname+location.search');
  await click('.lnb a[href="/context"]');await wait('location.pathname==="/context" && document.readyState==="complete"');await layout();
  const separatorWidth=await evaluate('document.querySelector(".source-tree-pane").getBoundingClientRect().width');
  await evaluate('document.querySelector("[data-context-pane-separator]").focus()');
  await key('ArrowLeft','ArrowLeft',1,37);
  await wait(`location.pathname+location.search===${JSON.stringify(altRoot)} && document.readyState==='complete'`);await layout();
  assert(true,'Alt Back has priority over focused splitter arrows');
  await key('ArrowRight','ArrowRight',1,39);await wait('location.pathname==="/context" && document.readyState==="complete"');await layout();
  assert(Math.abs(await evaluate('document.querySelector(".source-tree-pane").getBoundingClientRect().width')-separatorWidth)<1,'Alt navigation does not resize splitter');
  await evaluate('document.querySelector("[data-context-pane-separator]").focus()');
  await key('ArrowLeft','ArrowLeft',0,37);
  assert(Math.abs(await evaluate('document.querySelector(".source-tree-pane").getBoundingClientRect().width')-(separatorWidth-16))<1,'plain arrow remains a view-local resize action');
  const shortNative=await send('Page.addScriptToEvaluateOnNewDocument',{source:bootstrap});
  await send('Network.setUserAgentOverride',{userAgent:await evaluate('navigator.userAgent'),platform:'MacIntel'});
  await send('Emulation.setDeviceMetricsOverride',{width:640,height:480,deviceScaleFactor:1,mobile:false});
  await navigate('/sessions?short-window=1');await layout();
  if(!await evaluate('document.documentElement.classList.contains("sidebar-collapsed")'))await click('[data-sidebar-toggle]');
  await layout();
  assert(await evaluate(`(()=>{const r=document.querySelector('.lnb').getBoundingClientRect(),f=document.querySelector('.lnb-footer').getBoundingClientRect();return r.width===64&&r.y===58&&f.bottom<=innerHeight;})()`),'short native window retains rail and footer');
  await evaluate('document.querySelector(".brand").focus()');
  const focusSequence=[];
  for(let i=0;i<13;i++){
    await key('Tab','Tab',0,9);await delay(160);
    const selected=await evaluate(`(()=>{const a=document.activeElement;return {rail:!!a.closest('.lnb'),label:a.getAttribute('aria-label'),tip:!document.querySelector('#shell-tooltip').hidden,scroll:document.querySelector('.lnb-nav').scrollTop};})()`);
    focusSequence.push(selected);
    if(selected.rail)assert(selected.tip,'short window focused help '+selected.label);
  }
  await writeFile(join(output,'short-focus.json'),JSON.stringify(focusSequence,null,2));
  await evaluate(`document.querySelector('.lnb a[href="/sources"]').focus()`);
  await wait('!document.querySelector("#shell-tooltip").hidden');
  await send('Input.dispatchMouseEvent',{type:'mouseWheel',x:32,y:260,deltaY:40,deltaX:0});await delay(160);
  assert(await evaluate('document.querySelector("#shell-tooltip").hidden'),'explicit wheel movement dismisses focused hint');
  await capture('short-native-compact');
  await send('Page.removeScriptToEvaluateOnNewDocument',{identifier:shortNative.identifier});
  await writeFile(join(output,'toolbar-metrics.json'),JSON.stringify({metrics,dragSource:dragPath||null,hostEvidence:'browser host simulation; native movement requires host verification'},null,2));
  assert(exceptions.length===0,'no runtime exception');assert(failedRequests.length===0,'no unexpected request failure');
  await writeFile(join(output,'result.json'),JSON.stringify({result:'PASS',checks,exceptions,failedRequests},null,2));
  console.log(JSON.stringify({result:'PASS',checks:checks.length,evidence:output}));
} catch(error) {
  let diagnostic;
  try {diagnostic=await Promise.race([send('Runtime.evaluate',{expression:'({url:location.href,ready:document.readyState,visibility:document.visibilityState,fonts:document.fonts.status})',returnByValue:true}),delay(1200).then(()=>({timeout:true}))]);}catch(e){diagnostic={error:e.message};}
  await writeFile(join(output,'failure.json'),JSON.stringify({error:error.message,checks,exceptions,failedRequests,diagnostic},null,2));throw error;
} finally {
  socket?.close();for(const waiter of pending.values())clearTimeout(waiter.timer);
  await stop(chrome,'SIGTERM');await stop(backend,'SIGINT');
  await rm(profile,{recursive:true,force:true});await rm(runtime,{recursive:true,force:true});
  if(!process.argv[2])await rm(output,{recursive:true,force:true});
}
