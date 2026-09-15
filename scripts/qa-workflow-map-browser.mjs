import { spawn } from "node:child_process";
import { mkdir, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";


const baseUrl = process.argv[2] || "http://127.0.0.1:8000";
const outputDir = process.argv[3] || join(tmpdir(), "localbrain-workflow-browser-qa");
const selectedSessionId = process.argv[4] || "11";
const chromePath = process.env.LOCALBRAIN_CHROME_PATH
  || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const port = 9800 + (process.pid % 100);
const profile = join(tmpdir(), `localbrain-workflow-qa-profile-${process.pid}`);

await mkdir(outputDir, { recursive: true });

const chrome = spawn(chromePath, [
  "--headless=new",
  "--disable-gpu",
  "--disable-background-networking",
  "--disable-component-update",
  "--no-first-run",
  "--no-default-browser-check",
  `--remote-debugging-port=${port}`,
  `--user-data-dir=${profile}`,
  "about:blank",
], { stdio: ["ignore", "ignore", "pipe"] });

let chromeErrors = "";
chrome.stderr.on("data", (chunk) => {
  chromeErrors = (chromeErrors + chunk.toString()).slice(-12000);
});

const delay = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

async function waitForJson(path, attempts = 100) {
  let lastError;
  for (let attempt = 0; attempt < attempts; attempt += 1) {
    try {
      const response = await fetch(`http://127.0.0.1:${port}${path}`, {
        method: path.startsWith("/json/new") ? "PUT" : "GET",
      });
      if (response.ok) return await response.json();
    } catch (error) {
      lastError = error;
    }
    await delay(100);
  }
  throw new Error(`Chrome debugging endpoint unavailable: ${lastError || path}`);
}

class CdpSession {
  constructor(url) {
    this.socket = new WebSocket(url);
    this.sequence = 0;
    this.pending = new Map();
    this.waiters = new Map();
  }

  async open() {
    await new Promise((resolve, reject) => {
      this.socket.addEventListener("open", resolve, { once: true });
      this.socket.addEventListener("error", reject, { once: true });
    });
    this.socket.addEventListener("message", (event) => {
      const message = JSON.parse(event.data);
      if (message.id) {
        const pending = this.pending.get(message.id);
        if (!pending) return;
        this.pending.delete(message.id);
        if (message.error) pending.reject(new Error(message.error.message));
        else pending.resolve(message.result || {});
        return;
      }
      const waiters = this.waiters.get(message.method) || [];
      this.waiters.delete(message.method);
      waiters.forEach((resolve) => resolve(message.params || {}));
    });
  }

  send(method, params = {}) {
    this.sequence += 1;
    const id = this.sequence;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.socket.send(JSON.stringify({ id, method, params }));
    });
  }

  event(method, timeout = 10000) {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error(`Timed out waiting for ${method}`)), timeout);
      const waiters = this.waiters.get(method) || [];
      waiters.push((value) => {
        clearTimeout(timer);
        resolve(value);
      });
      this.waiters.set(method, waiters);
    });
  }

  close() {
    this.socket.close();
  }
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

