// Real xterm/PTY checks in a synthetic HOME and owned backend. Never use a live-user server.
// LOCALBRAIN_TERMINAL_TEST_BUNDLE=/path/to/built/public/runtime node scripts/qa-terminal-workspace-browser.mjs [outside-repo evidence parent]
import {spawn} from 'node:child_process';
import {mkdir, mkdtemp, readFile, writeFile, rm, access} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {dirname, join, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

const repository = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const destination = resolve(process.argv[2] || tmpdir());
if (destination === repository || destination.startsWith(repository + '/')) throw new Error('Evidence must stay outside the repository');
if (!process.env.LOCALBRAIN_TERMINAL_TEST_BUNDLE) throw new Error('An explicitly built public-package runtime payload is required');
await mkdir(destination, {recursive:true});
const output = await mkdtemp(join(destination, 'lb-terminal-ui-'));
// macOS Unix socket paths are limited to 104 bytes, independently of evidence location.
const runtimeOwner = await mkdtemp('/private/tmp/lbtu-');
const runtime = join(runtimeOwner, 'rt'), profile = join(output, 'chrome');
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const checks = [], exceptions = [], failures = [], pending = new Map(), held = new Set();
const assert = (value, name) => { if (!value) throw new Error(name); checks.push(name); };
let base, chrome, socket, send, evaluate, holdFonts = true, failFonts = false, failList = false, loseCreateResponse = true;
let holdListResponse = false, heldListResponse = null, acceptNextDialog = false;
let incompatibleService = false;
let failRename = false, failOrder = false, failWorkspaceMove = false;
let busyRetireTarget = null, injectedRetireBusy = 0;
let holdNextTabStop = false, heldTabStop = null, failReadAfterOrder = false;
const creationRequests = [];
const dialogs = [];
const backend = spawn(process.env.LOCALBRAIN_QA_PYTHON || join(repository, '.venv/bin/python'),
  [join(repository, 'tests/ui_state_fixture.py'), runtime, 'web', 'terminal'], {cwd:repository, stdio:['ignore','ignore','pipe']});
let backendError = '';
backend.stderr.on('data', chunk => {backendError = (backendError + chunk.toString()).slice(-4000);});
backend.on('error', error => {backendError = error.message;});
async function stop(child, signal) {
  if (!child?.pid || child.exitCode !== null || child.signalCode !== null) return;
  const ended = new Promise(resolve => child.once('exit', resolve));
  child.kill(signal); await Promise.race([ended, delay(15000)]);
  if (child.exitCode === null && child.signalCode === null) {child.kill('SIGKILL'); await ended; throw new Error('Owned fixture did not stop gracefully');}
}
try {
  let port;
  for (let i=0; i<200 && !port; i++) {
    try {port = JSON.parse(await readFile(join(runtime,'port.json'),'utf8')).port;} catch {}
    if (backend.exitCode !== null || backend.signalCode !== null) throw new Error('Fixture startup: '+backendError);
    if (!port) await delay(50);
  }
  if (!port) throw new Error('Fixture did not start: '+backendError);
  base = 'http://127.0.0.1:'+port;
  let marker;
  for (let i=0;i<100&&!marker;i++) {
    try {marker = await (await fetch(base+'/__qa__/fixture')).json();} catch {await delay(50);}
  }
  assert(marker?.fixture === 'synthetic-ui-states-v1', 'owned synthetic fixture');
  chrome = spawn(process.env.LOCALBRAIN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', [
    '--headless=new','--disable-gpu','--disable-background-networking','--disable-component-update',
    '--no-first-run','--no-default-browser-check','--remote-debugging-port=0',`--user-data-dir=${profile}`,
    '--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1, EXCLUDE localhost','about:blank'
  ], {stdio:'ignore'});
  let debugPort, browserError;
  chrome.on('error', error => {browserError = error.message;});
  for (let i=0;i<150&&!debugPort;i++) {
    if (browserError) throw new Error(browserError);
    try {debugPort = Number((await readFile(join(profile,'DevToolsActivePort'),'utf8')).split('\n')[0]);} catch {await delay(50);}
  }
  if (!debugPort) throw new Error('Chrome did not start');
  const target = await (await fetch(`http://127.0.0.1:${debugPort}/json/new?about:blank`,{method:'PUT'})).json();
  socket = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve,reject) => {socket.addEventListener('open',resolve,{once:true});socket.addEventListener('error',reject,{once:true});});
  let sequence = 0;
  send = (method, params={}) => new Promise((resolve,reject) => {
    const id = ++sequence, timer = setTimeout(() => {pending.delete(id);reject(new Error('CDP timeout: '+method));},20000);
    pending.set(id,{resolve,reject,timer});socket.send(JSON.stringify({id,method,params}));
  });
  socket.addEventListener('message', event => {
    const value = JSON.parse(event.data);
    if (value.id) {
      const waiter = pending.get(value.id);if (!waiter) return;
      pending.delete(value.id);clearTimeout(waiter.timer);
      value.error ? waiter.reject(new Error(JSON.stringify(value.error))) : waiter.resolve(value.result);
    } else if (value.method === 'Runtime.exceptionThrown') exceptions.push(value.params.exceptionDetails);
    else if (value.method === 'Page.javascriptDialogOpening') {
      dialogs.push(value.params.message);
      const accept = acceptNextDialog; acceptNextDialog = false;
      if (!accept) failures.push('Unexpected dialog');
      void send('Page.handleJavaScriptDialog',{accept}).catch(error=>failures.push(error.message));
    }
    else if (value.method === 'Fetch.requestPaused') {
      const {requestId,request,responseStatusCode} = value.params, url = new URL(request.url);
      let action;
      if (holdNextTabStop && url.pathname.startsWith('/api/terminal/tabs/') && url.pathname.endsWith('/stop')) {
        holdNextTabStop=false;heldTabStop=requestId;return;
      } else if (busyRetireTarget && url.pathname === '/api/terminal/terminals/'+busyRetireTarget+'/stop') {
        busyRetireTarget=null;injectedRetireBusy++;
        action=send('Fetch.fulfillRequest',{requestId,responseCode:409,responseHeaders:[{name:'Content-Type',value:'application/json'}],body:Buffer.from('{"error":{"code":"busy","message":"Synthetic control contention"}}').toString('base64')});
      } else if ((url.pathname.endsWith('/rename') && failRename) || (url.pathname === '/api/terminal/view-order' && failOrder) || (url.pathname === '/api/terminal/workspaces/move' && failWorkspaceMove)) {
        if(url.pathname==='/api/terminal/view-order'&&failReadAfterOrder){failList=true;failReadAfterOrder=false;}
        action=send('Fetch.fulfillRequest',{requestId,responseCode:503,responseHeaders:[{name:'Content-Type',value:'application/json'}],body:Buffer.from('{"detail":"Synthetic view preference failure"}').toString('base64')});
      } else if (url.pathname === '/api/terminal/terminals' && responseStatusCode) {
        creationRequests.push(JSON.parse(request.postData));
        if (loseCreateResponse) {
          const response = loseCreateResponse; loseCreateResponse = false;
          action = response === '503'
            ? send('Fetch.fulfillRequest',{requestId,responseCode:503,responseHeaders:[{name:'Content-Type',value:'application/json'}],body:Buffer.from('{"detail":"Synthetic uncertain control response"}').toString('base64')})
            : send('Fetch.failRequest',{requestId,errorReason:'Failed'});
        }
        else action = send('Fetch.continueRequest',{requestId});
      } else if (url.pathname === '/api/terminal' && responseStatusCode && holdListResponse) {
        holdListResponse = false; heldListResponse = requestId; return;
      } else if (url.pathname === '/api/terminal' && responseStatusCode === 200 && incompatibleService) {
        action = send('Fetch.getResponseBody',{requestId}).then(body => {
          const data=JSON.parse(body.base64Encoded?Buffer.from(body.body,'base64').toString():body.body);
          data.service.state='incompatible';
          return send('Fetch.fulfillRequest',{requestId,responseCode:200,responseHeaders:[{name:'Content-Type',value:'application/json'}],body:Buffer.from(JSON.stringify(data)).toString('base64')});
        });
      } else if (url.pathname.endsWith('.woff2') && failFonts) action = send('Fetch.failRequest',{requestId,errorReason:'Failed'});
      else if (url.pathname.endsWith('.woff2') && holdFonts) {held.add(requestId);return;}
      else if (url.pathname === '/api/terminal' && failList && !responseStatusCode) action = send('Fetch.fulfillRequest',{requestId,responseCode:503,responseHeaders:[{name:'Content-Type',value:'application/json'}],body:Buffer.from('{"detail":"Synthetic connection failure"}').toString('base64')});
      else action = send('Fetch.continueRequest',{requestId});
      void action.catch(error => failures.push(error.message));
    }
  });
  evaluate = async expression => {
    const result = await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});
    if (result.exceptionDetails) throw new Error(result.exceptionDetails.exception?.description || result.exceptionDetails.text);
    return result.result.value;
  };
  const wait = async (expression, seconds=30) => {
    const deadline=Date.now()+seconds*1000;
    while(Date.now()<deadline){if(await evaluate(expression))return;await delay(30);}
    throw new Error('State timeout: '+expression);
  };
  const click = async selector => {
    const point = await evaluate(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(!e||e.disabled)throw new Error('Control unavailable: '+${JSON.stringify(selector)});if(e.closest('.terminal-menu-items'))e.scrollIntoView({block:'nearest',inline:'nearest'});const r=e.getBoundingClientRect(),point={x:r.x+r.width/2,y:r.y+r.height/2};if(!e.contains(document.elementFromPoint(point.x,point.y)))throw new Error('Control covered: '+${JSON.stringify(selector)});return point;})()`);
    await send('Input.dispatchMouseEvent',{type:'mouseMoved',...point});
    await send('Input.dispatchMouseEvent',{type:'mousePressed',button:'left',clickCount:1,...point});
    await send('Input.dispatchMouseEvent',{type:'mouseReleased',button:'left',clickCount:1,...point});
  };
  const key = async (name, code=name, modifiers=0, windowsVirtualKeyCode=0) => {
    await send('Input.dispatchKeyEvent',{type:'keyDown',key:name,code,modifiers,windowsVirtualKeyCode,...(name==='Enter'?{text:'\r',unmodifiedText:'\r'}:{})});
    await send('Input.dispatchKeyEvent',{type:'keyUp',key:name,code,modifiers,windowsVirtualKeyCode});
  };
  const command = async text => {
    await wait(`document.querySelector('[data-terminal-connection]').textContent==='입력 가능'&&document.activeElement.classList.contains('xterm-helper-textarea')`);
    // Screen-reader mode intentionally ignores insertText input events; use normal keypresses.
    for (const character of text) {
      await send('Input.dispatchKeyEvent',{type:'keyDown',key:character,text:character,unmodifiedText:character});
      await send('Input.dispatchKeyEvent',{type:'keyUp',key:character});
    }
    await key('Enter','Enter',0,13);
  };
  const state = () => evaluate(`fetch('/api/terminal').then(r=>r.json())`);
  const capture = async name => {
    const result = await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
    await writeFile(join(output,name+'.png'),Buffer.from(result.data,'base64'));
  };
  const navigate = async path => {
    const previous = await evaluate('window.__terminalQaId');
    await send('Page.navigate',{url:base+path});
    await wait(`typeof window.__terminalQaId==='number' && window.__terminalQaId!==${JSON.stringify(previous)} && document.readyState!=='loading' && !!document.querySelector('.app-main')`);
  };
  const ensureRail = async () => {
    if(await evaluate(`document.querySelector('[data-terminal-rail-toggle]').getAttribute('aria-expanded')==='false'`)) await click('[data-terminal-rail-toggle]');
  };
  await send('Page.enable');await send('Runtime.enable');await send('Network.enable');
  await send('Network.setCacheDisabled',{cacheDisabled:true});
  await send('Fetch.enable',{patterns:[{urlPattern:'*woff2*'},{urlPattern:base+'/api/terminal'},{urlPattern:base+'/api/terminal',requestStage:'Response'},{urlPattern:base+'/api/terminal/terminals',requestStage:'Response'},{urlPattern:base+'/api/terminal/tabs/*/rename'},{urlPattern:base+'/api/terminal/view-order'},{urlPattern:base+'/api/terminal/workspaces/move'},{urlPattern:base+'/api/terminal/terminals/*/stop'},{urlPattern:base+'/api/terminal/tabs/*/stop'}]});
  await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
  await send('Emulation.setFocusEmulationEnabled',{enabled:true});
  await send('Page.addScriptToEvaluateOnNewDocument',{source:'window.__terminalQaId=Math.random();'});
  await navigate('/terminal');
  for(let i=0;i<100&&held.size<2;i++)await delay(30);
  assert(held.size===2 && await evaluate(`document.querySelector('[data-terminal-new]').disabled && !document.querySelector('.terminal-pane')`),'both fonts gate new panes while pending');
  holdFonts=false;
  for(const requestId of held)await send('Fetch.continueRequest',{requestId});held.clear();
  await wait(`!document.querySelector('[data-terminal-new]').disabled`);
  const initial=await state();
  assert(initial.service.state==='stopped' && initial.terminals.length===0,'inspection does not start manager');
  assert(await evaluate(`(()=>{const q=s=>document.querySelector(s).getBoundingClientRect();return q('.terminal-main').left===q('.lnb').right&&q('.terminal-rail').left===q('.terminal-main').left&&q('.terminal-stage').left===q('.terminal-rail').right&&q('.terminal-statusbar').bottom===innerHeight&&document.documentElement.scrollHeight===innerHeight;})()`),'rail directly adjoins global sidebar; frame fills remaining viewport');
  assert(await evaluate(`document.querySelector('[data-terminal-rail-toggle]').hidden&&!document.querySelector('[data-terminal-rail-close]').hidden`),'expanded Terminal rail has one visible collapse control');
  assert(await evaluate(`document.querySelector('.workspace-header').getBoundingClientRect().height===48`),'Terminal search/header uses compact 48px density');
  await capture('empty-wide');
  await click('[data-settings-open="terminal"]');
  await wait(`document.querySelector('#settings-dialog').open&&!document.querySelector('[data-terminal-settings-form] input').disabled`);
  assert(await evaluate(`!document.querySelector('[data-settings-panel="terminal"]').hidden&&document.querySelector('[data-terminal-settings-form] small').textContent.includes('기존 그룹의 폴더는 유지')`),'rail settings opens correct pane and explains group default scope');
  await capture('settings-terminal');await click('[data-settings-close]');
  await wait(`!document.querySelector('#settings-dialog').open`);
  await click('[data-terminal-new]');
  await wait(`!document.querySelector('[data-terminal-create-retry]').hidden&&!document.querySelector('[data-terminal-create-retry]').disabled`,90);
  const uncertain=await state();
  assert(uncertain.terminals.length===1 && await evaluate(`document.querySelector('[data-terminal-new]').disabled`),'lost creation response retains one shell and explicit retry');
  await click('[data-terminal-create-retry]');
  await wait(`document.querySelectorAll('.terminal-pane').length===1 && document.activeElement.classList.contains('xterm-helper-textarea')`);
  let current=await state();const first=current.terminals[0],firstTab=current.tabs[0],firstSpace=current.workspaces.items.find(item=>item.tabs.includes(firstTab.id));
  assert(current.terminals.length===1&&first.id===uncertain.terminals[0].id&&first.pid===uncertain.terminals[0].pid&&creationRequests[0].key===creationRequests[1].key,'first-folder discovery does not change retry identity or duplicate PTY');
  assert(first.activity.state==='unknown','plain shell has unknown command state');
  const currentShape=await evaluate(`(()=>{const e=document.querySelector('.terminal-pane .terminal-view-current'),b=e.getBoundingClientRect(),p=e.getBBox();return {width:b.width,height:b.height,inkWidth:p.width,inkHeight:p.height,icon:e.querySelector('use')?.getAttribute('href').split('#')[1]};})()`);
  assert(currentShape.icon==='check'&&currentShape.width===20&&currentShape.height===20&&currentShape.inkWidth>0&&await evaluate(`document.querySelector('[data-terminal-command]').textContent.includes('미확인')&&!document.querySelector('.terminal-pane .terminal-program-indicator:not([hidden])')`),'an uninstrumented shell has the same current-view check, a separate unknown command description and no fabricated program indicator');
  await command("printf 'QA_%s\\n' INPUT");
  await wait(`document.querySelector('.xterm-rows').textContent.includes('QA_INPUT')`);
  assert(await evaluate(`getComputedStyle(document.querySelector('.terminal-pane-body')).fontSize==='13px'`),'D2Coding 13px pane font');
  await send('Emulation.setFocusEmulationEnabled',{enabled:false});
  const inactiveTarget=await send('Target.createTarget',{url:'about:blank',background:false});
  await send('Target.activateTarget',{targetId:inactiveTarget.targetId});
  await wait(`document.querySelector('[data-terminal-page]').classList.contains('window-inactive')`);
  assert(await evaluate(`document.querySelector('[role=tab][aria-selected="true"]')?.dataset.terminalFocus==='tab:${firstTab.id}'&&document.querySelector('.terminal-view-current use').getAttribute('href').endsWith('#check')&&document.querySelector('[data-terminal-command]').textContent.includes('미확인')`),'inactive view retains selected tab/current check and unknown shell description');
  await capture('status-window-inactive');
  await send('Target.activateTarget',{targetId:target.id});
  await send('Emulation.setFocusEmulationEnabled',{enabled:true});
  await wait(`!document.querySelector('[data-terminal-page]').classList.contains('window-inactive')&&document.querySelector('[data-terminal-connection]').textContent==='입력 가능'`);
  await send('Target.closeTarget',{targetId:inactiveTarget.targetId});
  assert((await state()).terminals[0].id===first.id&&(await state()).terminals[0].pid===first.pid,'focus/visibility round trip restores emphasis and input on the same process');
  await capture('status-window-active');
  const cwdB=join(runtime,'demo-b');
  await command(`cd ${JSON.stringify(cwdB)}; printf '\\033]7;file://localhost%s\\007' "$PWD"`);
  await wait(`fetch('/api/terminal').then(r=>r.json()).then(s=>s.terminals[0].cwd===${JSON.stringify(cwdB)})`);
  assert((await state()).tabs[0].cwd===firstTab.cwd,'folder group remains at creation cwd after cd');
  assert(await evaluate(`!document.querySelector('.terminal-toolbar [data-terminal-split]')&&document.querySelectorAll('.terminal-pane-header [data-terminal-split]').length===2`),'tab toolbar creates groups and split controls belong to each individual pane');
  await click(`[data-terminal-pane="${first.id}"] [data-terminal-split="down"]`);
  await wait(`document.querySelectorAll('.terminal-pane').length===2&&document.querySelector('.terminal-workspace').classList.contains('down')`);
  const second=(await state()).terminals.find(t=>t.id!==first.id);
  await command(`cd ${JSON.stringify(first.cwd)}; printf '\\033]7;file://localhost%s\\007' "$PWD"`);
  await wait(`fetch('/api/terminal').then(r=>r.json()).then(s=>s.terminals.find(t=>t.id==='${second.id}').cwd===${JSON.stringify(first.cwd)})`);
  assert(await evaluate(`document.querySelector('.terminal-pane.focused').dataset.terminalPane==='${second.id}'`),'different-folder second pane holds focus before splitting the first pane');
  for(let n=3;n<=4;n++){
    await click(`[data-terminal-pane="${first.id}"] [data-terminal-split="right"]`);
    await wait(`document.querySelectorAll('.terminal-pane').length===${n}&&!document.querySelector('[data-terminal-new]').disabled`);
  }
  current=await state();
  assert(current.terminals.filter(t=>![first.id,second.id].includes(t.id)).every(t=>t.cwd===cwdB&&t.shell===first.shell) && current.terminals.find(t=>t.id===second.id).cwd===first.cwd && current.tabs[0].cwd===firstTab.cwd,'pane split inherits the clicked pane cwd/shell despite another pane holding focus, without moving group');
  assert(await evaluate(`[...document.querySelectorAll('[data-terminal-split]')].every(e=>e.disabled)`),'four-pane limit disables split controls');
  assert(await evaluate(`document.querySelectorAll('.terminal-pane .terminal-view-current').length===1&&document.querySelectorAll('.terminal-pane .terminal-view-neutral').length===3&&[...document.querySelectorAll('.terminal-pane .terminal-view-neutral')].every(e=>e.getBoundingClientRect().width===20&&!e.querySelector('circle,use'))`),'focused pane has a check; unreported peers keep an empty20px slot rather than a fabricated running mark');
  const focusPeer=await evaluate(`document.querySelector('.terminal-pane.focused').dataset.terminalPane`);
  await evaluate(`document.querySelector('[data-terminal-pane="${first.id}"] textarea').focus()`);
  await command("printf '\\033]133;C\\007'; sleep 2; printf '\\033]133;D;0\\007\\033]133;A\\007'");
  await evaluate(`document.querySelector('[data-terminal-pane="${focusPeer}"] textarea').focus()`);
  await wait(`!!document.querySelector('[data-terminal-pane="${first.id}"] .terminal-view-running circle')`);
  const dotShape=await evaluate(`(()=>{const e=document.querySelector('[data-terminal-pane="${first.id}"] .terminal-view-running'),c=e.querySelector('circle');return {slot:e.getBoundingClientRect().width,diameter:Number(c.getAttribute('r'))*2,fill:c.getAttribute('fill')};})()`);
  assert(dotShape.slot===20&&dotShape.diameter===320&&dotShape.fill==='currentColor','reported shell command in a nonfocused pane uses the small filled program mark');
  await wait(`!!document.querySelector('[data-terminal-pane="${first.id}"] .terminal-view-idle circle')`);
  assert(await evaluate(`(()=>{const e=document.querySelector('[data-terminal-pane="${first.id}"] .terminal-view-idle'),c=e.querySelector('circle');return e.getBoundingClientRect().width===20&&Number(c.getAttribute('r'))*2+Number(c.getAttribute('stroke-width'))===${dotShape.diameter}&&c.getAttribute('fill')==='none'&&!!document.querySelector('[data-terminal-pane="${focusPeer}"] .terminal-view-current');})()`),'confirmed prompt uses a hollow ring with the exact same painted outer diameter as the filled dot; current selection stays independent');
  await capture('prompt-ring-and-unknown');
  await capture('four-panes');
  await click('[data-terminal-tab-menu] > summary');
  assert(await evaluate(`(()=>{const m=document.querySelector('[data-terminal-tab-menu]'),r=m.querySelector('.terminal-menu-items').getBoundingClientRect(),t=m.querySelector('summary').getBoundingClientRect();return !m.querySelector('select')&&r.top>=t.bottom&&r.right<=innerWidth&&[...m.querySelectorAll('[data-terminal-tab-actions] button')].filter(b=>!b.hidden).every(b=>b.getBoundingClientRect().height===32);})()`),'tab action rows are compact32px and below their trigger, with no native workspace select');
  await capture('compact-tab-menu');
  await key('ArrowDown');await key('End');
  assert(await evaluate(`document.activeElement.matches('[data-terminal-workspace-move]')`),'tab menu supports Arrow/Home/End keyboard navigation');
  await key('ArrowRight');
  assert(await evaluate(`document.activeElement.getAttribute('aria-checked')==='true'&&document.querySelector('[data-terminal-tab-actions]').hidden`),'workspace action opens one panel view and focuses checked current membership');
  await key('Escape');
  assert(await evaluate(`document.querySelector('[data-terminal-tab-menu]').open&&document.activeElement.matches('[data-terminal-workspace-move]')`),'Escape returns from workspace list to the originating action');
  await key('Escape');
  assert(await evaluate(`!document.querySelector('[data-terminal-tab-menu]').open&&document.activeElement.matches('[data-terminal-tab-menu]>summary')`),'second Escape closes menu and returns trigger focus');
  await click('[data-terminal-tab-menu] > summary');await key('ArrowDown');await key('Tab','Tab',0,9);
  assert(await evaluate(`!document.querySelector('[data-terminal-tab-menu]').open&&!document.activeElement.closest('[data-terminal-tab-menu]')`),'Tab dismisses the action menu and continues through page controls');
  for(const width of [1440,920,700,320]){
    await send('Emulation.setDeviceMetricsOverride',{width,height:width<=700?800:400,deviceScaleFactor:1,mobile:false});await delay(120);
    await click('[data-terminal-tab-menu] > summary');await click('[data-terminal-workspace-move]');
    assert(await evaluate(`(()=>{const m=document.querySelector('[data-terminal-tab-menu] .terminal-menu-items'),r=m.getBoundingClientRect(),t=document.querySelector('[data-terminal-tab-menu]>summary').getBoundingClientRect();return r.x>=0&&r.right<=innerWidth&&r.top>=0&&r.bottom<=innerHeight&&(r.top>=t.bottom||r.bottom<=t.top)&&[...m.querySelectorAll('button')].filter(b=>b.getClientRects().length).every(b=>b.getBoundingClientRect().height===${width<=700?40:32});})()`),`workspace panel and ${width<=700?40:32}px rows fit ${width}px viewport without covering trigger`);
    if(width===320)await capture('workspace-choices-narrow');
    await key('Escape');await key('Escape');
    await click('.terminal-pane:last-child summary');
    assert(await evaluate(`(()=>{const m=document.querySelector('.terminal-pane:last-child .terminal-menu-items'),r=m.getBoundingClientRect();return r.x>=0&&r.right<=innerWidth&&r.top>=0&&r.bottom<=innerHeight&&m.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2));})()`),`pane menu escapes canvas clipping at ${width}px`);
    await key('Escape');
  }
  await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});await delay(120);
  const deletedDefault=join(runtime,'deleted-default');await mkdir(deletedDefault);
  await evaluate(`(async()=>{const s=await(await fetch('/api/terminal/settings')).json();const r=await fetch('/api/terminal/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cwd:${JSON.stringify(deletedDefault)},shell:'/bin/sh',revision:s.revision})});if(!r.ok)throw new Error('Synthetic settings save');})()`);
  await rm(deletedDefault,{recursive:true});
  assert(await evaluate(`fetch('/api/terminal/settings?launch=true').then(r=>r.status===409)`),'deleted saved default still fails default-folder validation');
  await click('[data-terminal-new]');
  await wait(`document.querySelectorAll('[role=tab]').length===2&&!document.querySelector('[data-terminal-new]').disabled`);
  current=await state();const secondTab=current.tabs[1];
  assert(current.terminals.at(-1).cwd===firstTab.cwd,'new tab uses group root rather than current pane cwd');
  await click(`[data-terminal-focus="tab:${secondTab.id}"] .terminal-tab-name`);
  await wait(`document.activeElement.matches('.terminal-tab-input')`);
  await evaluate(`document.querySelector('.terminal-tab-input').select()`);
  await send('Input.insertText',{text:'작업 제목'});
  await evaluate(`document.querySelector('.terminal-tab-input').dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',isComposing:true,bubbles:true}))`);
  assert(await evaluate(`!!document.querySelector('.terminal-tab-input')`),'tab title Enter during composition keeps inline draft');
  await key('Enter','Enter',0,13);
  await wait(`!document.querySelector('.terminal-tab-input')&&document.querySelector('[data-terminal-focus="tab:${secondTab.id}"]').textContent.includes('작업 제목')`);
  assert((await state()).tabs.find(t=>t.id===secondTab.id).name==='작업 제목'&&dialogs.length===0,'active tab title saves inline without prompt');
  await evaluate(`document.querySelector('[data-terminal-focus="tab:${secondTab.id}"]').focus()`);await key('F2','F2',0,113);
  await wait(`!!document.querySelector('.terminal-tab-input')`);
  await evaluate(`document.querySelector('.terminal-tab-input').value='취소할 초안'`);await key('Escape','Escape',0,27);
  assert(!await evaluate(`!!document.querySelector('.terminal-tab-input')`)&&(await state()).tabs.find(t=>t.id===secondTab.id).name==='작업 제목','Escape cancels draft and preserves saved title');
  await click(`[data-terminal-focus="tab:${secondTab.id}"] .terminal-tab-name`);
  await evaluate(`document.querySelector('.terminal-tab-input').value='재시도 제목'`);failRename=true;
  await key('Enter','Enter',0,13);
  await wait(`document.querySelector('.terminal-tab-input')?.getAttribute('aria-invalid')==='true'&&!document.querySelector('.terminal-tab-input').disabled`);
  await delay(3300);
  assert(await evaluate(`document.querySelector('.terminal-tab-input').value==='재시도 제목'`),'failed title save preserves draft through periodic refresh');
  await click('[data-terminal-new]');await delay(100);
  assert((await state()).terminals.length===5&&await evaluate(`document.querySelector('.terminal-tab-input').value==='재시도 제목'`),'unconfirmed draft is not discarded by a new-tab action');
  failRename=false;await evaluate(`document.querySelector('.terminal-tab-input').focus()`);await key('Enter','Enter',0,13);
  await wait(`!document.querySelector('.terminal-tab-input')`);
  assert((await state()).tabs.find(t=>t.id===secondTab.id).name==='재시도 제목','explicit inline retry confirms the same tab title');
  await click(`[data-terminal-focus="tab:${secondTab.id}"] .terminal-tab-name`);
  await evaluate(`document.querySelector('.terminal-tab-input').value='포커스 저장';document.querySelector('[data-terminal-new]').focus()`);
  await wait(`!document.querySelector('.terminal-tab-input')`);
  assert((await state()).tabs.find(t=>t.id===secondTab.id).name==='포커스 저장'&&await evaluate(`document.activeElement.matches('[data-terminal-new]')`),'focus-out saves title without stealing new target focus');
  assert(await evaluate(`document.querySelector('[data-terminal-tab="${secondTab.id}"] .terminal-view-current')&&document.querySelector('[data-terminal-tab="${firstTab.id}"] .terminal-view-neutral')&&!document.querySelector('[data-terminal-tab="${firstTab.id}"] .terminal-view-neutral circle')`),'a mixed prompt/unknown group remains neutral while the current tab keeps its check');
  await evaluate(`document.querySelector('.terminal-pane textarea').focus()`);
  await command("printf '\\033]133;C\\007\\033]0;⠋ Synthetic Agent\\007'; sleep 1.5; printf '\\033]0;⠙ Synthetic Agent\\007'; sleep 1.5; printf '\\033]0;Synthetic Agent\\007'; sleep 2; printf '\\033]133;D;0\\007\\033]133;A\\007'");
  await wait(`document.querySelector('[data-terminal-tab="${secondTab.id}"] .terminal-program-indicator').textContent==='⠋'`);
  await evaluate(`window.__programTaskRow=document.querySelector('[data-terminal-focus="task:${secondTab.terminals[0]}"]').parentElement`);
  await evaluate(`window.__programCloseLeft=document.querySelector('[data-terminal-tab="${secondTab.id}"] .terminal-close').getBoundingClientRect().left`);
  assert(await evaluate(`document.querySelector('.terminal-pane .terminal-program-indicator').textContent==='⠋'&&document.querySelector('.terminal-pane-name').textContent==='Synthetic Agent'&&document.querySelector('[data-terminal-tab="${secondTab.id}"] .terminal-tab-name').textContent==='포커스 저장'&&document.querySelector('[data-terminal-command]').textContent.includes('명령 실행 중')`),'program-reported braille/title is separate from the current check, manual tab alias and shell command state');
  await capture('program-title-activity');
  await click(`[data-terminal-focus="tab:${secondTab.id}"] .terminal-tab-name`);
  await evaluate(`window.__programRenameInput=document.querySelector('.terminal-tab-input');window.__programRenameInput.value='보존할 초안'`);
  await wait(`document.querySelector('[data-terminal-tab="${secondTab.id}"] .terminal-program-indicator').textContent==='⠙'`);
  assert(await evaluate(`document.activeElement===window.__programRenameInput&&window.__programRenameInput.value==='보존할 초안'&&document.querySelector('[data-terminal-focus="task:${secondTab.terminals[0]}"]').parentElement===window.__programTaskRow&&window.__programTaskRow.querySelector('.terminal-program-indicator').textContent==='⠙'`),'reported title animation updates in place without rebuilding a rename editor or task row');
  await wait(`document.querySelector('[data-terminal-tab="${secondTab.id}"] .terminal-program-indicator').hidden`);
  assert(await evaluate(`document.activeElement===window.__programRenameInput&&document.querySelector('[data-terminal-command]').textContent.includes('명령 실행 중')&&!document.querySelector('.terminal-pane .terminal-program-indicator:not([hidden])')&&document.querySelector('.terminal-pane .terminal-view-current use[href$="#check"]')&&document.querySelector('[data-terminal-tab="${secondTab.id}"] .terminal-close').getBoundingClientRect().left===window.__programCloseLeft`),'removing the program title glyph clears activity while shell running/current state and the close position remain independent');
  await key('Escape','Escape',0,27);await evaluate(`document.querySelector('.terminal-pane textarea').focus()`);
  await evaluate(`window.__programTabClose=document.querySelector('[data-terminal-tab="${secondTab.id}"] .terminal-close')`);
  await wait(`document.querySelector('[data-terminal-command]').textContent.includes('프롬프트 대기')`);
  assert(await evaluate(`document.querySelector('[data-terminal-tab="${secondTab.id}"] .terminal-close')===window.__programTabClose&&window.__programTabClose.getBoundingClientRect().left===window.__programCloseLeft`),'shell completion/acknowledgement preserves both tab-close identity and painted position');
  await command("printf '\\033]133;C\\007'; sleep 6; printf '\\033]133;D;0\\007\\033]133;A\\007'");
  await click(`[data-terminal-focus="tab:${firstTab.id}"] svg`);
  await wait(`!!document.querySelector('[data-terminal-tab="${secondTab.id}"] .terminal-view-running circle')`);
  assert(await evaluate(`document.querySelector('[data-terminal-tab="${secondTab.id}"] .terminal-program-indicator').hidden&&!!document.querySelector('[data-terminal-tab="${firstTab.id}"] .terminal-view-current')`),'an inactive tab reports a running program without inventing an agent spinner');
  await wait(`!!document.querySelector('[data-terminal-tab="${secondTab.id}"] .terminal-view-idle circle')`);
  await capture('inactive-tab-prompt');
  await click(`[data-terminal-focus="tab:${secondTab.id}"] svg`);
  await wait(`document.activeElement.matches('.terminal-pane textarea')&&document.querySelector('[data-terminal-command]').textContent.includes('프롬프트 대기')&&!document.querySelector('[data-terminal-tab="${secondTab.id}"] .terminal-state-done')`);
  const tabOrder=()=>evaluate(`[...document.querySelectorAll('[data-terminal-tabs] [role=tab]')].map(e=>e.dataset.terminalFocus.slice(4))`);
  const dragTab=async(from,to,before)=>{
    const points=await evaluate(`(()=>{const a=document.querySelector('[data-terminal-tab="${from}"]').getBoundingClientRect(),b=document.querySelector('[data-terminal-tab="${to}"]').getBoundingClientRect();return {from:{x:a.left+20,y:a.top+a.height/2},to:{x:${before?'b.left+4':'b.right-4'},y:b.top+b.height/2}};})()`);
    await send('Input.dispatchMouseEvent',{type:'mouseMoved',...points.from});
    await send('Input.dispatchMouseEvent',{type:'mousePressed',button:'left',buttons:1,clickCount:1,...points.from});
    for(let i=1;i<=10;i++){await send('Input.dispatchMouseEvent',{type:'mouseMoved',button:'left',buttons:1,x:points.from.x+(points.to.x-points.from.x)*i/10,y:points.to.y});await delay(20);}
    await send('Input.dispatchMouseEvent',{type:'mouseReleased',button:'left',buttons:0,clickCount:1,...points.to});
  };
  const beforeReorder=await state();
  await dragTab(firstTab.id,secondTab.id,false);
  await wait(`fetch('/api/terminal').then(r=>r.json()).then(s=>s.presentation.order[0]==='${secondTab.id}')`);
  assert(JSON.stringify(await tabOrder())===JSON.stringify([secondTab.id,firstTab.id])&&await evaluate(`document.querySelector('[aria-selected=true]').dataset.terminalFocus==='tab:${secondTab.id}'`),'actual pointer drag reorders while preserving active tab');
  assert(JSON.stringify((await state()).terminals.map(t=>[t.id,t.pid]))===JSON.stringify(beforeReorder.terminals.map(t=>[t.id,t.pid])),'reorder changes no execution or split membership');
  await navigate('/terminal');await wait(`document.querySelectorAll('[role=tab]').length===2`);
  assert(JSON.stringify(await tabOrder())===JSON.stringify([secondTab.id,firstTab.id]),'shared order survives page reload');
  await evaluate(`document.querySelector('[data-terminal-focus="tab:${firstTab.id}"]').focus()`);await key('ArrowLeft','ArrowLeft',9,37);
  await wait(`fetch('/api/terminal').then(r=>r.json()).then(s=>s.presentation.order[0]==='${firstTab.id}')`);
  assert(JSON.stringify(await tabOrder())===JSON.stringify([firstTab.id,secondTab.id]),'Alt Shift Arrow reorders with no pointer');
  failOrder=true;failReadAfterOrder=true;await dragTab(firstTab.id,secondTab.id,false);
  await wait(`document.querySelector('[data-terminal-error]').textContent.includes('Synthetic connection failure')`);
  await delay(100);
  assert(JSON.stringify(await tabOrder())===JSON.stringify([firstTab.id,secondTab.id]),'failed order POST and GET still roll back to confirmed tab order');
  failOrder=false;failList=false;await wait(`!document.querySelector('[data-terminal-new]').disabled`);
  await click(`[data-terminal-focus="tab:${secondTab.id}"] svg`);
  holdNextTabStop=true;await click('.terminal-tab.selected .terminal-close');
  for(let i=0;i<100&&!heldTabStop;i++)await delay(20);
  assert(!!heldTabStop,'held tab-stop request before manager scope validation');
  const peer=await(await fetch(base+'/api/terminal/terminals',{method:'POST',headers:{'Content-Type':'application/json',Origin:base},body:JSON.stringify({key:crypto.randomUUID(),tabId:secondTab.id,cwd:secondTab.cwd,shell:'/bin/sh',direction:'right'})})).json();
  await send('Fetch.continueRequest',{requestId:heldTabStop});heldTabStop=null;
  await wait(`document.querySelectorAll('.terminal-pane').length===2&&document.querySelector('[data-terminal-connection]').textContent==='입력 가능'`);
  await command("printf 'REJECT_%s\\n' RECOVERED");
  await wait(`document.querySelector('.xterm-rows').textContent.includes('REJECT_RECOVERED')`);
  assert((await state()).terminals.some(t=>t.id===secondTab.terminals[0]),'rejected stale tab stop restores original pane output/input without navigation');
  await click('.terminal-pane:last-child button[aria-label="이 터미널 닫기 및 종료"]');
  await wait(`document.querySelectorAll('.terminal-pane').length===1`);
  holdNextTabStop=true;await click('.terminal-tab.selected .terminal-close');
  for(let i=0;i<100&&!heldTabStop;i++)await delay(20);
  assert(!!heldTabStop,'held a second End for view-recreation recovery');
  await click(`[data-terminal-focus="tab:${firstTab.id}"] svg`);
  holdListResponse=true;
  await send('Fetch.fulfillRequest',{requestId:heldTabStop,responseCode:409,responseHeaders:[{name:'Content-Type',value:'application/json'}],body:Buffer.from('{"error":{"code":"conflict","message":"Synthetic rejected End"}}').toString('base64')});heldTabStop=null;
  for(let i=0;i<160&&!heldListResponse;i++)await delay(20);
  assert(!!heldListResponse,'held the successful read after rejected End');
  await click(`[data-terminal-focus="tab:${secondTab.id}"] svg`);
  await wait(`document.querySelectorAll('.terminal-pane').length===1`);
  await send('Fetch.continueRequest',{requestId:heldListResponse});heldListResponse=null;
  await command("printf 'RECREATED_%s\\n' RECOVERED");
  await wait(`document.querySelector('.xterm-rows').textContent.includes('RECREATED_RECOVERED')`);
  assert((await state()).terminals.length===5,'pane recreated during rejected-End recovery resumes input without navigation or replay');
  await click('[data-terminal-folder-open]');
  await evaluate(`document.querySelector('[data-terminal-workspace-name]').value='Second';document.querySelector('[data-terminal-workspace-cwd]').value='/synthetic/missing-folder'`);
  await click('[data-terminal-workspace-submit]');
  await wait(`!document.querySelector('[data-terminal-workspace-submit]').disabled&&!document.querySelector('[data-terminal-workspace-error]').hidden`);
  assert((await state()).terminals.length===5 && await evaluate(`document.querySelector('[data-terminal-workspace-dialog]').open`),'invalid default folder keeps workspace repair dialog and creates no shell');
  await evaluate(`document.querySelector('[data-terminal-workspace-cwd]').value=${JSON.stringify(cwdB)}`);
  await click('[data-terminal-workspace-submit]');
  await wait(`document.querySelectorAll('.terminal-group').length===2&&!document.querySelector('[data-terminal-workspace-dialog]').open`);
  assert((await state()).terminals.length===5,'empty workspace creation starts no shell');
  await click('[data-terminal-new]');
  await wait(`document.querySelectorAll('.terminal-pane').length===1&&document.querySelector('[data-terminal-connection]').textContent==='입력 가능'`);
  current=await state();const other=current.terminals.at(-1),otherTab=current.tabs.at(-1);
  assert(current.terminals.length===6 && await evaluate(`document.querySelectorAll('.terminal-task').length===6&&document.querySelectorAll('[role=tab]').length===1`),'lower task list spans groups; top tabs are group-scoped');
  await command("printf '\\033]133;C\\007\\033]0;⠋ Synthetic Background Agent\\007'; sleep 2; printf '\\033]0;⠙ Synthetic Background Agent\\007'; sleep 3; printf '\\033]0;Synthetic Background Agent\\007\\033]133;D;0\\007\\033]133;A\\007QA_%s\\n' DONE");
  await wait(`fetch('/api/terminal').then(r=>r.json()).then(s=>s.terminals.find(t=>t.id==='${other.id}').activity.state==='running')`);
  await click(`[data-terminal-task-menu="${other.id}"] > summary`);
  assert(await evaluate(`(()=>{const menu=document.querySelector('[data-terminal-task-menu="${other.id}"] .terminal-menu-items'),r=menu.getBoundingClientRect(),p=document.elementFromPoint(r.x+r.width/2,r.y+15);return r.x>=0&&r.right<=innerWidth&&r.y>=0&&r.bottom<=innerHeight&&menu.contains(p);})()`),'per-task menu is painted and reachable beyond the rail scroll clip');
  await click(`[data-terminal-focus="task-action:background:${other.id}"]`);
  await wait(`document.querySelector('[data-terminal-hidden-count]').textContent==='1'`);
  await wait(`!document.querySelector('[data-terminal-focus="task:${other.id}"]')&&document.querySelector('[data-terminal-task-count]').textContent==='5'`);
  assert(await evaluate(`document.querySelector('[data-terminal-hidden-open]').getAttribute('aria-expanded')==='true'&&!document.querySelector('[data-terminal-hidden-list]').hidden&&!!document.querySelector('.terminal-rail-footer [data-terminal-hidden-list]')&&!document.querySelector('dialog[open]')`),'Hide reveals an inline rail list without a modal while foreground task rows stay removed');
  await wait(`!!document.querySelector('[data-terminal-hidden-tab="${otherTab.id}"] .terminal-state-working')`);
  assert(await evaluate(`(()=>{const row=document.querySelector('[data-terminal-hidden-tab="${otherTab.id}"]'),shape=row.querySelector('.terminal-view-hidden polygon');return shape?.getAttribute('fill')==='none'&&shape.getAttribute('points')==='480,160 800,480 480,800 160,480'&&['⠋','⠙'].includes(row.querySelector('.terminal-program-indicator').textContent)&&row.querySelector('.terminal-state-working').hidden;})()`),'a hidden tab keeps a simple hollow diamond and program-reported braille separately from shell running');
  await capture('hidden-running-status');
  await click('[data-terminal-hidden-open]');await delay(3300);
  assert(await evaluate(`document.querySelector('[data-terminal-hidden-list]').hidden&&document.querySelector('[data-terminal-hidden-open]').getAttribute('aria-expanded')==='false'`),'manual Background collapse survives periodic model refresh');
  await wait(`!!document.querySelector('[data-terminal-hidden-tab="${otherTab.id}"] .terminal-state-done')&&document.querySelector('[data-terminal-hidden-open]').classList.contains('has-completion')`);
  await key('Enter','Enter',0,13);
  assert(await evaluate(`!document.querySelector('[data-terminal-hidden-list]').hidden&&!document.querySelector('dialog[open]')`),'keyboard activation reopens inline Background with retained unread completion');
  assert(await evaluate(`!!document.querySelector('[data-terminal-hidden-tab="${otherTab.id}"] .terminal-state-done use[href$="#check_circle"]')&&!!document.querySelector('[data-terminal-hidden-tab="${otherTab.id}"] .terminal-view-hidden')&&document.querySelector('[data-terminal-hidden-tab="${otherTab.id}"] .terminal-program-indicator').hidden`),'hidden completion adds an unread result badge, keeps the diamond and clears the removed program glyph');
  await capture('hidden-unseen-completion');
  await key('Tab','Tab',0,9);
  assert(await evaluate(`document.activeElement.dataset.terminalFocus==='hidden:${otherTab.id}'&&!!document.querySelector('[data-terminal-hidden-tab="${otherTab.id}"] .terminal-state-done')`),'inline restore is keyboard reachable without acknowledging terminal output');
  current=await state();
  assert(current.tabs.find(t=>t.id===otherTab.id).hidden && current.terminals.find(t=>t.id===other.id).pid===other.pid,'hide retains same running process and unseen completion');
  await click(`[data-terminal-focus="hidden:${otherTab.id}"]`);
  await wait(`document.querySelector('[data-terminal-hidden-count]').textContent==='0'&&!!document.querySelector('[data-terminal-focus="task:${other.id}"] .terminal-state-idle')`);
  assert((await state()).terminals.find(t=>t.id===other.id).pid===other.pid,'background list restores exact hidden execution and marks painted focused completion seen');
  await command("printf '\\033]133;C\\007'; sleep 1; printf '\\033]133;D;7\\007\\033]133;A\\007'");
  await evaluate(`document.querySelector('[data-terminal-new]').focus()`);
  await wait(`!!document.querySelector('[data-terminal-focus="task:${other.id}"] .terminal-state-failed')`);
  assert(await evaluate(`(()=>{const rgb=s=>s.match(/[\\d.]+/g).slice(0,3).map(Number).map(v=>v/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);const light=s=>rgb(s).reduce((n,v,i)=>n+v*[.2126,.7152,.0722][i],0);const a=light(getComputedStyle(document.querySelector('.terminal-pane-header .terminal-state-failed')).color),b=light(getComputedStyle(document.querySelector('.terminal-pane')).backgroundColor);return (Math.max(a,b)+.05)/(Math.min(a,b)+.05)>=3;})()`),'command failure icon has essential-symbol contrast on code surface');
  assert(await evaluate(`!document.activeElement.closest('.terminal-pane')`),'pane without keyboard focus retains unseen failure');
  await evaluate(`document.querySelector('.terminal-pane textarea').focus()`);
  await wait(`!!document.querySelector('[data-terminal-focus="task:${other.id}"] .terminal-state-idle')`);
  await command("printf '\\033]133;C\\007'; sleep 1; printf '\\033]133;D;0\\007\\033]133;A\\007'");
  await key('Escape','Escape',8,27);
  await wait(`!!document.querySelector('[data-terminal-focus="task:${other.id}"] .terminal-state-done')`);
  assert(await evaluate(`document.activeElement.matches('.terminal-pane summary')`),'pane menu focus does not acknowledge command completion');
  await evaluate(`document.querySelector('.terminal-pane textarea').focus()`);
  await wait(`!!document.querySelector('[data-terminal-focus="task:${other.id}"] .terminal-state-idle')`);
  await command("printf '\\033]133;C\\007\\033[?2026h\\033]133;D;0\\007\\033]133;A\\007SYNC_%s\\n' HELD; sleep 0.8; printf '\\033[?2026l'");
  await wait(`!!document.querySelector('[data-terminal-focus="task:${other.id}"] .terminal-state-done')`);
  assert(await evaluate(`!document.querySelector('.terminal-pane .xterm-rows').textContent.includes('SYNC_HELD')`),'synchronized output completion stays unseen while render is held');
  await wait(`!!document.querySelector('[data-terminal-focus="task:${other.id}"] .terminal-state-idle')&&document.querySelector('.terminal-pane .xterm-rows').textContent.includes('SYNC_HELD')`);
  holdListResponse=true;
  for(let i=0;i<160&&!heldListResponse;i++)await delay(30);
  assert(Boolean(heldListResponse),'held actual periodic list response');
  const previousList=await send('Fetch.getResponseBody',{requestId:heldListResponse});
  const previousState=JSON.parse(previousList.base64Encoded?Buffer.from(previousList.body,'base64').toString():previousList.body);
  assert(previousState.terminals.find(t=>t.id===other.id).activity.state==='prompt','held response predates next command');
  await command("printf '\\033]133;C\\007'; sleep 1.5; printf '\\033]133;D;0\\007\\033]133;A\\007'");
  await wait(`!!document.querySelector('[data-terminal-focus="task:${other.id}"] .terminal-state-working')`);
  await send('Fetch.continueRequest',{requestId:heldListResponse});heldListResponse=null;
  await delay(100);
  assert(await evaluate(`!!document.querySelector('[data-terminal-focus="task:${other.id}"] .terminal-state-working')`),'late HTTP snapshot does not regress newer stream command state');
  await wait(`!!document.querySelector('[data-terminal-focus="task:${other.id}"] .terminal-state-idle')`);
  await click(`[data-terminal-focus="workspace:${firstSpace.id}"]`);
  assert(await evaluate(`document.querySelector('[aria-selected=true]').dataset.terminalFocus==='tab:${secondTab.id}'`),'group restores its selected tab');
  await evaluate(`document.querySelector('[data-terminal-focus="tab:${secondTab.id}"]').focus()`);
  await key('Home','Home',0,36);
  assert(await evaluate(`document.querySelector('[aria-selected=true]').dataset.terminalFocus==='tab:${firstTab.id}'`),'tab keyboard navigation stays inside group');
  await click(`[data-terminal-focus="task:${first.id}"]`);
  await wait(`document.activeElement.matches('.terminal-pane textarea')&&document.querySelector('[data-terminal-connection]').textContent==='입력 가능'`);
  await key('Escape','Escape',8,27);
  assert(await evaluate(`document.activeElement.matches('.terminal-pane summary')`),'Shift Escape transfers terminal focus to pane menu');
  await capture('groups-tasks-tabs');
  assert(await evaluate(`document.querySelector('.terminal-group').getBoundingClientRect().height<=36&&document.querySelector('.terminal-task').getBoundingClientRect().height<=36`),'workspace and task rows retain compact one-line density');
  await evaluate(`document.documentElement.classList.add('native-window-toolbar')`);
  await delay(150);
  assert(await evaluate(`(()=>{const header=document.querySelector('.workspace-header').getBoundingClientRect(),page=document.querySelector('.terminal-page').getBoundingClientRect(),footer=document.querySelector('.terminal-rail-footer').getBoundingClientRect(),status=document.querySelector('.terminal-statusbar').getBoundingClientRect();return Math.abs(header.top)<1&&page.top>=header.bottom-1&&page.bottom<=innerHeight+1&&footer.bottom<=innerHeight+1&&status.bottom<=innerHeight+1;})()`),'native titlebar class on html keeps terminal footer and statusbar within viewport');
  await capture('native-titlebar-geometry');
  await evaluate(`document.documentElement.classList.remove('native-window-toolbar')`);
  await delay(100);
  const ids=current.terminals.map(t=>t.id).sort(), generation=current.generation;
  for(const width of [920,700,320]){
    await send('Emulation.setDeviceMetricsOverride',{width,height:800,deviceScaleFactor:1,mobile:false});await delay(150);
    assert(await evaluate(`document.documentElement.scrollWidth<=innerWidth&&document.documentElement.scrollHeight<=innerHeight&&document.querySelector('.terminal-statusbar').getBoundingClientRect().bottom<=innerHeight`),'viewport containment '+width);
    if(width<=700)assert(await evaluate(`document.querySelectorAll('.terminal-pane').length===1&&!document.querySelector('[data-terminal-pane-select]').hidden`),'narrow pane switcher '+width);
    if(width===920){
      await click('[data-terminal-rail-toggle]');
      await click(`[data-terminal-task-menu="${first.id}"] > summary`);
      await click(`[data-terminal-focus="task-action:rename:${first.id}"]`);
      await wait(`!!document.querySelector('.terminal-tab-input')`);
      assert(await evaluate(`(()=>{const e=document.querySelector('.terminal-tab-input'),r=e.getBoundingClientRect();return document.querySelector('[data-terminal-rail-toggle]').getAttribute('aria-expanded')==='false'&&document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)===e;})()`),'compact task-menu rename collapses overlay and exposes actual title editor');
      await key('Escape','Escape',0,27);
    }
    await capture('width-'+width);
  }
  const longName='긴 작업 이름 - '+'abcdef'.repeat(12);
  await evaluate(`fetch('/api/terminal/tabs/${secondTab.id}/rename',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:${JSON.stringify(longName)}})})`);
  await wait(`document.querySelector('[data-terminal-focus="tab:${secondTab.id}"]')?.title.startsWith('긴 작업 이름')`);
  assert(await evaluate(`document.documentElement.scrollWidth<=innerWidth&&document.querySelector('[data-terminal-tabs]').scrollWidth>document.querySelector('[data-terminal-tabs]').clientWidth`),'long tab uses horizontal tab scroll without page overflow');
  await click('[data-terminal-rail-toggle]');
  assert(await evaluate(`document.querySelector('[data-terminal-rail-toggle]').getAttribute('aria-expanded')==='true'&&!document.querySelector('[data-terminal-rail]').inert`),'narrow rail is reachable');
  await click('[data-terminal-rail-close]');
  assert(await evaluate(`document.querySelector('[data-terminal-rail-toggle]').getAttribute('aria-expanded')==='false'&&document.activeElement.matches('[data-terminal-rail-toggle]')`),'narrow rail has reachable close and returns focus');
  assert(JSON.stringify((await state()).terminals.map(t=>t.id).sort())===JSON.stringify(ids),'responsive view changes keep every PTY');
  await navigate('/sessions');
  assert(await evaluate(`!document.body.classList.contains('terminal-route')&&getComputedStyle(document.querySelector('.app-main')).paddingTop!=='0px'&&getComputedStyle(document.body).getPropertyValue('--shell-header-height').trim()==='48px'`),'reading routes keep normal page layout and share the compact header');
  await navigate('/terminal');await wait(`!document.querySelector('[data-terminal-new]').disabled`);
  assert((await state()).generation===generation,'navigation reconnects same manager generation');
  failList=true;await navigate('/terminal');
  await wait(`!document.querySelector('[data-terminal-error]').hidden`);
  assert(await evaluate(`document.querySelector('[data-terminal-new]').disabled`),'failed initial API read gates creation');
  failList=false;await wait(`!document.querySelector('[data-terminal-new]').disabled`);
  failFonts=true;await navigate('/terminal');
  await wait(`!document.querySelector('[data-terminal-font-retry]').hidden`);
  assert(await evaluate(`document.querySelector('[data-terminal-new]').disabled&&!document.querySelector('.terminal-pane')`),'font failure has retry and does not render fallback');
  failFonts=false;await click('[data-terminal-font-retry]');await wait(`document.querySelector('[data-terminal-new]')?.disabled===false`);
  assert((await state()).terminals.length===ids.length,'failure and recovery do not terminate or duplicate work');
  await ensureRail();await click(`[data-terminal-focus="task:${other.id}"]`);
  await wait(`!!document.querySelector('[data-terminal-focus="close:${otherTab.id}"]')`);
  await click(`[data-terminal-focus="close:${otherTab.id}"]`);
  await wait(`fetch('/api/terminal').then(r=>r.json()).then(s=>s.terminals.length===${ids.length-1})`);
  current=await state();
  assert(dialogs.length===0&&!current.tabs.some(t=>t.id===otherTab.id)&&!current.terminals.some(t=>t.id===other.id),'tab close has no dialog and ends only its exact scope');
  assert(await evaluate(`document.querySelectorAll('.terminal-group').length===2`)&&current.terminals.every(t=>ids.includes(t.id)),'last tab removal preserves its empty workspace and other executions');
  const exactFolder=join(runtime,'folder ');await mkdir(exactFolder);await mkdir(join(runtime,'folder'));
  await click('[data-terminal-tab-menu] > summary');await click('[data-terminal-folder-tab]');
  await wait(`document.querySelector('[data-terminal-folder-dialog]').open&&!document.querySelector('[data-terminal-folder-path]').disabled`);
  await evaluate(`document.querySelector('[data-terminal-folder-path]').value=${JSON.stringify(exactFolder)}`);
  await click('[data-terminal-folder-submit]');
  await wait(`!document.querySelector('[data-terminal-folder-dialog]').open&&document.activeElement.matches('.terminal-pane textarea')`);
  current=await state();const exact=current.terminals.find(t=>!ids.includes(t.id));
  assert(exact?.cwd===exactFolder&&await evaluate(`document.querySelector('[data-terminal-rail-toggle]').getAttribute('aria-expanded')==='false'`),'narrow folder open preserves trailing space and reveals focused pane');
  await evaluate(`fetch('/api/terminal/tabs/${exact.tabId}/stop',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({expected:{generation:${JSON.stringify(generation)},terminals:['${exact.id}']}})})`);
  await wait(`!document.querySelector('[data-terminal-focus="tab:${exact.tabId}"]')`);
  await ensureRail();await click('[data-terminal-manage]');
  acceptNextDialog=true;await click('[data-terminal-service="restart"]');
  await wait(`fetch('/api/terminal').then(r=>r.json()).then(s=>s.generation&&s.generation!==${JSON.stringify(generation)}&&s.terminals.length===0)`);
  await wait(`document.querySelectorAll('.terminal-task').length===0&&document.querySelectorAll('.terminal-group').length===2`);
  assert(dialogs.length===1&&dialogs[0].includes('5개')&&(await state()).tabs.length===0,'explicit restart clears process/status membership while preserving empty workspace identities');
  await click('[data-terminal-dialog-close]');await click('[data-terminal-rail-close]');
  await evaluate(`(async()=>{const s=await(await fetch('/api/terminal/settings')).json();await fetch('/api/terminal/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cwd:${JSON.stringify(join(runtime,'demo-a'))},shell:'/bin/sh',revision:s.revision})});})()`);
  for(const closeKind of ['tab','pane','tab']) {
    await wait(`document.querySelector('[data-terminal-new]')?.disabled===false`);
    if(closeKind==='pane')loseCreateResponse='503';
    await click('[data-terminal-new]');
    if(closeKind==='pane') {
      await wait(`!document.querySelector('[data-terminal-create-retry]').hidden&&!document.querySelector('[data-terminal-create-retry]').disabled`);
      const uncertain503=await state();
      assert(uncertain503.terminals.length===1&&await evaluate(`document.querySelector('[data-terminal-new]').disabled`),'uncertain 503 preserves one created shell and retry gate');
      await click('[data-terminal-create-retry]');
      await wait(`document.querySelector('[data-terminal-create-retry]').hidden&&document.querySelectorAll('.terminal-pane').length===1&&document.querySelector('[data-terminal-connection]').textContent==='입력 가능'`);
      const recovered503=await state();
      assert(recovered503.terminals.length===1&&recovered503.terminals[0].pid===uncertain503.terminals[0].pid&&creationRequests.at(-1).key===creationRequests.at(-2).key,'503 retry reuses exact key and PTY');
    }
    await wait(`document.querySelectorAll('.terminal-pane').length===1&&document.querySelector('[data-terminal-connection]').textContent==='입력 가능'`);
    await click(closeKind==='tab'?'.terminal-tab .terminal-close':'.terminal-pane-header button[aria-label="이 터미널 닫기 및 종료"]');
    await wait(`document.querySelectorAll('.terminal-pane').length===0&&document.querySelector('[data-terminal-new]')?.disabled===false`);
    assert((await state()).terminals.length===0,'last '+closeKind+' close permits another toolbar New');
  }
  assert(dialogs.length===1,'individual pane/tab closes never add a confirmation');
  await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
  if(await evaluate(`document.querySelector('[data-terminal-rail-toggle]').getAttribute('aria-expanded')==='false'`)) await click('[data-terminal-rail-toggle]');
  await click('[data-terminal-new]');
  await wait(`document.querySelector('[data-terminal-connection]').textContent==='입력 가능'`);
  const cleanExit=(await state()).terminals[0];
  busyRetireTarget=cleanExit.id;
  await command('exit');
  await wait(`fetch('/api/terminal').then(r=>r.json()).then(s=>s.terminals.length===0&&s.tabs.length===0)`);
  await wait(`document.querySelectorAll('.terminal-group').length===2&&!document.querySelector('[data-terminal-new]').disabled&&!document.querySelector('[data-terminal-focus="task:${cleanExit.id}"]')`);
  assert(!await evaluate(`!!document.querySelector('[data-terminal-focus="task:${cleanExit.id}"]')`),'normal shell exit removes terminal/tab while retaining empty workspaces');
  await wait(`document.activeElement.matches('[data-terminal-new]')`);
  assert(injectedRetireBusy===1&&!await evaluate(`document.querySelector('[data-terminal-error]').textContent.includes('정리하지 못')`),'transient retirement contention retries and clean exit returns keyboard focus to New');
  await click('[data-terminal-new]');
  await wait(`document.querySelector('[data-terminal-connection]').textContent==='입력 가능'`);
  await command('exit 7');
  await wait(`fetch('/api/terminal').then(r=>r.json()).then(s=>s.terminals.length===0)`);
  assert((await state()).tabs.length===0,'explicit nonzero shell exit also retires after confirmed process cleanup');
  await wait(`document.querySelectorAll('.terminal-pane').length===0`);
  await click('[data-terminal-new]');
  await wait(`document.querySelector('[data-terminal-connection]').textContent==='입력 가능'`);
  const retainedSibling=(await state()).terminals[0];
  await click('[data-terminal-split="right"]');
  await wait(`document.querySelectorAll('.terminal-pane').length===2&&document.activeElement.matches('.terminal-pane:last-child textarea')`);
  await command('exit');
  await wait(`fetch('/api/terminal').then(r=>r.json()).then(s=>s.terminals.length===1)`);
  const siblingState=await state();
  assert(siblingState.terminals[0].id===retainedSibling.id&&siblingState.terminals[0].pid===retainedSibling.pid,'split shell exit retires only that pane and preserves sibling execution');
  await wait(`document.activeElement.matches('.terminal-pane textarea')`);
  await click('.terminal-tab .terminal-close');await wait(`document.querySelectorAll('.terminal-pane').length===0`);
  await click('[data-terminal-new]');await wait(`document.querySelector('[data-terminal-connection]').textContent==='입력 가능'`);
  const hiddenExit=(await state()).terminals[0];
  await command('sleep 1; exit');
  await click(`[data-terminal-task-menu="${hiddenExit.id}"] > summary`);
  await click(`[data-terminal-focus="task-action:background:${hiddenExit.id}"]`);
  await wait(`document.querySelector('[data-terminal-hidden-count]').textContent==='1'`);
  await wait(`fetch('/api/terminal').then(r=>r.json()).then(s=>s.terminals.length===0)`);
  await wait(`document.querySelector('[data-terminal-hidden-count]').textContent==='0'`);
  assert(dialogs.length===1,'background clean shell exit retires without confirmation or foreground clutter');
  incompatibleService=true;await navigate('/terminal');
  await wait(`document.querySelector('[data-terminal-new]').disabled&&!document.querySelector('[data-terminal-update-service]').hidden&&document.querySelector('[data-terminal-error]').textContent.includes('이전 버전')`);
  assert(await evaluate(`document.querySelector('[data-terminal-error]').textContent.includes('이전 버전')`),'incompatible empty service explains disabled New and exposes update');
  const oldGeneration=(await state()).generation;
  incompatibleService=false;await click('[data-terminal-update-service]');
  await wait(`document.querySelector('[data-terminal-new]')?.disabled===false&&document.querySelector('[data-terminal-update-service]').hidden`);
  assert((await state()).generation!==oldGeneration&&(await state()).terminals.length===0,'explicit empty-service update restores New without creating or terminating work');
  const roomsBefore = (await state()).workspaces.items.map(item=>[item.id,item.name,item.cwd]);
  const cwdA = firstSpace.cwd;
  await ensureRail();await click('[data-terminal-folder-open]');
  await evaluate(`document.querySelector('[data-terminal-workspace-name]').value='Mixed roots';document.querySelector('[data-terminal-workspace-cwd]').value=${JSON.stringify(cwdA)}`);
  await click('[data-terminal-workspace-submit]');await wait(`!document.querySelector('[data-terminal-workspace-dialog]').open`);
  const mixed = (await state()).workspaces.items.find(item=>item.name==='Mixed roots');
  assert(mixed.tabs.length===0&&(await state()).terminals.length===0,'named workspace may be created empty with a default folder');
  await click('[data-terminal-new]');await wait(`document.querySelector('[data-terminal-connection]').textContent==='입력 가능'`);
  const mixedFirst=(await state()).terminals[0];
  await click('.terminal-pane-header summary');await click('[data-terminal-split-folder]');
  await wait(`document.querySelector('[data-terminal-folder-dialog]').open&&!document.querySelector('[data-terminal-folder-path]').disabled`);
  await evaluate(`document.querySelector('[data-terminal-folder-path]').value=${JSON.stringify(cwdB)}`);
  await click('[data-terminal-folder-submit]');
  await wait(`!document.querySelector('[data-terminal-folder-dialog]').open&&document.querySelectorAll('.terminal-pane').length===2`);
  let mixedState=await state();
  assert(mixedState.terminals.length===2&&new Set(mixedState.terminals.map(t=>t.cwd)).size===2&&new Set(mixedState.terminals.map(t=>t.tabId)).size===1&&mixedState.workspaces.items.find(item=>item.id===mixed.id).tabs.length===1,'one tab holds split terminals from different roots inside the same workspace');
  await click('[data-terminal-tab-menu] > summary');await click('[data-terminal-folder-tab]');
  await wait(`document.querySelector('[data-terminal-folder-dialog]').open&&!document.querySelector('[data-terminal-folder-path]').disabled`);
  await evaluate(`document.querySelector('[data-terminal-folder-path]').value=${JSON.stringify(cwdB)}`);
  await click('[data-terminal-folder-submit]');await wait(`!document.querySelector('[data-terminal-folder-dialog]').open&&document.querySelectorAll('[role=tab]').length===2`);
  mixedState=await state();const mixedTabs=mixedState.tabs.filter(tab=>mixedState.workspaces.items.find(item=>item.id===mixed.id).tabs.includes(tab.id));
  assert(mixedTabs.length===2&&new Set(mixedTabs.map(tab=>tab.cwd)).size===2,'workspace tabs can use different initial folders');
  await delay(350);
  await dragTab(mixedTabs[0].id,mixedTabs[1].id,false);
  await wait(`fetch('/api/terminal').then(r=>r.json()).then(s=>s.presentation.order.indexOf('${mixedTabs[1].id}')<s.presentation.order.indexOf('${mixedTabs[0].id}'))`);
  assert(JSON.stringify(await tabOrder())===JSON.stringify([mixedTabs[1].id,mixedTabs[0].id]),'pointer ordering follows workspace membership across different roots');
  const movedTab=mixedTabs[1],beforeMove=(await state()).terminals.map(t=>[t.id,t.pid]);
  await click('[data-terminal-tab-menu] > summary');await click('[data-terminal-workspace-move]');
  await click(`[data-terminal-tab="${mixedTabs[0].id}"] [role=tab]`);
  assert(await evaluate(`!document.querySelector('[data-terminal-tab-menu]').open&&document.querySelector('[data-terminal-workspace-choices]').hidden`),'changing the active tab dismisses the old workspace action context');
  await click(`[data-terminal-tab="${movedTab.id}"] [role=tab]`);
  await click('[data-terminal-tab-menu] > summary');
  await click('[data-terminal-workspace-move]');
  await evaluate(`document.querySelector('[data-terminal-workspace-destination="${firstSpace.id}"]').focus()`);
  await delay(3300);
  assert(await evaluate(`document.querySelector('[data-terminal-tab-menu]').open&&!document.querySelector('[data-terminal-workspace-choices]').hidden&&document.activeElement.dataset.terminalWorkspaceDestination==='${firstSpace.id}'&&document.querySelector('[data-terminal-workspace-destination="${mixed.id}"]').getAttribute('aria-checked')==='true'`),'polling preserves the workspace chooser, checked membership and focused destination');
  await capture('workspace-choices-wide');
  failWorkspaceMove=true;
  await key('Enter','Enter',0,13);
  await wait(`document.querySelector('[data-terminal-error]').textContent.includes('Synthetic')&&document.activeElement.matches('[data-terminal-tab-menu]>summary')`);
  assert((await state()).workspaces.items.find(item=>item.id===mixed.id).tabs.includes(movedTab.id)&&JSON.stringify((await state()).terminals.map(t=>[t.id,t.pid]))===JSON.stringify(beforeMove),'failed workspace move retains membership/processes and returns focus for retry');
  failWorkspaceMove=false;
  await click('[data-terminal-tab-menu] > summary');await click('[data-terminal-workspace-move]');
  await evaluate(`document.querySelector('[data-terminal-workspace-destination="${firstSpace.id}"]').focus()`);
  await key('Enter','Enter',0,13);
  await wait(`fetch('/api/terminal').then(r=>r.json()).then(s=>s.workspaces.items.find(item=>item.id==='${firstSpace.id}').tabs.includes('${movedTab.id}'))`);
  await command("printf 'WORKSPACE_%s\\n' MOVED");
  await wait(`document.querySelector('.xterm-rows').textContent.includes('WORKSPACE_MOVED')`);
  assert(JSON.stringify((await state()).terminals.map(t=>[t.id,t.pid]))===JSON.stringify(beforeMove),'moving an existing tab between workspaces preserves exact processes and writable input');
  await capture('mixed-roots-and-status');
  while((await state()).tabs.length){
    const remaining=(await state()).terminals[0];await ensureRail();await click(`[data-terminal-focus="task:${remaining.id}"]`);
    await click('.terminal-tab.selected .terminal-close');
    await wait(`fetch('/api/terminal').then(r=>r.json()).then(s=>!s.terminals.some(t=>t.id==='${remaining.id}'))`);
  }
  const emptyRooms=(await state()).workspaces.items.map(item=>[item.id,item.name,item.cwd]);
  await navigate('/terminal');await wait(`!document.querySelector('[data-terminal-new]').disabled`);
  assert(JSON.stringify((await state()).workspaces.items.map(item=>[item.id,item.name,item.cwd]))===JSON.stringify(emptyRooms)&&(await state()).terminals.length===0,'all workspace identities/names/defaults survive last-shell close and page reload without replay');
  await ensureRail();await click(`[data-terminal-focus="workspace-edit:${mixed.id}"]`);
  assert(await evaluate(`!document.querySelector('[data-terminal-workspace-remove]').disabled`),'empty workspace offers an explicit list-removal action');
  await click('[data-terminal-workspace-remove]');await wait(`!document.querySelector('[data-terminal-workspace-dialog]').open`);
  await access(cwdA);await access(cwdB);
  assert(!(await state()).workspaces.items.some(item=>item.id===mixed.id)&&JSON.stringify((await state()).workspaces.items.map(item=>[item.id,item.name,item.cwd]))===JSON.stringify(roomsBefore),'explicit removal forgets only the empty workspace and keeps directories/other groups');
  const backgroundViewport=await evaluate(`({width:innerWidth,height:innerHeight,expanded:document.querySelector('[data-terminal-rail-toggle]').getAttribute('aria-expanded')==='true'})`);
  const backgroundFixtures=await evaluate(`(async()=>{const tabs=[];for(let i=0;i<6;i++){const response=await fetch('/api/terminal/terminals',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key:crypto.randomUUID(),workspaceId:'${firstSpace.id}',cwd:${JSON.stringify(cwdA)},shell:'/bin/sh'})});if(!response.ok)throw new Error('Synthetic background creation');const term=(await response.json()).terminal;const hidden=await fetch('/api/terminal/tabs/'+term.tabId+'/hide',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});if(!hidden.ok)throw new Error('Synthetic background hide');tabs.push({id:term.tabId,terminal:term.id,pid:term.pid});}return tabs;})()`);
  await send('Emulation.setDeviceMetricsOverride',{width:1440,height:400,deviceScaleFactor:1,mobile:false});await ensureRail();
  await wait(`document.querySelector('[data-terminal-hidden-count]').textContent==='6'`);
  if(await evaluate(`document.querySelector('[data-terminal-hidden-list]').hidden`))await click('[data-terminal-hidden-open]');
  for(const size of [{width:1440,height:400},{width:700,height:800},{width:320,height:800}]){
    await send('Emulation.setDeviceMetricsOverride',{...size,deviceScaleFactor:1,mobile:false});await ensureRail();
  assert(await evaluate(`(()=>{const rail=document.querySelector('.terminal-rail').getBoundingClientRect(),list=document.querySelector('[data-terminal-hidden-list]'),r=list.getBoundingClientRect(),footer=document.querySelector('.terminal-rail-footer').getBoundingClientRect(),tools=document.querySelector('.terminal-rail-utilities').getBoundingClientRect();return list.scrollHeight>list.clientHeight&&r.height>0&&r.top>=rail.top&&r.bottom<=tools.top&&footer.height<=rail.height*.4+1&&tools.bottom<=rail.bottom&&document.querySelector('.terminal-groups-section').getBoundingClientRect().height>0&&document.querySelector('.terminal-tasks-section').getBoundingClientRect().height>0&&document.documentElement.scrollHeight===innerHeight;})()`),'many hidden tabs scroll inside the bounded footer while group/task regions and utilities remain reachable in a short viewport');
    await capture('background-many-'+size.width);
  }
  await send('Emulation.setDeviceMetricsOverride',{width:1440,height:400,deviceScaleFactor:1,mobile:false});await ensureRail();
  await evaluate(`document.querySelector('[data-terminal-hidden-open]').focus()`);
  for(let i=0;i<backgroundFixtures.length*2;i++)await key('Tab','Tab',0,9);
  assert(await evaluate(`(()=>{const e=document.activeElement,l=document.querySelector('[data-terminal-hidden-list]'),r=e.getBoundingClientRect(),b=l.getBoundingClientRect();return e.dataset.terminalFocus==='hidden-stop:${backgroundFixtures.at(-1).id}'&&r.top>=b.top-1&&r.bottom<=b.bottom+1;})()`),'keyboard focus scrolls the final hidden-tab End target into view');
  const backgroundBeforeEnd=await state();await key('Enter','Enter',0,13);
  await wait(`document.querySelector('[data-terminal-hidden-count]').textContent==='5'`);
  const backgroundAfterEnd=await state();
  assert(backgroundAfterEnd.generation===backgroundBeforeEnd.generation&&backgroundAfterEnd.terminals.length===5&&backgroundFixtures.slice(0,-1).every(item=>backgroundAfterEnd.terminals.some(term=>term.id===item.terminal&&term.pid===item.pid))&&await evaluate(`!!document.activeElement.closest('[data-terminal-hidden-list]')`),'inline End has no confirmation, preserves other exact processes and keeps list focus');
  await evaluate(`(async()=>{const s=await(await fetch('/api/terminal')).json();for(const tab of s.tabs){const response=await fetch('/api/terminal/tabs/'+tab.id+'/stop',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({expected:{generation:s.generation,terminals:tab.terminals}})});if(!response.ok)throw new Error('Synthetic background cleanup');}})()`);
  await wait(`document.querySelector('[data-terminal-hidden-count]').textContent==='0'`);
  assert(await evaluate(`document.activeElement.matches('[data-terminal-hidden-open]')`),'peer removal of the focused final hidden row restores disclosure focus');
  await send('Emulation.setDeviceMetricsOverride',{width:backgroundViewport.width,height:backgroundViewport.height,deviceScaleFactor:1,mobile:false});
  if(!backgroundViewport.expanded&&await evaluate(`document.querySelector('[data-terminal-rail-toggle]').getAttribute('aria-expanded')==='true'`))await click('[data-terminal-rail-close]');
  await click(`[data-terminal-focus="workspace:${firstSpace.id}"]`);
  await evaluate(`(async()=>{const s=await(await fetch('/api/terminal/settings')).json();await fetch('/api/terminal/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cwd:${JSON.stringify(cwdA)},shell:'/bin/zsh',revision:s.revision})});})()`);
  await click('[data-terminal-new]');
  await wait(`document.querySelector('[data-terminal-connection]').textContent==='입력 가능'&&!!document.querySelector('.terminal-state-idle')`);
  const zshTerm=(await state()).terminals[0];
  assert(zshTerm.activity.state==='prompt'&&await evaluate(`!!document.querySelector('.terminal-pane .terminal-view-current use[href$="#check"]')&&document.querySelector('[data-terminal-command]').textContent.includes('프롬프트 대기')`),'default zsh reports a prompt separately from the same current-view check');
  const promptShape=await evaluate(`(()=>{const e=document.querySelector('.terminal-pane .terminal-view-current'),b=e.getBoundingClientRect(),p=e.getBBox();return {width:b.width,height:b.height,inkWidth:p.width,inkHeight:p.height};})()`);
  assert(promptShape.width===currentShape.width&&promptShape.height===currentShape.height&&Math.abs(promptShape.inkWidth-currentShape.inkWidth)<0.01&&Math.abs(promptShape.inkHeight-currentShape.inkHeight)<0.01,'old unknown and new integrated prompt have identical painted current-view marks');
  await command('sleep 0.5; false');
  await wait(`!!document.querySelector('.terminal-state-working')`);
  await wait(`fetch('/api/terminal').then(r=>r.json()).then(s=>s.terminals[0].activity.state==='prompt'&&s.terminals[0].activity.exitCode===1)`);
  assert((await state()).terminals[0].activity.completion>0,'real zsh reports command running and nonzero completion without manual escape sequences');
  await command('sleep 5');await wait(`!!document.querySelector('.terminal-state-working')`);
  await key('c','KeyC',2,67);
  await wait(`fetch('/api/terminal').then(r=>r.json()).then(s=>s.terminals[0].activity.state==='prompt'&&s.terminals[0].activity.exitCode===130)`);
  assert((await state()).terminals[0].id===zshTerm.id,'Ctrl C returns the same zsh to prompt and reports interruption result');
  await capture('zsh-prompt-compact');
  const extraSpaces=await evaluate(`(async()=>{const ids=[];for(let i=0;i<24;i++){const response=await fetch('/api/terminal/workspaces/create',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:'Synthetic long workspace '+i+' — '+('project folder '.repeat(5)),cwd:''})});if(!response.ok)throw new Error('Synthetic menu fixture');ids.push((await response.json()).id);}return ids;})()`);
  await wait(`document.querySelectorAll('.terminal-group').length===${emptyRooms.length-1+extraSpaces.length}`);
  await send('Emulation.setDeviceMetricsOverride',{width:320,height:800,deviceScaleFactor:1,mobile:false});await delay(120);
  await click('[data-terminal-tab-menu] > summary');await click('[data-terminal-workspace-move]');await key('End');
  assert(await evaluate(`(()=>{const m=document.querySelector('[data-terminal-tab-menu] .terminal-menu-items'),b=document.activeElement,r=b.getBoundingClientRect(),p=m.getBoundingClientRect();return b.dataset.terminalWorkspaceDestination==='${extraSpaces.at(-1)}'&&m.scrollHeight>m.clientHeight&&p.x>=0&&p.right<=innerWidth&&p.top>=0&&p.bottom<=innerHeight&&b.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2))&&b.title.length>70;})()`),'long workspace names stay bounded and End scrolls the last destination into a reachable narrow menu');
  await capture('workspace-long-list-narrow');
  await click('#global-query');
  assert(await evaluate(`!document.querySelector('[data-terminal-tab-menu]').open`),'outside focus/click in the shared header dismisses the Terminal menu');
  await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});await delay(120);
  await click('.terminal-pane-header summary');await click('[data-terminal-tab-menu] > summary');
  assert(await evaluate(`document.querySelectorAll('.terminal-menu[open]').length===1&&document.querySelector('[data-terminal-tab-menu]').open`),'switching from pane to visible tab trigger leaves only the tab action surface open');
  await key('Escape');
  await evaluate(`(async()=>{for(const id of ${JSON.stringify(extraSpaces)}){const r=await fetch('/api/terminal/workspaces/remove',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});if(!r.ok)throw new Error('Synthetic menu cleanup');}})()`);
  await evaluate(`document.querySelector('.xterm-helper-textarea').focus()`);
  await evaluate(`(async()=>{const s=await(await fetch('/api/terminal')).json();const r=await fetch('/api/terminal/terminals/${zshTerm.id}/stop',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({generation:s.generation})});if(!r.ok)throw new Error('Synthetic peer close');})()`);
  await wait(`document.querySelectorAll('.terminal-pane').length===0&&document.activeElement.matches('[data-terminal-new]')`);
  assert((await state()).terminals.length===0,'confirmed peer removal restores focused last-pane input to New when polling applies the actual unmount');
  assert(exceptions.length===0 && failures.length===0,'no runtime exceptions or interception failures');
  await writeFile(join(output,'result.json'),JSON.stringify({result:'PASS',checks,exceptions,failures,hostEvidence:'Chromium with real synthetic PTYs; not packaged macOS/physical IME/sleep evidence'},null,2));
  console.log(JSON.stringify({result:'PASS',checks:checks.length,evidence:output}));
} catch(error) {
  let focus;
  if(evaluate)try{focus=await evaluate(`({tag:document.activeElement.tagName,classes:document.activeElement.className,key:document.activeElement.dataset.terminalFocus,status:document.querySelector('[data-terminal-connection]')?.textContent})`);}catch{}
  await writeFile(join(output,'failure.json'),JSON.stringify({error:error.message,checks,exceptions,failures,backendError,focus},null,2));
  if(send)try{const result=await send('Page.captureScreenshot',{format:'png'});await writeFile(join(output,'failure.png'),Buffer.from(result.data,'base64'));}catch{}
  throw error;
} finally {
  socket?.close();for(const waiter of pending.values())clearTimeout(waiter.timer);
  await stop(chrome,'SIGTERM');await stop(backend,'SIGINT');
  await rm(profile,{recursive:true,force:true});await rm(runtimeOwner,{recursive:true,force:true});
  if(!process.argv[2])await rm(output,{recursive:true,force:true});
}
