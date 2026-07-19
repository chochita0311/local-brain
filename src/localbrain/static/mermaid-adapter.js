import mermaid from "./vendor/mermaid/mermaid.esm.min.js";

const OWNED_SELECTOR = '[data-localbrain-mermaid="owned"]';
const SOURCE_SELECTOR = 'script[type="text/plain"][data-localbrain-mermaid-source]';
let initialized = false;
let renderSequence = 0;

function initializeMermaid() {
  if (initialized) return;
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

export async function renderLocalBrainMermaid(node) {
  if (!(node instanceof Element) || !node.matches(OWNED_SELECTOR)) {
    return boundedFailure("untrusted-node");
  }

  const sourceNode = node.querySelector(SOURCE_SELECTOR);
  const source = sourceNode?.textContent?.trim();
  if (!source) return boundedFailure("missing-source");

  initializeMermaid();
  renderSequence += 1;

  try {
    const renderId = `localbrain-mermaid-${renderSequence}`;
    const { svg, bindFunctions } = await mermaid.render(renderId, source);
    const rendered = document.createElement("div");
    rendered.setAttribute("data-localbrain-mermaid-rendered", "true");
    rendered.innerHTML = svg;
    node.replaceChildren(rendered);
    bindFunctions?.(rendered);
    return { ok: true, code: "rendered" };
  } catch (_error) {
    return boundedFailure("render-failed");
  }
}

export async function renderLocalBrainMermaidAll(root = document) {
  if (!(root instanceof Document || root instanceof Element)) {
    return [boundedFailure("untrusted-root")];
  }
  return Promise.all(
    [...root.querySelectorAll(OWNED_SELECTOR)].map(renderLocalBrainMermaid),
  );
}