async function main() {
  const target = await waitForJson(`/json/new?${encodeURIComponent("about:blank")}`);
  const cdp = new CdpSession(target.webSocketDebuggerUrl);
  await cdp.open();
  await Promise.all([
    cdp.send("Page.enable"),
    cdp.send("Runtime.enable"),
    cdp.send("Network.enable"),
  ]);
  await cdp.send("Network.setCacheDisabled", { cacheDisabled: true });

  const evaluate = async (expression) => {
    const result = await cdp.send("Runtime.evaluate", {
      expression,
      awaitPromise: true,
      returnByValue: true,
    });
    if (result.exceptionDetails) {
      throw new Error(result.exceptionDetails.exception?.description || result.exceptionDetails.text);
    }
    return result.result.value;
  };

  const waitFor = async (expression, message, attempts = 120) => {
    for (let attempt = 0; attempt < attempts; attempt += 1) {
      if (await evaluate(`Boolean(${expression})`)) return;
      await delay(100);
    }
    throw new Error(message);
  };

  const setViewport = (width, height = 1000) => cdp.send(
    "Emulation.setDeviceMetricsOverride",
    { width, height, deviceScaleFactor: 1, mobile: width <= 320 },
  );

  const navigate = async (path, { ready = true } = {}) => {
    const loaded = cdp.event("Page.loadEventFired");
    await cdp.send("Page.navigate", { url: `${baseUrl}${path}` });
    await loaded;
    await waitFor(
      "document.querySelector('[data-workflow-map]')",
      `Workflow page missing: ${path}`,
    );
    if (ready) {
      await waitFor(
        "document.querySelector('[data-workflow-render-state=\"ready\"]')",
        `Workflow renderer did not become ready: ${path}`,
      );
    }
  };

  const state = () => evaluate(`(() => {
    const root = document.querySelector('[data-workflow-map]');
    const viewport = document.querySelector('[data-workflow-viewport]');
    const selected = document.querySelector('[data-workflow-episode-card].is-selected')
      ?.closest('[data-episode-key]');
    const trace = document.querySelector('[data-workflow-episode-trace]:not([hidden])');
    const fallback = document.querySelector('[data-workflow-fallback]');
    return {
      href: location.href,
      innerWidth,
      clientWidth: document.documentElement.clientWidth,
      documentWidth: document.documentElement.scrollWidth,
      renderState: document.querySelector('.workflow-map-panel')?.dataset.workflowRenderState || null,
      orientation: document.querySelector('[data-workflow-stage]')?.dataset.orientation || null,
      mapDisplay: viewport ? getComputedStyle(viewport).display : null,
      fallbackOpen: fallback?.open || false,
      episodeCount: document.querySelectorAll('[data-workflow-episode-position]').length,
      visibleEpisodeCount: [...document.querySelectorAll('[data-workflow-episode-position]')]
        .filter((item) => !item.hidden).length,
      relationCount: document.querySelectorAll('[data-workflow-relation]').length,
      visibleRelationCount: [...document.querySelectorAll('[data-workflow-relation]')]
        .filter((item) => !item.hidden).length,
      selectedKey: selected?.dataset.episodeKey || null,
      selectedTransform: selected?.style.transform || null,
      selectedText: trace?.querySelector('h3')?.textContent.trim() || null,
      selectedLabel: selected?.querySelector('[data-workflow-selected-label]')?.textContent.trim() || null,
      scale: document.querySelector('[data-workflow-zoom-reset]')?.textContent.trim() || null,
      zoomDisabled: document.querySelector('[data-workflow-zoom-in]')?.disabled ?? null,
      branchToggleVisible: Boolean(document.querySelector('[data-workflow-branch-toggle]:not([hidden])')),
      relationTraceVisible: Boolean(document.querySelector('[data-workflow-relation-trace]:not([hidden])')),
      viewportScrolls: viewport
        ? viewport.scrollWidth > viewport.clientWidth || viewport.scrollHeight > viewport.clientHeight
        : false,
      shellPresent: Boolean(document.querySelector('.lnb') && document.querySelector('.workspace-header')),
      conversationPresent: Boolean(document.querySelector('.timeline-section')),
      userConfirmedEdges: document.querySelectorAll('[data-workflow-relation][data-workflow-authority="user-confirmed"]').length,
      userConfirmedEpisodes: document.querySelectorAll('[data-workflow-episode-card][data-workflow-authority="user-confirmed"]').length,
      correctionFeedback: document.querySelector('[data-workflow-correction-feedback]:not([hidden])')?.textContent.trim() || null,
      activeElement: document.activeElement?.matches('[data-workflow-assertion-summary]')
        ? 'assertion'
        : document.activeElement?.tagName || null,
    };
  })()`);

  const capture = async (name, { fullPage = false } = {}) => {
    const result = await cdp.send("Page.captureScreenshot", {
      format: "png",
      captureBeyondViewport: fullPage,
      fromSurface: true,
    });
    await writeFile(join(outputDir, `${name}.png`), Buffer.from(result.data, "base64"));
  };

  await setViewport(1440);
  const detailLoaded = cdp.event("Page.loadEventFired");
  await cdp.send("Page.navigate", { url: `${baseUrl}/sessions/${selectedSessionId}` });
  await detailLoaded;
  await waitFor("document.querySelector('.session-heading')", "Session reference screen missing");
  const detailState = await state();
  assert(detailState.shellPresent, "Session reference lost the shared shell");
  assert(detailState.conversationPresent, "Session reference lost conversation reading");
  assert(
    await evaluate("Boolean(document.querySelector('.session-workflow-link'))"),
    "Eligible Session has no Workflow entry",
  );
  await capture("session-reference-1440", { fullPage: true });

  const viewports = [1440, 920, 700, 320];
  const viewportEvidence = [];
  for (const width of viewports) {
    await setViewport(width);
    await navigate(`/sessions/${selectedSessionId}/workflow`);
    const current = await state();
    assert(current.innerWidth === width, `Viewport mismatch at ${width}`);
    assert(current.documentWidth <= current.clientWidth, `Document overflow at ${width}`);
    assert(current.shellPresent, `Shared shell missing at ${width}`);
    assert(current.episodeCount === 4, `Episode count changed at ${width}`);
    assert(current.relationCount === 3, `Relation count changed at ${width}`);
    assert(current.selectedText === "Current implementation", `Initial Trace mismatch at ${width}`);
    assert(current.selectedLabel === "선택됨", `Selection text missing at ${width}`);
    if (width > 920) {
      assert(current.orientation === "wide", "Wide time direction missing");
      assert(current.mapDisplay !== "none", "Wide map is hidden");
      assert(!current.zoomDisabled, "Wide zoom controls stayed disabled");
    } else if (width > 700) {
      assert(current.orientation === "compact", "Compact vertical layout missing");
      assert(current.mapDisplay !== "none", "Compact map is hidden");
    } else {
      assert(current.mapDisplay === "none", `Narrow graph should yield at ${width}`);
      assert(current.fallbackOpen, `Narrow textual lineage is closed at ${width}`);
      assert(current.zoomDisabled, `Hidden narrow zoom controls are enabled at ${width}`);
    }
    viewportEvidence.push(current);
    await capture(`workflow-${width}`, { fullPage: true });
  }

  await setViewport(1440);
  await navigate(`/sessions/${selectedSessionId}/workflow`);
  let interaction = await state();
  assert(interaction.visibleEpisodeCount === 3, "Non-selected side branch was not bounded");
  assert(interaction.branchToggleVisible, "Bounded branch disclosure is missing");
  await evaluate("document.querySelector('[data-workflow-branch-toggle]:not([hidden])').click()");
  await waitFor(
    "[...document.querySelectorAll('[data-workflow-episode-position]')].filter((item) => !item.hidden).length === 4",
    "Branch disclosure did not reveal its retained Episode",
  );
  const expanded = await state();

  const beforeTransform = await evaluate("document.querySelector('[data-episode-key]')?.style.transform");
  await evaluate(`document.querySelector('[data-workflow-destination="/sessions/10/workflow"]').click()`);
  await waitFor(
    "location.pathname === '/sessions/10/workflow' && document.querySelector('[data-workflow-episode-trace]:not([hidden]) h3')?.textContent.trim() === 'First intent'",
    "Episode selection did not update focus, Trace, and canonical history",
  );
  interaction = await state();
  assert(interaction.selectedTransform === beforeTransform, "Episode selection relocated the focused node");

  await evaluate("history.back()");
  await waitFor(
    `location.pathname === '/sessions/${selectedSessionId}/workflow' && document.querySelector('[data-workflow-episode-trace]:not([hidden]) h3')?.textContent.trim() === 'Current implementation'`,
    "Back did not restore Workflow focus",
  );
  const back = await state();
  await evaluate("history.forward()");
  await waitFor(
    "location.pathname === '/sessions/10/workflow' && document.querySelector('[data-workflow-episode-trace]:not([hidden]) h3')?.textContent.trim() === 'First intent'",
    "Forward did not restore Workflow focus",
  );
  const forward = await state();

  await evaluate(`(() => {
    const edge = document.querySelector('[data-workflow-relation]:not([hidden])');
    edge.focus();
    edge.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, cancelable: true }));
  })()`);
  await waitFor(
    "document.querySelector('[data-workflow-relation-trace]:not([hidden])')",
    "Edge inspection did not open Relation Trace",
  );
  const relation = await state();
  assert(relation.relationTraceVisible, "Relation Trace did not remain visible");
  const reasonCount = await evaluate("document.querySelectorAll('[data-workflow-relation-trace]:not([hidden]) .workflow-reason-list li').length");
  assert(reasonCount > 0, "Relation Trace omitted its complete reason list");
  await evaluate("document.querySelector('[data-workflow-trace-return]').click()");

  await evaluate("document.querySelector('[data-workflow-zoom-in]').click()");
  await waitFor(
    "document.querySelector('[data-workflow-zoom-reset]').textContent.trim() !== '100%'",
    "Zoom control did not change scale",
  );
  const zoomed = await state();
  const ordinaryWheelOwned = await evaluate(`(() => {
    const viewport = document.querySelector('[data-workflow-viewport]');
    return !viewport.dispatchEvent(new WheelEvent('wheel', { deltaY: 20, cancelable: true }));
  })()`);
  const modifierWheelOwned = await evaluate(`(() => {
    const viewport = document.querySelector('[data-workflow-viewport]');
    return !viewport.dispatchEvent(new WheelEvent('wheel', { deltaY: 20, ctrlKey: true, cancelable: true }));
  })()`);
  assert(!ordinaryWheelOwned, "Ordinary wheel was incorrectly captured");
  assert(modifierWheelOwned, "Modifier wheel was not captured for zoom");
  await evaluate("document.querySelector('[data-workflow-zoom-reset]').click()");
  await waitFor(
    "document.querySelector('[data-workflow-zoom-reset]').textContent.trim() === '100%'",
    "Zoom reset did not restore 100%",
  );

  await evaluate("document.querySelector('.workflow-session-destination').click()");
  await waitFor("location.pathname === '/sessions/10'", "Session evidence destination did not open");
  assert(
    await evaluate("Boolean(document.querySelector('.timeline-section'))"),
    "Session destination lost conversation reading",
  );
  await evaluate("history.back()");
  await waitFor(
    "location.pathname === '/sessions/10/workflow' && document.querySelector('[data-workflow-map]')",
    "Browser return did not restore the focused Workflow route",
  );
  const sourceReturn = await state();

  await setViewport(1440);
  await navigate(`/sessions/${selectedSessionId}/workflow`);
  await evaluate(`(() => {
    const toggle = document.querySelector('[data-workflow-branch-toggle]:not([hidden])');
    if (toggle && toggle.getAttribute('aria-expanded') !== 'true') toggle.click();
    document.querySelector('[data-workflow-zoom-in]').click();
    const evidence = document.querySelector('[data-workflow-episode-trace]:not([hidden]) [data-workflow-disclosure-key]');
    if (evidence) evidence.open = true;
  })()`);
  await waitFor(
    "document.querySelector('[data-workflow-zoom-reset]').textContent.trim() !== '100%'",
    "Correction setup did not retain a non-default zoom",
  );
  const correctionRelationId = await evaluate(`(() => {
    const panel = [...document.querySelectorAll('[data-workflow-relation-trace]')]
      .find((item) => item.querySelector('code')?.textContent.trim() === 'continues');
    return panel?.dataset.workflowRelationTrace || null;
  })()`);
  assert(correctionRelationId, "No continuation boundary was available for correction");
  await evaluate(`(() => {
    const edge = document.querySelector(
      '[data-workflow-relation][data-relation-id="${correctionRelationId}"]',
    );
    edge.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    const panel = document.querySelector(
      '[data-workflow-relation-trace="${correctionRelationId}"]',
    );
    const form = panel.querySelector('input[name="action"][value="merge-into"]').form;
    form.closest('[data-workflow-correction-action]').open = true;
    const viewport = document.querySelector('[data-workflow-viewport]');
    viewport.scrollLeft = Math.min(140, Math.max(0, viewport.scrollWidth - viewport.clientWidth));
    viewport.scrollTop = Math.min(90, Math.max(0, viewport.scrollHeight - viewport.clientHeight));
    const trace = document.querySelector('.workflow-trace-scroll');
    trace.scrollTop = Math.min(110, Math.max(0, trace.scrollHeight - trace.clientHeight));
    window.scrollTo(0, Math.min(80, document.documentElement.scrollHeight - innerHeight));
  })()`);
  const correctionBefore = await evaluate(`(() => {
    const viewport = document.querySelector('[data-workflow-viewport]');
    const trace = document.querySelector('.workflow-trace-scroll');
    return {
      href: location.href,
      historyLength: history.length,
      selectedKey: document.querySelector('[data-workflow-map]').dataset.selectedEpisodeKey,
      expanded: [...document.querySelectorAll('[data-workflow-branch-toggle][aria-expanded="true"]')]
        .map((item) => item.closest('[data-episode-key]').dataset.episodeKey),
      scale: document.querySelector('[data-workflow-zoom-reset]').textContent.trim(),
      viewportLeft: viewport.scrollLeft,
      viewportTop: viewport.scrollTop,
      viewportWidth: viewport.clientWidth,
      viewportScrollWidth: viewport.scrollWidth,
      traceTop: trace.scrollTop,
      outerY: scrollY,
      disclosures: [...document.querySelectorAll('[data-workflow-disclosure-key][open]')]
        .map((item) => item.dataset.workflowDisclosureKey),
    };
  })()`);
  const correctionLoaded = cdp.event("Page.loadEventFired");
  const correctionRequestEvent = cdp.event("Network.requestWillBeSent");
  const correctionResponseEvent = cdp.event("Network.responseReceived");
  await evaluate(`document.querySelector(
    '[data-workflow-relation-trace="${correctionRelationId}"] input[name="action"][value="merge-into"]',
  ).form.querySelector('button[type="submit"]').click()`);
  const correctionRequest = await correctionRequestEvent;
  const correctionNetwork = await correctionResponseEvent;
  assert(
    correctionNetwork.response.url.endsWith('/sessions/11/workflow/corrections'),
    `Unexpected correction response: ${correctionNetwork.response.url}`,
  );
  if (correctionNetwork.response.status !== 200) {
    const failedBody = await cdp.send("Network.getResponseBody", {
      requestId: correctionNetwork.requestId,
    });
    throw new Error(
      `Relation correction returned ${correctionNetwork.response.status}: ${failedBody.body}; request ${JSON.stringify({
        contentType: correctionRequest.request.headers['Content-Type'],
        bodyLength: correctionRequest.request.postData?.length || 0,
      })}`,
    );
  }
  await correctionLoaded;
  await waitFor(
    "document.querySelector('[data-workflow-render-state=\"ready\"]') && document.querySelector('[data-workflow-correction-feedback]:not([hidden])')",
    "Relation correction did not reload with feedback",
  );
  await waitFor(
    "document.querySelector('[data-workflow-map]')?.dataset.workflowRestorationState === 'complete'",
    "Relation correction restoration did not complete",
  );
  const correctionTimeline = [];
  let correctionElapsed = 0;
  for (const delayMs of [0, 16, 50, 100, 250, 500, 1000]) {
    if (delayMs) await delay(delayMs);
    correctionElapsed += delayMs;
    correctionTimeline.push(await evaluate(`(() => {
      const viewport = document.querySelector('[data-workflow-viewport]');
      return {
        afterMs: ${correctionElapsed},
        left: viewport.scrollLeft,
        top: viewport.scrollTop,
        trace: document.querySelector('.workflow-trace-scroll').scrollTop,
        outer: scrollY,
        active: document.activeElement?.tagName,
        activeAssertion: document.activeElement?.matches('[data-workflow-assertion-summary]') || false,
        scrollRestoration: history.scrollRestoration,
      };
    })()`));
  }
  const correctionAfter = await evaluate(`(() => {
    const viewport = document.querySelector('[data-workflow-viewport]');
    const trace = document.querySelector('.workflow-trace-scroll');
    const edge = document.querySelector(
      '[data-workflow-relation][data-relation-id="${correctionRelationId}"]',
    );
    const panel = document.querySelector(
      '[data-workflow-relation-trace="${correctionRelationId}"]',
    );
    return {
      href: location.href,
      historyLength: history.length,
      selectedKey: document.querySelector('[data-workflow-map]').dataset.selectedEpisodeKey,
      expanded: [...document.querySelectorAll('[data-workflow-branch-toggle][aria-expanded="true"]')]
        .map((item) => item.closest('[data-episode-key]').dataset.episodeKey),
      scale: document.querySelector('[data-workflow-zoom-reset]').textContent.trim(),
      viewportLeft: viewport.scrollLeft,
      viewportTop: viewport.scrollTop,
      viewportWidth: viewport.clientWidth,
      viewportScrollWidth: viewport.scrollWidth,
      traceTop: trace.scrollTop,
      outerY: scrollY,
      disclosures: [...document.querySelectorAll('[data-workflow-disclosure-key][open]')]
        .map((item) => item.dataset.workflowDisclosureKey),
      authority: edge?.dataset.workflowAuthority,
      relationKind: panel?.querySelector('.workflow-trace-facts code')?.textContent.trim(),
      originalReasons: panel?.querySelectorAll('.workflow-base-reasons li').length || 0,
      assertionFocus: document.activeElement?.matches('[data-workflow-assertion-summary]') || false,
      feedback: document.querySelector('[data-workflow-correction-feedback]')?.textContent.trim(),
      restoreConsumed: sessionStorage.getItem('localbrain.workflow-correction-restore') === null,
    };
  })()`);
  assert(correctionAfter.href === correctionBefore.href, "Correction changed the canonical URL");
  assert(correctionAfter.historyLength === correctionBefore.historyLength, "Correction added browser history");
  assert(correctionAfter.selectedKey === correctionBefore.selectedKey, "Correction lost selected Episode");
  assert(correctionAfter.scale === correctionBefore.scale, "Correction lost zoom");
  assert(correctionAfter.authority === "user-confirmed", "Corrected edge lacks user authority");
  assert(correctionAfter.relationKind === "merged-into", "Relation consequence was not projected");
  assert(correctionAfter.originalReasons > 0, "Correction hid original candidate reasons");
  assert(correctionAfter.assertionFocus, "Correction did not focus its assertion result");
  assert(correctionAfter.restoreConsumed, "One-shot restoration state was retained");
  assert(correctionAfter.feedback?.includes("사용자 확인"), "Correction feedback is missing");
  assert(
    correctionBefore.disclosures.every((key) => correctionAfter.disclosures.includes(key)),
    "Correction lost an evidence disclosure",
  );
  assert(
    correctionBefore.expanded.every((key) => correctionAfter.expanded.includes(key)),
    "Correction lost an unaffected branch disclosure",
  );
  assert(
    Math.abs(correctionAfter.viewportLeft - correctionBefore.viewportLeft) <= 2,
    `Correction lost map pan (${correctionBefore.viewportLeft} -> ${correctionAfter.viewportLeft}; widths ${correctionBefore.viewportWidth}/${correctionBefore.viewportScrollWidth} -> ${correctionAfter.viewportWidth}/${correctionAfter.viewportScrollWidth}; timeline ${JSON.stringify(correctionTimeline)})`,
  );
  assert(
    Math.abs(correctionAfter.viewportTop - correctionBefore.viewportTop) <= 2,
    `Correction lost map vertical pan (${correctionBefore.viewportTop} -> ${correctionAfter.viewportTop})`,
  );
  assert(
    Math.abs(correctionAfter.traceTop - correctionBefore.traceTop) <= 2,
    `Correction lost Trace scroll (${correctionBefore.traceTop} -> ${correctionAfter.traceTop})`,
  );
  assert(
    Math.abs(correctionAfter.outerY - correctionBefore.outerY) <= 2,
    `Correction lost page scroll (${correctionBefore.outerY} -> ${correctionAfter.outerY})`,
  );
  await capture("workflow-relation-corrected-1440", { fullPage: true });

  const tip = await evaluate(`(() => {
    const payload = JSON.parse(document.querySelector('[data-workflow-projection]').textContent);
    const sources = new Set(payload.relations.map((item) => item.source_episode_key));
    const episode = [...payload.episodes].reverse().find((item) => !sources.has(item.episode_key));
    return episode ? { key: episode.episode_key, destination: episode.workflow_destination } : null;
  })()`);
  assert(tip, "No current workflow tip was available");
  await evaluate(`document.querySelector(
    '[data-episode-key="${tip.key}"] [data-workflow-episode]',
  ).click()`);
  await waitFor(
    `location.pathname === '${tip.destination}' && document.querySelector('[data-workflow-episode-trace]:not([hidden]) input[name="action"][value="close"]')`,
    "Tip selection did not expose close",
  );
  const closeLoaded = cdp.event("Page.loadEventFired");
  await evaluate(`(() => {
    const form = document.querySelector(
      '[data-workflow-episode-trace]:not([hidden]) input[name="action"][value="close"]',
    ).form;
    form.closest('[data-workflow-correction-action]').open = true;
    form.querySelector('button[type="submit"]').click();
  })()`);
  await closeLoaded;
  await waitFor(
    "document.querySelector('[data-workflow-episode-card].is-selected')?.dataset.workflowLifecycle === 'closed'",
    "Close did not project a closed tip",
  );
  const closed = await state();
  assert(closed.userConfirmedEpisodes > 0, "Closed tip lacks a user-confirmed structure");
  assert(
    await evaluate("Boolean(document.querySelector('[data-workflow-episode-trace]:not([hidden]) input[name=\"action\"][value=\"reopen\"]'))"),
    "Closed tip does not expose reopen",
  );

  const reopenLoaded = cdp.event("Page.loadEventFired");
  await evaluate(`(() => {
    const form = document.querySelector(
      '[data-workflow-episode-trace]:not([hidden]) input[name="action"][value="reopen"]',
    ).form;
    form.closest('[data-workflow-correction-action]').open = true;
    form.querySelector('button[type="submit"]').click();
  })()`);
  await reopenLoaded;
  await waitFor(
    "document.querySelector('[data-workflow-episode-card].is-selected')?.dataset.workflowLifecycle === 'open'",
    "Reopen did not project an open tip",
  );
  const reopened = await state();

  const undoLoaded = cdp.event("Page.loadEventFired");
  await evaluate(`(() => {
    const form = document.querySelector(
      '[data-workflow-episode-trace]:not([hidden]) input[name="action"][value="undo"]',
    ).form;
    form.closest('[data-workflow-correction-action]').open = true;
    form.querySelector('button[type="submit"]').click();
  })()`);
  await undoLoaded;
  await waitFor(
    "document.querySelector('[data-workflow-episode-card].is-selected')?.dataset.workflowLifecycle === 'closed'",
    "Undo did not restore the prior closed boundary",
  );
  const undone = await state();

  const staleBefore = await state();
  await evaluate(`(() => {
    const form = document.querySelector(
      '[data-workflow-episode-trace]:not([hidden]) input[name="action"][value="close"]',
    ).form;
    form.closest('[data-workflow-correction-action]').open = true;
    form.querySelector('input[name="expected_revision"]').value = 'workflow-revision:' + '0'.repeat(64);
    form.querySelector('button[type="submit"]').click();
  })()`);
  await waitFor(
    "document.querySelector('[data-workflow-episode-trace]:not([hidden]) [data-workflow-correction-form-feedback]:not([hidden])')",
    "Stale correction did not expose in-place recovery",
  );
  const stale = await evaluate(`(() => {
    const form = document.querySelector(
      '[data-workflow-episode-trace]:not([hidden]) input[name="action"][value="close"]',
    ).form;
    return {
      href: location.href,
      selectedKey: document.querySelector('[data-workflow-map]').dataset.selectedEpisodeKey,
      lifecycle: document.querySelector('[data-workflow-episode-card].is-selected').dataset.workflowLifecycle,
      enabled: !form.querySelector('fieldset').disabled,
      feedback: form.querySelector('[data-workflow-correction-form-feedback]').textContent.trim(),
      reload: !form.querySelector('[data-workflow-correction-reload]').hidden,
    };
  })()`);
  assert(stale.href === staleBefore.href, "Stale failure reloaded the page");
  assert(stale.selectedKey === staleBefore.selectedKey, "Stale failure lost selection");
  assert(stale.lifecycle === "closed", "Stale failure changed the graph");
  assert(stale.enabled, "Stale failure left its form disabled");
  assert(stale.reload, "Stale failure omitted explicit reload recovery");
  assert(stale.feedback.includes("달라졌습니다"), "Stale failure copy is unclear");
  const cancel = await evaluate(`(() => {
    const form = document.querySelector(
      '[data-workflow-episode-trace]:not([hidden]) input[name="action"][value="close"]',
    ).form;
    const details = form.closest('[data-workflow-correction-action]');
    details.open = true;
    form.querySelector('[data-workflow-correction-cancel]').click();
    return { open: details.open, focus: document.activeElement === details.querySelector('summary') };
  })()`);
  assert(!cancel.open && cancel.focus, "Cancel did not close and return focus to its preview");

  const renderFailure = await evaluate(`(async () => {
    const original = document.querySelector('[data-workflow-map]');
    const clone = original.cloneNode(true);
    clone.querySelector('[data-workflow-projection]').textContent = '{malformed';
    document.body.append(clone);
    const moduleUrl = document.querySelector('script[src*="workflow-map.js"]').src;
    const controller = await import(moduleUrl);
    controller.setupWorkflowMap(clone);
    const result = {
      state: clone.querySelector('.workflow-map-panel').dataset.workflowRenderState,
      fallbackOpen: clone.querySelector('[data-workflow-fallback]').open,
      controlsDisabled: [...clone.querySelectorAll('[data-workflow-zoom-controls] button')]
        .every((button) => button.disabled),
      sessionDestination: Boolean(clone.querySelector('.workflow-session-destination')),
    };
    clone.remove();
    return result;
  })()`);
  assert(renderFailure.state === "unavailable", "Malformed renderer did not expose failure state");
  assert(renderFailure.fallbackOpen, "Renderer failure did not open textual lineage");
  assert(renderFailure.controlsDisabled, "Renderer failure left inert controls enabled");
  assert(renderFailure.sessionDestination, "Renderer failure lost Session navigation");

  await cdp.send("Emulation.setScriptExecutionDisabled", { value: true });
  await navigate(`${tip.destination}?qa=no-script`, { ready: false });
  const noScript = await state();
  assert(noScript.fallbackOpen, "No-script textual lineage is closed");
  assert(noScript.episodeCount === 4, "No-script lineage lost Episodes");
  assert(noScript.zoomDisabled, "No-script controls are enabled");
  assert(
    await evaluate("Boolean(document.querySelector('.workflow-session-destination'))"),
    "No-script Trace lost the Session destination",
  );
  assert(
    await evaluate("Boolean(document.querySelector('[data-workflow-episode-trace]:not([hidden]) form[data-workflow-correction-form]'))"),
    "No-script Trace lost sequential correction forms",
  );
  const noScriptLoaded = cdp.event("Page.loadEventFired");
  await evaluate(`document.querySelector(
    '[data-workflow-episode-trace]:not([hidden]) input[name="action"][value="reopen"]',
  ).form.querySelector('button[type="submit"]').click()`);
  await noScriptLoaded;
  await waitFor(
    "document.querySelector('[data-workflow-correction-feedback]:not([hidden])')",
    "No-script correction did not return fixed feedback",
  );
  const noScriptSubmitted = await state();
  assert(noScriptSubmitted.correctionFeedback?.includes("사용자 확인"), "No-script feedback is missing");
  await capture("workflow-no-script-1440", { fullPage: true });
  await cdp.send("Emulation.setScriptExecutionDisabled", { value: false });

  const evidence = {
    detailReference: detailState,
    viewports: viewportEvidence,
    interaction: {
      expanded,
      selected: interaction,
      back,
      forward,
      relation,
      zoomed,
      ordinaryWheelOwned,
      modifierWheelOwned,
      sourceReturn,
      correctionBefore,
      correctionAfter,
      closed,
      reopened,
      undone,
      stale,
      cancel,
      renderFailure,
      noScript,
      noScriptSubmitted,
    },
    outputDir,
  };
  process.stdout.write(`${JSON.stringify(evidence, null, 2)}\n`);
  cdp.close();
}

try {
  await main();
} catch (error) {
  process.stderr.write(`${error.stack || error}\n${chromeErrors}\n`);
  process.exitCode = 1;
} finally {
  chrome.kill("SIGTERM");
  await rm(profile, { recursive: true, force: true });
}
