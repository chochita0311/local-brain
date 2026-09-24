// Synthetic-only end-to-end map checks. Never point this at private runtime data.
import {spawn} from 'node:child_process';
import {mkdir, rm, writeFile} from 'node:fs/promises';
import {join} from 'node:path';

const [base, output] = process.argv.slice(2);
if (!base || !output || !['127.0.0.1', 'localhost'].includes(new URL(base).hostname)) throw new Error('Local synthetic URL and task output required');
await mkdir(output, {recursive: true});
const profile = join(output, 'chrome-profile'), port = 9700 + process.pid % 100;
const browser = spawn(process.env.LOCALBRAIN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', [
  '--headless=new', '--disable-gpu', '--disable-background-networking', '--disable-component-update',
  '--no-first-run', '--no-default-browser-check', `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`, 'about:blank',
], {stdio: 'ignore'});
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const assert = (condition, message) => {if (!condition) throw new Error(message);};
let socket;
try {
  let target;
  for (let i = 0; i < 100 && !target; i++) {
    try {target = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, {method: 'PUT'})).json();} catch {await delay(100);}
  }
  assert(target, 'Browser unavailable');
  socket = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {socket.addEventListener('open', resolve, {once: true}); socket.addEventListener('error', reject, {once: true});});
  let sequence = 0, writes = 0;
  const pending = new Map(), exceptions = [];
  socket.addEventListener('message', event => {
    const value = JSON.parse(event.data);
    if (value.method === 'Runtime.exceptionThrown') exceptions.push(value.params.exceptionDetails.text);
    if (value.method === 'Network.requestWillBeSent' && !['GET', 'HEAD'].includes(value.params.request.method)) writes++;
    if (!value.id) return;
    const waiter = pending.get(value.id); if (!waiter) return;
    pending.delete(value.id); clearTimeout(waiter.timer);
    if (value.error) waiter.reject(new Error('CDP command failed')); else waiter.resolve(value.result);
  });
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const id = ++sequence;
    pending.set(id, {resolve, reject, timer: setTimeout(() => reject(new Error('CDP timeout: ' + method)), 15000)});
    socket.send(JSON.stringify({id, method, params}));
  });
  const evaluate = async expression => {
    const value = await send('Runtime.evaluate', {expression, returnByValue: true, awaitPromise: true});
    assert(!value.exceptionDetails, 'Page evaluation failed'); return value.result.value;
  };
  const wait = async expression => {
    for (let i = 0; i < 160; i++) {if (await evaluate(expression)) return; await delay(100);}
    throw new Error('Expected state unavailable: ' + expression);
  };
  const navigate = async path => {
    await evaluate('window.__previousQAView = true');
    await send('Page.navigate', {url: base + path});
    await wait("!window.__previousQAView && document.readyState === 'complete'");
  };
  const settled = () => wait("document.querySelector('[data-affinity-root]') && !document.querySelector('[data-affinity-root]').hasAttribute('aria-busy')");
  const click = async selector => {
    await evaluate(`(() => {const e=document.querySelector(${JSON.stringify(selector)});if(!e)return;if(e.closest('svg')){e.focus({preventScroll:true});e.closest('[data-affinity-canvas]').scrollIntoView({block:'center'});}else e.scrollIntoView({block:'center',inline:'nearest'});})()`);
    // Wait outside page script so the same helper works with scripting disabled.
    await delay(80);
    const point = await evaluate(`(() => {const e=document.querySelector(${JSON.stringify(selector)});if(!e)return null;const r=e.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})()`);
    assert(point, 'Click target missing: ' + selector);
    await send('Input.dispatchMouseEvent', {type: 'mousePressed', button: 'left', clickCount: 1, ...point});
    await send('Input.dispatchMouseEvent', {type: 'mouseReleased', button: 'left', clickCount: 1, ...point});
    await delay(150);
  };
  const capture = async name => {
    const shot = await send('Page.captureScreenshot', {format: 'png', captureBeyondViewport: false});
    await writeFile(join(output, name + '.png'), Buffer.from(shot.data, 'base64'));
  };
  await send('Page.enable'); await send('Runtime.enable'); await send('Network.enable');
  await send('Network.setCacheDisabled', {cacheDisabled: true});
  await navigate('/auto-work');
  assert(await evaluate("document.body.textContent.includes('synthetic-fixture')"), 'Synthetic fixture required');
  const viewports = [];
  for (const width of [1440, 920, 700, 320]) {
    await send('Emulation.setDeviceMetricsOverride', {width, height: 1000, deviceScaleFactor: 1, mobile: false});
    await navigate('/auto-work');
    const result = await evaluate(`(() => {const nav=[...document.querySelectorAll('.lnb-item')];return {width:innerWidth,overflow:document.documentElement.scrollWidth>document.documentElement.clientWidth,enhanced:document.querySelector('[data-affinity-root]').dataset.enhanced,nodes:document.querySelectorAll('[data-affinity-map-node]').length,columns:getComputedStyle(document.querySelector('.affinity-layout')).gridTemplateColumns.split(' ').length,sidebar:nav.findIndex(e=>e.getAttribute('href')==='/auto-work')+1===nav.findIndex(e=>e.getAttribute('href')==='/workstreams'),fallbackOpen:document.querySelector('[data-affinity-list]').open,buttonHeight:document.querySelector('[data-map-action="in"]').getBoundingClientRect().height};})()`);
    assert(result.width === width && !result.overflow && result.enhanced === 'true' && result.nodes > 48 && result.sidebar, 'Viewport/map contract: ' + JSON.stringify(result));
    assert(await evaluate("(() => {const p=JSON.parse(document.querySelector('[data-affinity-graph]').textContent),c=document.querySelector('[data-affinity-canvas]');return p.nodes.length===document.querySelectorAll('[data-affinity-map-node]').length&&c.scrollWidth>c.clientWidth&&c.scrollHeight>c.clientHeight&&document.querySelector('[data-affinity-pagination]').closest('[data-affinity-list]');})()"), 'Whole-scope continuous canvas and list-only pagination');
    assert(result.columns === (width > 920 ? 2 : 1) && (width > 700 || result.fallbackOpen && result.buttonHeight >= 40), 'Responsive contract');
    await capture('affinity-' + width); viewports.push(result);
    // Native list selection remains practical at every width.
    await evaluate("document.querySelector('[data-affinity-list]').open=true");
    await click('[data-affinity-node]'); await settled();
    assert(await evaluate("Boolean(document.querySelector('[data-affinity-evidence]')) && !document.querySelector('.affinity-evidence script')"), 'Exact escaped evidence');
    assert(await evaluate("document.documentElement.scrollWidth<=document.documentElement.clientWidth"), 'Selected overflow');
    await capture('affinity-selected-' + width);
  }
  await send('Emulation.setDeviceMetricsOverride', {width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false});
  await navigate('/auto-work');
  await click('[data-map-action="fit"]');
  const temporal = await evaluate(`(() => {
    const payload=JSON.parse(document.querySelector('[data-affinity-graph]').textContent);
    const knots=[...document.querySelectorAll('[data-affinity-period]')].map(e=>({at:Number(e.dataset.at),x:Number(e.getAttribute('transform').match(/translate\\(([^ ]+)/)[1])})).sort((a,b)=>a.at-b.at);
    const axis=[...document.querySelectorAll('[data-time-tick]')].map(e=>Number(e.dataset.timeTick));
    return {ordered:knots.every((v,i)=>!i||v.x>=knots[i-1].x),sameTime:knots.every((v,i)=>!i||v.at!==knots[i-1].at||v.x===knots[i-1].x),curves:[...document.querySelectorAll('.affinity-strand-path')].every(e=>e.getAttribute('d').includes(' C')),gaps:document.querySelectorAll('.affinity-strand-path.is-gap').length,axis:axis.length>1&&axis.every((v,i)=>!i||v>axis[i-1]),accounted:payload.nodes.every(n=>n.activity.reduce((s,a)=>s+a.occurrences,0)===n.occurrences)};
  })()`);
  assert(temporal.ordered && temporal.sameTime && temporal.curves && temporal.gaps > 0 && temporal.axis && temporal.accounted, 'Temporal geometry: '+JSON.stringify(temporal));
  await click('[data-affinity-period]'); await settled();
  assert(await evaluate("new URL(location.href).searchParams.has('period') && document.querySelector('.affinity-periods a[aria-current]').textContent.includes('근거')"), 'Activity knot opens period evidence');
  const periodUrl = await evaluate('location.href');
  await click('[data-map-action="lens"]');
  assert(await evaluate("document.querySelector('[data-map-zoom]').textContent==='300%'"), 'Selected moment lens');
  await capture('affinity-period-lens-1440');
  const centerTime = () => evaluate(`(() => {const s=history.state.affinity,v=s.viewport,t=s.transform;return (((v.left+v.right)/2-t.x)/t.k-v.left)/(v.right-v.left);})()`);
  const beforeResize = await centerTime();
  await evaluate("document.querySelector('[data-affinity-list]').open=true");
  await send('Emulation.setDeviceMetricsOverride', {width:700,height:1000,deviceScaleFactor:1,mobile:false});
  await wait("history.state.affinity.viewport.width===document.querySelector('[data-affinity-canvas]').clientWidth");
  assert(Math.abs(beforeResize - await centerTime()) < 0.001, 'Resize preserves temporal viewport');
  await send('Emulation.setDeviceMetricsOverride', {width:1440,height:1000,deviceScaleFactor:1,mobile:false});
  await wait("history.state.affinity.viewport.width===document.querySelector('[data-affinity-canvas]').clientWidth");
  assert(await evaluate("document.querySelector('[data-affinity-list]').open"), 'Resize preserves text-list disclosure');
  assert(await evaluate(`(() => {const node=[...document.querySelectorAll('[data-affinity-period]')].at(-1);node.focus({preventScroll:true});const p=node.querySelector('circle').getBoundingClientRect(),c=document.querySelector('[data-affinity-canvas]').getBoundingClientRect();return p.right>c.left&&p.left<c.right&&p.top>=c.top&&p.bottom<=c.bottom;})()`), 'Keyboard focus pans a clipped period into view');
  await click('.affinity-source');
  await wait("location.pathname.startsWith('/sessions/') && document.readyState==='complete'");
  await evaluate('history.back()');
  await wait(`location.href===${JSON.stringify(periodUrl)} && document.readyState==='complete' && document.querySelector('[data-affinity-root]')?.dataset.enhanced==='true'`);
  await settled();
  assert(await evaluate("document.querySelector('[data-map-zoom]').textContent==='300%'"), 'Period source-return camera');
  await navigate('/auto-work');
  const initialPositions = await evaluate("[...document.querySelectorAll('.affinity-strand-path')].map(e=>e.getAttribute('d'))");
  await click('[data-map-action="in"]');
  assert(await evaluate("document.querySelector('[data-map-zoom]').textContent==='250%'"), 'Zoom handler registration');
  await click('[data-affinity-map-node]:not([style*="display: none"])'); await settled();
  const selectedUrl = await evaluate('location.href');
  assert(await evaluate("document.querySelector('[data-map-zoom]').textContent==='250%'"), 'Selection transform retention');
  assert(JSON.stringify(initialPositions) === JSON.stringify(await evaluate("[...document.querySelectorAll('.affinity-strand-path')].map(e=>e.getAttribute('d'))")), 'Selection must not relayout');
  await click('[data-affinity-expand]'); await settled();
  assert(await evaluate("new URL(location.href).searchParams.has('group') && !new URL(location.href).searchParams.has('subgroup')"), 'Subgroup expansion');
  await click('[data-affinity-map-node]'); await settled();
  await click('[data-affinity-expand]'); await settled();
  assert(await evaluate("new URL(location.href).searchParams.has('subgroup')"), 'Session expansion');
  await click('[data-affinity-map-node]'); await settled();
  const sessionView = await evaluate('location.href');
  await click('.affinity-source');
  await wait("location.pathname.startsWith('/sessions/') && document.readyState==='complete'");
  await evaluate('history.back()');
  await wait(`location.href===${JSON.stringify(sessionView)} && Boolean(document.querySelector('[data-affinity-evidence]'))`);
  await navigate(new URL(selectedUrl).pathname + new URL(selectedUrl).search);
  const hrefs = await evaluate("[...document.querySelectorAll('[data-affinity-map-node]')].slice(1,4).map(e=>e.getAttribute('href'))");
  await evaluate("[...document.querySelectorAll('[data-affinity-map-node]')].slice(1,4).forEach(e=>e.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,button:0})))");
  await settled();
  assert(await evaluate(`location.search===new URL(${JSON.stringify(hrefs[2])},location.origin).search`), 'Rapid latest-selection ownership');
  const rapidUrl = await evaluate('location.href');
  await evaluate('history.back()'); await settled();
  await wait(`location.search===${JSON.stringify(new URL(selectedUrl).search)}`);
  await evaluate('history.forward()'); await settled(); await wait(`location.href===${JSON.stringify(rapidUrl)}`);
  await click('[data-map-action="reset"]');
  await evaluate("document.querySelector('[data-affinity-canvas]').focus({preventScroll:true})");
  await send('Input.dispatchKeyEvent', {type:'keyDown',key:'+',code:'Equal'});
  assert(await evaluate("document.querySelector('[data-map-zoom]').textContent==='250%'"), 'Keyboard zoom');
  await send('Input.dispatchKeyEvent', {type:'keyDown',key:'ArrowRight',code:'ArrowRight'});
  assert(await evaluate("history.state.affinity.transform.x!==0"), 'Keyboard pan');
  await click('[data-map-action="fit"]');
  assert(await evaluate("document.querySelector('[data-map-zoom]').textContent==='100%' && document.querySelector('[data-map-action=\"earlier\"]').disabled && document.querySelector('[data-map-action=\"later\"]').disabled"), 'Whole-time fit');
  await click('[data-map-action="reset"]');
  assert(await evaluate("document.querySelector('[data-map-zoom]').textContent==='200%'"), 'Reset inspection scale');
  const dragPoint = await evaluate("(() => {const e=document.querySelector('[data-affinity-canvas]');e.scrollIntoView({block:'center'});const r=e.getBoundingClientRect();return {x:r.x+8,y:r.y+20};})()");
  await send('Input.dispatchMouseEvent', {type:'mousePressed',button:'left',clickCount:1,...dragPoint});
  await send('Input.dispatchMouseEvent', {type:'mouseMoved',button:'left',buttons:1,x:dragPoint.x-60,y:dragPoint.y-25});
  await send('Input.dispatchMouseEvent', {type:'mouseReleased',button:'left',clickCount:1,x:dragPoint.x-60,y:dragPoint.y-25});
  assert(await evaluate("history.state.affinity.transform.x!==0 && !document.querySelector('.is-dragging')"), 'Pointer pan');
  await click('[data-map-action="reset"]');
  await click('[data-map-all-edges]');
  assert(await evaluate("document.querySelectorAll('.affinity-edge').length===JSON.parse(document.querySelector('[data-affinity-graph]').textContent).edges.length"), 'All whole-scope edges');
  const wheel = await evaluate(`(() => {const e=document.querySelector('[data-affinity-canvas]');return {ordinary:e.dispatchEvent(new WheelEvent('wheel',{deltaY:20,cancelable:true,bubbles:true})),modified:e.dispatchEvent(new WheelEvent('wheel',{deltaY:-20,ctrlKey:true,cancelable:true,bubbles:true,clientX:500,clientY:600}))};})()`);
  assert(wheel.ordinary && !wheel.modified, 'Wheel input ownership');
  await click('[data-map-action="reset"]');
  const scrollPoint = await evaluate("(() => {const c=document.querySelector('[data-affinity-canvas]');c.scrollIntoView({block:'center'});const r=c.getBoundingClientRect();return {x:r.x+r.width*0.7,y:r.y+r.height/2};})()");
  await send('Input.dispatchMouseEvent', {type:'mouseWheel',deltaX:140,deltaY:0,...scrollPoint});
  await wait("document.querySelector('[data-affinity-canvas]').scrollLeft>100");
  assert(await evaluate("history.state.affinity.transform.k===2 && history.state.affinity.transform.x < -history.state.affinity.viewport.left - 100"), 'Native horizontal trackpad pans time without zoom');
  await send('Input.dispatchMouseEvent', {type:'mouseWheel',deltaX:0,deltaY:220,...scrollPoint});
  await wait("document.querySelector('[data-affinity-canvas]').scrollTop>180");
  assert(await evaluate("(() => {const c=document.querySelector('[data-affinity-canvas]').getBoundingClientRect(),s=document.querySelector('.affinity-canvas svg').getBoundingClientRect();return Math.abs(c.left-s.left)<1&&Math.abs(c.top-s.top)<1;})()"), 'Native vertical scrolling retains viewport axis');
  const beforeArrow = await evaluate("history.state.affinity.transform.x");
  await click('[data-map-action="later"]');
  assert(await evaluate("history.state.affinity.transform.x") < beforeArrow, 'Visible later-time control');
  await click('[data-map-action="earlier"]');
  // Page three used to lose off-page connections. Now only the native text
  // slice changes, never map geometry, edge membership or user-owned camera.
  const mapState = () => evaluate("JSON.stringify({camera:history.state.affinity.transform,scope:history.state.affinity.scope,ids:[...document.querySelectorAll('[data-affinity-map-node]')].map(n=>n.dataset.affinityMapNode),paths:[...document.querySelectorAll('.affinity-strand-path')].map(n=>n.getAttribute('d')),edges:JSON.parse(document.querySelector('[data-affinity-graph]').textContent).edges})");
  await evaluate("document.querySelector('[data-affinity-list]').open=true");
  const beforePaging = await mapState();
  await click('[data-affinity-next]'); await settled();
  assert(await evaluate("new URL(location.href).searchParams.get('page')==='2' && document.querySelector('[data-affinity-list]').open"), 'Text page two stays open');
  assert(await mapState() === beforePaging, 'List page two cannot partition or move map');
  await click('[data-affinity-next]'); await settled();
  assert(await evaluate("new URL(location.href).searchParams.get('page')==='3' && document.querySelector('[data-affinity-list]').open"), 'Text page three stays open');
  assert(await mapState() === beforePaging, 'List page three cannot partition or move map');
  assert(await evaluate("(() => {const ids=new Set([...document.querySelectorAll('[data-affinity-node]')].map(n=>n.dataset.affinityNode));return JSON.parse(document.querySelector('[data-affinity-graph]').textContent).edges.some(e=>ids.has(e.left)!==ids.has(e.right));})()"), 'Cross-page affinity remains available on page three');
  await capture('affinity-list-page-three');
  await evaluate('history.back()'); await wait("new URL(location.href).searchParams.get('page')==='2'"); await settled();
  assert(await mapState() === beforePaging, 'List history retains camera');
  await navigate('/auto-work?inventory=all');
  assert(await evaluate("document.body.textContent.includes('제외 · 유지관리') || document.body.textContent.includes('분석 대상')"), 'Inventory fallback');
  await navigate('/auto-work?q=mixed-English');
  assert(await evaluate("document.querySelectorAll('[data-affinity-map-node]').length>0"), 'Long-label search over complete level');
  assert(await evaluate("document.querySelectorAll('[data-time-tick]').length>1 && document.querySelector('[data-map-zoom]').textContent==='200%'"), 'Sparse neighborhood retains the shared time domain');
  await click('[data-affinity-map-node]'); await settled();
  await send('Emulation.setDeviceMetricsOverride', {width:320,height:1000,deviceScaleFactor:1,mobile:false});
  assert(await evaluate("document.documentElement.scrollWidth<=document.documentElement.clientWidth"), 'Long mixed-label overflow');
  await evaluate("[...document.querySelectorAll('.affinity-source')].find(e=>e.textContent.includes('mixed-English'))?.scrollIntoView({block:'center'})");
  await capture('affinity-long-label-320');
  await navigate('/auto-work?snapshot=obsolete');
  assert(await evaluate("document.querySelector('[data-affinity-root]').dataset.state==='selection-stale'"), 'Obsolete snapshot');
  await send('Emulation.setEmulatedMedia', {features:[{name:'prefers-reduced-motion',value:'reduce'}]});
  await navigate('/auto-work');
  assert(await evaluate("matchMedia('(prefers-reduced-motion: reduce)').matches"), 'Reduced motion');
  // Force a real client-render failure before enhancement; SSR stays operable.
  const injected = await send('Page.addScriptToEvaluateOnNewDocument', {source:"const originalCreate=document.createElementNS.bind(document);document.createElementNS=(ns,name,...rest)=>{if(ns==='http://www.w3.org/2000/svg')throw Error('Synthetic render failure');return originalCreate(ns,name,...rest);};"});
  await navigate('/auto-work');
  assert(await evaluate("document.querySelector('[data-affinity-root]').dataset.enhanced==='failed' && document.querySelector('[data-affinity-list]').open && !document.querySelector('[data-affinity-render-status]').hidden"), 'Render failure fallback');
  await click('[data-affinity-node]'); await settled();
  assert(await evaluate("Boolean(document.querySelector('[data-affinity-evidence]'))"), 'Failure source path');
  await send('Page.removeScriptToEvaluateOnNewDocument', {identifier:injected.identifier});
  await send('Emulation.setScriptExecutionDisabled', {value:true});
  await navigate('/auto-work');
  assert(await evaluate("document.querySelector('[data-affinity-list]').open"), 'No-script list');
  await click('[data-affinity-node]'); await wait("Boolean(document.querySelector('[data-affinity-expand]'))");
  await click('[data-affinity-expand]'); await wait("new URL(location.href).searchParams.has('group') && document.readyState==='complete'");
  await click('[data-affinity-node]'); await wait("Boolean(document.querySelector('[data-affinity-evidence]'))");
  assert(writes===0 && exceptions.length===0, 'Unexpected write or runtime exception');
  console.log(JSON.stringify({result:'PASS',viewports,temporal,periodEvidence:true,momentLens:true,stableSelection:true,threeScales:true,exactSourceReturn:true,rapidSelection:true,history:true,keyboard:true,pointerPan:true,wheelOwnership:true,fitReset:true,paging:true,longLabels:true,allEdges:true,noScript:true,renderFailure:true,reducedMotion:true,mutationRequests:writes}));
} finally {
  socket?.close();
  const stopped = new Promise(resolve => browser.once('exit',resolve)); browser.kill('SIGTERM');
  await Promise.race([stopped,delay(3000)]);
  if (browser.exitCode===null && browser.signalCode===null) {browser.kill('SIGKILL');await stopped;}
  await rm(profile,{recursive:true,force:true});
}
