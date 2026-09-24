// Synthetic Auto Work fixture only. Output and Chrome profile are task-owned.
import {spawn} from 'node:child_process';
import {mkdir, rm, writeFile} from 'node:fs/promises';
import {join} from 'node:path';

const [base, output] = process.argv.slice(2);
if (!base || !output || !['127.0.0.1', 'localhost'].includes(new URL(base).hostname)) {
  throw new Error('Explicit local synthetic URL and task-owned output directory required');
}
await mkdir(output, {recursive: true});
const profile = join(output, 'chrome-profile');
const port = 9800 + process.pid % 100;
const browser = spawn(process.env.LOCALBRAIN_CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', [
  '--headless=new', '--disable-gpu', '--disable-background-networking', '--disable-component-update',
  '--no-first-run', '--no-default-browser-check', `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`, 'about:blank',
], {stdio: 'ignore'});
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const assert = (condition, message) => { if (!condition) throw new Error(message); };
let socket;
try {
  let target;
  for (let i = 0; i < 100 && !target; i++) {
    try { target = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, {method: 'PUT'})).json(); }
    catch { await delay(100); }
  }
  assert(target, 'Browser unavailable');
  socket = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => { socket.addEventListener('open', resolve, {once: true}); socket.addEventListener('error', reject, {once: true}); });
  let sequence = 0;
  const pending = new Map();
  socket.addEventListener('message', event => {
    const value = JSON.parse(event.data);
    if (!value.id) return;
    const waiter = pending.get(value.id);
    if (!waiter) return;
    pending.delete(value.id);
    clearTimeout(waiter.timer);
    if (value.error) waiter.reject(new Error('CDP command failed'));
    else waiter.resolve(value.result);
  });
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const id = ++sequence;
    pending.set(id, {resolve, reject, timer: setTimeout(() => reject(new Error('CDP timeout')), 15000)});
    socket.send(JSON.stringify({id, method, params}));
  });
  const evaluate = async expression => {
    const value = await send('Runtime.evaluate', {expression, returnByValue: true, awaitPromise: true});
    assert(!value.exceptionDetails, 'Page evaluation failed');
    return value.result.value;
  };
  const wait = async expression => {
    for (let i = 0; i < 150; i++) {
      if (await evaluate(expression)) return;
      await delay(100);
    }
    throw new Error('Expected page state unavailable');
  };
  const navigate = async path => {
    await send('Page.navigate', {url: base + path});
    await wait(`location.pathname === ${JSON.stringify(path.split('?')[0])} && document.readyState === 'complete'`);
  };
  const click = async selector => {
    const point = await evaluate(`(() => {const e=document.querySelector(${JSON.stringify(selector)});if(!e)return null;e.scrollIntoView({block:'center',inline:'nearest'});const r=e.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})()`);
    assert(point, 'Click target missing');
    await send('Input.dispatchMouseEvent', {type: 'mousePressed', button: 'left', clickCount: 1, ...point});
    await send('Input.dispatchMouseEvent', {type: 'mouseReleased', button: 'left', clickCount: 1, ...point});
    await delay(350);
    await wait("document.readyState === 'complete'");
  };
  const capture = async name => {
    const shot = await send('Page.captureScreenshot', {format: 'png', captureBeyondViewport: false});
    await writeFile(join(output, `${name}.png`), Buffer.from(shot.data, 'base64'));
  };
  await send('Page.enable'); await send('Runtime.enable'); await send('Network.enable');
  await send('Network.setCacheDisabled', {cacheDisabled: true});
  await navigate('/auto-work?mode=sample');
  assert(await evaluate("document.body.textContent.includes('long-subject-') && document.body.textContent.includes('품질 미평가')"), 'Synthetic fixture required');
  const evidence = [];
  for (const width of [1440, 920, 700, 320]) {
    await send('Emulation.setDeviceMetricsOverride', {width, height: 1000, deviceScaleFactor: 1, mobile: false});
    await navigate('/auto-work?mode=sample');
    const state = await evaluate(`(() => {const nav=[...document.querySelectorAll('.lnb-item')];const active=document.querySelector('.lnb-item[aria-current]');return {width:innerWidth,overflow:document.documentElement.scrollWidth>document.documentElement.clientWidth,position:nav.indexOf(active)+1===nav.findIndex(e=>e.getAttribute('href')==='/workstreams'),refreshHeight:document.querySelector('[data-auto-work-refresh-button]').getBoundingClientRect().height,groups:document.querySelectorAll('[data-auto-work-group]').length,columns:getComputedStyle(document.querySelector('.auto-work-layout')).gridTemplateColumns.split(' ').length};})()`);
    assert(state.width === width && !state.overflow && state.position && state.groups === 12, 'Viewport or sidebar contract failed');
    assert(state.columns === (width > 920 ? 2 : 1), 'Responsive composition failed');
    assert(state.refreshHeight >= (width <= 700 ? 40 : 32), 'Control geometry failed');
    evidence.push(state);
    await capture(`auto-work-${width}`);
  }
  await send('Emulation.setDeviceMetricsOverride', {width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false});
  await navigate('/workstreams');
  await click('.lnb-item[href="/auto-work"]');
  assert(await evaluate("location.pathname === '/auto-work'"), 'Sidebar click failed');
  await click('.affinity-tabs a[href="/auto-work?mode=sample"]');
  await click('[data-auto-work-group]:nth-child(2)');
  const selectedUrl = await evaluate('location.href');
  assert(await evaluate("location.hash==='#auto-work-detail' && document.querySelector('[data-auto-work-group][aria-current]')!==null"), 'Selection failed');
  await click('[data-auto-work-evidence] a');
  assert(await evaluate("location.pathname.startsWith('/sessions/') && Boolean(document.querySelector('.session-heading'))"), 'Source reading failed');
  await evaluate('history.back()');
  await wait(`location.href === ${JSON.stringify(selectedUrl)} && document.querySelector('[data-auto-work]') !== null`);
  await click('[data-auto-work-next]');
  assert(await evaluate("new URL(location.href).searchParams.get('page')==='2' && document.querySelectorAll('[data-auto-work-group]').length===6"), 'Pagination failed');
  await click('[data-auto-work-unassigned]');
  assert(await evaluate("document.querySelector('.auto-work-detail h2').textContent.includes('연결하지 못한') && !document.querySelector('.auto-work-evidence script')"), 'Unassigned/XSS contract failed');
  await evaluate("document.querySelector('[data-auto-work-refresh-button]').focus()");
  await send('Input.dispatchKeyEvent', {type: 'keyDown', key: 'Tab', code: 'Tab', windowsVirtualKeyCode: 9});
  await send('Input.dispatchKeyEvent', {type: 'keyUp', key: 'Tab', code: 'Tab', windowsVirtualKeyCode: 9});
  assert(await evaluate("document.activeElement.tagName==='A' && getComputedStyle(document.activeElement).outlineStyle!=='none'"), 'Keyboard focus failed');
  await click('[data-auto-work-refresh-button]');
  await wait("new URL(location.href).searchParams.get('notice')==='updated' && document.readyState==='complete'");
  assert(await evaluate("!document.querySelector('[data-auto-work-refresh-button]').disabled"), 'Refresh reset failed');
  await send('Emulation.setEmulatedMedia', {features:[{name:'prefers-reduced-motion',value:'reduce'}]});
  await navigate('/auto-work?mode=sample');
  assert(await evaluate("matchMedia('(prefers-reduced-motion: reduce)').matches"), 'Reduced-motion emulation failed');
  await send('Emulation.setScriptExecutionDisabled', {value: true});
  await navigate('/auto-work?mode=sample');
  await click('[data-auto-work-group]:nth-child(2)');
  assert(await evaluate("Boolean(document.querySelector('[data-auto-work-evidence]'))"), 'No-script selection failed');
  await click('[data-auto-work-refresh-button]');
  await wait("new URL(location.href).searchParams.get('notice')==='updated' && document.readyState==='complete'");
  console.log(JSON.stringify({result: 'PASS', viewports: evidence, sourceNavigation: true, history: true, pagination: true,
    unassigned: true, keyboard: true, refresh: true, noScript: true, reducedMotion: true}));
} finally {
  socket?.close();
  const stopped = new Promise(resolve => browser.once('exit', resolve));
  browser.kill('SIGTERM');
  await Promise.race([stopped, delay(3000)]);
  if (browser.exitCode === null && browser.signalCode === null) { browser.kill('SIGKILL'); await stopped; }
  await rm(profile, {recursive: true, force: true});
}
