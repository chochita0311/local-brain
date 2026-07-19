import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const DOCUMENTS = [
  ["Global model", "docs/policies/project/data-model.md"],
  ["Source registry and scans", "docs/policies/project/data-model/source-registry-and-scans.md"],
  ["Workspace and Session activity", "docs/policies/project/data-model/workspace-and-session-activity.md"],
  ["Usage and cost records", "docs/policies/project/data-model/usage-and-cost-records.md"],
  ["Local Context corpus", "docs/policies/project/data-model/local-context-corpus.md"],
  ["Work organization and resources", "docs/policies/project/data-model/work-organization-and-resources.md"],
  ["Review and resume continuity", "docs/policies/project/data-model/review-and-resume-continuity.md"],
  ["Maintenance execution", "docs/policies/project/data-model/maintenance-execution.md"],
  ["Derived retrieval index", "docs/policies/project/data-model/derived-retrieval-index.md"],
];

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

const cards = [];
for (const [title, relativePath] of DOCUMENTS) {
  const markdown = await readFile(join(ROOT, relativePath), "utf8");
  const match = markdown.match(/```mermaid\s*\n([\s\S]*?)```/);
  if (!match) throw new Error(`Missing Mermaid diagram: ${relativePath}`);
  cards.push(`
    <article class="diagram-card${cards.length === 0 ? " diagram-card-global" : ""}">
      <h2>${escapeHtml(title)}</h2>
      <p>${escapeHtml(relativePath)}</p>
      <div class="diagram" data-localbrain-mermaid="owned">
        <script type="text/plain" data-localbrain-mermaid-source>${escapeHtml(match[1])}</script>
      </div>
    </article>`);
}

const html = `<!doctype html>
<html lang="en" data-render-status="pending">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>LocalBrain data-model render check</title>
  <style>
    :root { color-scheme: light; font-family: Inter, ui-sans-serif, system-ui, sans-serif; }
    * { box-sizing: border-box; }
    body { margin: 0; padding: 32px; color: #17202a; background: #edf1f5; }
    header { display: flex; align-items: end; justify-content: space-between; gap: 24px; margin-bottom: 24px; }
    h1 { margin: 0; font-size: 32px; }
    header p { margin: 0; color: #52606d; }
    #status { border-radius: 999px; padding: 8px 14px; background: #fff; font-weight: 700; }
    main { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20px; }
    .diagram-card { min-width: 0; padding: 20px; border: 1px solid #cbd5df; border-radius: 16px; background: #fff; box-shadow: 0 8px 24px rgb(23 32 42 / 7%); }
    .diagram-card-global { grid-column: 1 / -1; }
    h2 { margin: 0 0 4px; font-size: 20px; }
    .diagram-card > p { margin: 0 0 16px; color: #66788a; font: 13px ui-monospace, monospace; }
    .diagram { overflow: auto; padding: 12px; border-radius: 10px; background: #fafbfd; }
    .diagram svg { display: block; width: 100%; height: auto; min-width: 720px; margin: auto; }
    .diagram-card-global .diagram svg { min-width: 1800px; }
  </style>
</head>
<body>
  <header>
    <div><h1>LocalBrain data-model ERDs</h1><p>Schema-only generated QA preview · not a product route</p></div>
    <div id="status" role="status">Rendering 9 diagrams…</div>
  </header>
  <main>${cards.join("\n")}</main>
  <script type="module">
    import { renderLocalBrainMermaid } from "/src/localbrain/static/mermaid-adapter.js";
    const allCards = [...document.querySelectorAll(".diagram-card")];
    const diagramParam = new URLSearchParams(location.search).get("diagram");
    const requestedIndex = diagramParam === null ? Number.NaN : Number(diagramParam);
    const selectedCards = Number.isInteger(requestedIndex) && requestedIndex >= 0 && requestedIndex < allCards.length
      ? [allCards[requestedIndex]]
      : allCards;
    if (selectedCards.length === 1) {
      allCards.filter((card) => card !== selectedCards[0]).forEach((card) => card.remove());
    }
    const results = [];
    for (const card of selectedCards) {
      const node = card.querySelector('[data-localbrain-mermaid="owned"]');
      results.push(await Promise.race([
        renderLocalBrainMermaid(node),
        new Promise((resolve) => setTimeout(() => resolve({ ok: false, code: "timeout" }), 15000)),
      ]));
    }
    const passed = results.filter((result) => result.ok).length;
    document.documentElement.dataset.renderStatus = passed === selectedCards.length ? "passed" : "failed";
    document.querySelector("#status").textContent = passed + " / " + selectedCards.length + " diagrams rendered";
  </script>
</body>
</html>`;

const output = join(ROOT, ".cache/data-model-preview.html");
await mkdir(dirname(output), { recursive: true });
await writeFile(output, html);
console.log(output);
