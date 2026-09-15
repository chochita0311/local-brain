import { spawn } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";


const baseUrl = process.argv[2] || "http://127.0.0.1:8000";
const outputDir = process.argv[3] || join(tmpdir(), "localbrain-schema-browser-qa");
const chromePath = process.env.LOCALBRAIN_CHROME_PATH
  || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const port = 9300 + (process.pid % 500);
const profile = join(tmpdir(), `localbrain-schema-qa-profile-${process.pid}`);

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

async function waitForJson(path, attempts = 80) {
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
      const waiters = this.waiters.get(method) || [];
      waiters.push(resolve);
      this.waiters.set(method, waiters);
      const timer = setTimeout(() => {
        const current = this.waiters.get(method) || [];
        this.waiters.set(method, current.filter((item) => item !== resolve));
        reject(new Error(`Timed out waiting for ${method}`));
      }, timeout);
      waiters[waiters.length - 1] = (value) => {
        clearTimeout(timer);
        resolve(value);
      };
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
      throw new Error(result.exceptionDetails.text || "Browser evaluation failed");
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

  const navigate = async (path, { diagramState = "rendered" } = {}) => {
    const loaded = cdp.event("Page.loadEventFired");
    await cdp.send("Page.navigate", { url: `${baseUrl}${path}` });
    await loaded;
    if (diagramState) {
      await waitFor(
        `document.querySelector('[data-schema-mermaid-state="${diagramState}"]')`,
        `Schema diagram did not reach ${diagramState}: ${path}`,
      );
    }
    await waitFor(
      "document.querySelector('[data-schema-explorer]')",
      `Schema Explorer missing: ${path}`,
    );
  };

  const state = () => evaluate(`(() => {
    const explorer = document.querySelector('[data-schema-explorer]');
    const diagramScroll = document.querySelector('.schema-diagram-scroll');
    return {
      href: location.href,
      innerWidth,
      clientWidth: document.documentElement.clientWidth,
      documentWidth: document.documentElement.scrollWidth,
      subjectCount: document.querySelectorAll('.schema-subject-link:not([href="/schema"])').length,
      tableCount: document.querySelectorAll('.schema-table-link').length,
      currentArea: document.querySelector('.schema-subject-link[aria-current="page"] strong')?.textContent.trim() || null,
      currentTable: document.querySelector('.schema-table-link[aria-current="page"] code')?.textContent.trim() || null,
      detailTable: document.querySelector('#schema-table-title code')?.textContent.trim() || null,
      diagramState: document.querySelector('[data-schema-mermaid-state]')?.dataset.schemaMermaidState || null,
      layoutState: document.querySelector('[data-schema-layout-state]')?.dataset.schemaLayoutState || null,
      layoutStatus: document.querySelector('[data-schema-layout-status]')?.textContent.trim() || null,
      diagramScrolls: diagramScroll ? diagramScroll.scrollWidth > diagramScroll.clientWidth : false,
      focusedHeading: document.activeElement?.hasAttribute('data-schema-focus') || false,
      focusTarget: document.activeElement?.dataset.schemaFocus || null,
      focusTop: document.activeElement?.hasAttribute('data-schema-focus')
        ? Math.round(document.activeElement.getBoundingClientRect().top)
        : null,
      stickyOffset: Number.parseFloat(
        getComputedStyle(document.documentElement).getPropertyValue('--shell-sticky-offset'),
      ),
      scrollY: Math.round(window.scrollY),
      maxScrollY: Math.round(document.documentElement.scrollHeight - window.innerHeight),
      notice: document.querySelector('[data-schema-notice]')?.dataset.schemaNotice || null,
      unavailable: Boolean(document.querySelector('[data-schema-error]')),
      explorerBusy: explorer?.getAttribute('aria-busy'),
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

  const clickHref = async (href) => {
    const clicked = await evaluate(`(() => {
      const link = [...document.querySelectorAll('[data-schema-link]')]
        .find((item) => item.getAttribute('href') === ${JSON.stringify(href)});
      if (!link) return false;
      link.click();
      return true;
    })()`);
    assert(clicked, `Missing Schema link: ${href}`);
  };

  const viewports = [
    { width: 1440, path: "/schema", name: "global-1440" },
    {
      width: 920,
      path: "/schema?area=work-organization-and-resources",
      name: "area-920",
    },
    {
      width: 700,
      path: "/schema?area=usage-and-cost-records&table=usage_records",
      name: "table-700",
    },
    {
      width: 320,
      path: "/schema?area=usage-and-cost-records&table=usage_records",
      name: "table-320",
    },
  ];
  const viewportEvidence = [];
  for (const viewport of viewports) {
    await setViewport(viewport.width);
    await navigate(viewport.path);
    const current = await state();
    assert(current.innerWidth === viewport.width, `Viewport mismatch at ${viewport.width}`);
    assert(
      current.documentWidth <= current.clientWidth,
      `Document overflow at ${viewport.width}: ${current.documentWidth}`,
    );
    assert(current.subjectCount === 10, `Incomplete subject navigation at ${viewport.width}`);
    assert(current.diagramState === "rendered", `Diagram unavailable at ${viewport.width}`);
    assert(current.layoutState === "elk", `ELK layout missing at ${viewport.width}`);
    assert(current.layoutStatus === "직각 관계 배치", `ELK label mismatch at ${viewport.width}`);
    if (viewport.path.includes("table=")) {
      assert(current.currentTable === "usage_records", `Table selection mismatch at ${viewport.width}`);
      assert(current.detailTable === "usage_records", `Table detail mismatch at ${viewport.width}`);
    }
    viewportEvidence.push(current);
    await capture(viewport.name, { fullPage: viewport.width >= 700 });
    if (viewport.width === 320) {
      await evaluate("document.querySelector('#schema-table-title').scrollIntoView({block: 'start'})");
      await capture("table-detail-320");
    }
  }

  await setViewport(1440);
  await navigate("/schema");
  await clickHref("/schema?area=usage-and-cost-records");
  await waitFor(
    "location.search === '?area=usage-and-cost-records' && document.querySelector('[data-schema-mermaid-state=\"rendered\"]')",
    "Area partial navigation did not settle",
  );
  let interaction = await state();
  assert(interaction.currentArea === "Usage and cost records", "Area current state mismatch");
  assert(interaction.focusedHeading, "Area navigation did not focus the destination heading");
  assert(interaction.focusTarget === "area", "Area navigation focused the wrong heading");
  assert(
    interaction.focusTop >= interaction.stickyOffset - 1,
    `Area heading scrolled under the sticky shell: ${interaction.focusTop}/${interaction.stickyOffset}`,
  );
  assert(
    interaction.focusTop <= interaction.stickyOffset + 1
      || interaction.scrollY >= interaction.maxScrollY - 1,
    `Area heading did not settle at the nearest reachable offset: ${JSON.stringify(interaction)}`,
  );

  await clickHref("/schema?area=usage-and-cost-records&table=usage_records");
  await waitFor(
    "location.search.includes('table=usage_records') && document.querySelector('#schema-table-title code')?.textContent.trim() === 'usage_records'",
    "Table partial navigation did not settle",
  );
  interaction = await state();
  assert(interaction.currentTable === "usage_records", "Table current state mismatch");
  assert(interaction.focusedHeading, "Table navigation did not focus the destination heading");
  assert(interaction.focusTarget === "table", "Table navigation focused the wrong heading");
  assert(
    interaction.focusTop >= interaction.stickyOffset - 1,
    `Table heading scrolled under the sticky shell: ${interaction.focusTop}/${interaction.stickyOffset}`,
  );
  assert(
    interaction.focusTop <= interaction.stickyOffset + 1
      || interaction.scrollY >= interaction.maxScrollY - 1,
    `Table heading did not settle at the nearest reachable offset: ${JSON.stringify(interaction)}`,
  );

  await evaluate("history.back()");
  await waitFor(
    "location.search === '?area=usage-and-cost-records' && !document.querySelector('#schema-table-title')",
    "Back navigation did not restore area state",
  );
  const backState = await state();
  assert(backState.focusedHeading, "Back navigation did not restore focus");
  assert(backState.focusTarget === "area", "Back navigation restored the wrong focus target");

  await evaluate("history.forward()");
  await waitFor(
    "location.search.includes('table=usage_records') && document.querySelector('#schema-table-title')",
    "Forward navigation did not restore table state",
  );
  const forwardState = await state();
  assert(forwardState.currentTable === "usage_records", "Forward table state mismatch");
  assert(forwardState.focusTarget === "table", "Forward navigation restored the wrong focus target");

  await navigate("/schema");
  await evaluate(`(() => {
    const links = [...document.querySelectorAll('[data-schema-link]')];
    links.find((item) => item.getAttribute('href') === '/schema?area=source-registry-and-scans').click();
    links.find((item) => item.getAttribute('href') === '/schema?area=maintenance-execution').click();
  })()`);
  await waitFor(
    "location.search === '?area=maintenance-execution' && document.querySelector('[data-schema-mermaid-state=\"rendered\"]')",
    "Rapid selection did not preserve the latest destination",
  );
  const rapidState = await state();
  assert(rapidState.currentArea === "Maintenance execution", "Stale request won rapid selection");
  assert(rapidState.focusTarget === "area", "Rapid area selection focused the wrong heading");

  await cdp.send("Network.setCacheDisabled", { cacheDisabled: false });
  await navigate("/schema?area=maintenance-execution&qa=warm-cache");
  const reloaded = cdp.event("Page.loadEventFired");
  await cdp.send("Page.reload", { ignoreCache: false });
  await reloaded;
  await waitFor(
    "document.querySelector('[data-schema-mermaid-state=\"rendered\"]')",
    "Warm-cache revisit left Schema markup inert",
  );
  const warmCacheState = await state();
  assert(warmCacheState.tableCount === 2, "Warm-cache revisit lost area content");
  await cdp.send("Network.setCacheDisabled", { cacheDisabled: true });

  await cdp.send("Network.setBlockedURLs", { urls: ["*mermaid-adapter.js*"] });
  await navigate("/schema?area=local-context-corpus&qa=blocked", {
    diagramState: "unavailable",
  });
  const blockedState = await state();
  assert(blockedState.subjectCount === 10, "Mermaid failure removed subject navigation");
  assert(blockedState.tableCount === 2, "Mermaid failure removed the textual table index");
  await cdp.send("Network.setBlockedURLs", { urls: [] });

  await cdp.send("Emulation.setScriptExecutionDisabled", { value: true });
  await navigate(
    "/schema?area=source-registry-and-scans&table=source_files&qa=no-script",
    { diagramState: null },
  );
  const noScriptState = await state();
  assert(noScriptState.currentTable === "source_files", "No-script current table missing");
  assert(noScriptState.detailTable === "source_files", "No-script table detail missing");
  assert(noScriptState.subjectCount === 10, "No-script subject links missing");
  await cdp.send("Emulation.setScriptExecutionDisabled", { value: false });

  await navigate("/schema?area=private-query-value&table=another-private-value");
  const invalidState = await state();
  const invalidText = await evaluate("document.querySelector('[data-schema-explorer]').textContent");
  assert(invalidState.notice === "invalid-area", "Invalid area feedback missing");
  assert(invalidState.currentArea === "Global model", "Invalid area did not normalize globally");
  assert(!invalidText.includes("private-query-value"), "Invalid query was reflected");

  const evidence = {
    viewports: viewportEvidence,
    interaction: {
      table: interaction,
      back: backState,
      forward: forwardState,
      rapid: rapidState,
      warmCache: warmCacheState,
      blocked: blockedState,
      noScript: noScriptState,
      invalid: invalidState,
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
}
