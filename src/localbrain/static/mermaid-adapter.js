import mermaid, { elkLayouts } from "./vendor/mermaid/mermaid.esm.min.js";

const OWNED_SELECTOR = '[data-localbrain-mermaid="owned"]';
const SOURCE_SELECTOR = 'script[type="text/plain"][data-localbrain-mermaid-source]';
const SCHEMA_LAYOUT_ATTRIBUTE = "data-localbrain-mermaid-layout";
let initialized = false;
let renderSequence = 0;

function initializeMermaid() {
  if (initialized) return;
  mermaid.registerLayoutLoaders(elkLayouts);
  mermaid.initialize({
    startOnLoad: false,
    securityLevel: "strict",
    suppressErrorRendering: true,
    htmlLabels: false,
  });
  initialized = true;
}

function boundedFailure(code) {
  return { ok: false, code };
}

export function schemaMermaidAttempts(source, requestedLayout) {
  if (requestedLayout !== "elk") return [{ layout: "dagre", source }];
  return [
    {
      layout: "elk",
      source: `---\nconfig:\n  layout: elk\n---\n${source}`,
    },
    { layout: "dagre", source },
  ];
}

export async function renderLocalBrainMermaid(node) {
  if (!(node instanceof Element) || !node.matches(OWNED_SELECTOR)) {
    return boundedFailure("untrusted-node");
  }

  const sourceNode = node.querySelector(SOURCE_SELECTOR);
  const source = sourceNode?.textContent?.trim();
  if (!source) return boundedFailure("missing-source");

  initializeMermaid();
  const attempts = schemaMermaidAttempts(
    source,
    node.getAttribute(SCHEMA_LAYOUT_ATTRIBUTE),
  );
  for (const attempt of attempts) {
    renderSequence += 1;
    try {
      const renderId = `localbrain-mermaid-${renderSequence}`;
      const { svg, bindFunctions } = await mermaid.render(
        renderId,
        attempt.source,
      );
      const rendered = document.createElement("div");
      rendered.setAttribute("data-localbrain-mermaid-rendered", "true");
      rendered.setAttribute("data-localbrain-mermaid-layout", attempt.layout);
      rendered.innerHTML = svg;
      node.replaceChildren(rendered);
      bindFunctions?.(rendered);
      return {
        ok: true,
        code: attempt.layout === "elk"
          ? "rendered-elk"
          : "rendered-dagre",
        layout: attempt.layout,
      };
    } catch (_error) {
      // Schema-owned ELK diagrams retry the unchanged source once with Dagre.
    }
  }
  return boundedFailure("render-failed");
}

export async function renderLocalBrainMermaidAll(root = document) {
  if (!(root instanceof Document || root instanceof Element)) {
    return [boundedFailure("untrusted-root")];
  }
  return Promise.all(
    [...root.querySelectorAll(OWNED_SELECTOR)].map(renderLocalBrainMermaid),
  );
}
