import { readFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import mermaid from "../src/localbrain/static/vendor/mermaid/mermaid.esm.min.js";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const DOCUMENTS = [
  "docs/policies/project/data-model.md",
  "docs/policies/project/data-model/source-registry-and-scans.md",
  "docs/policies/project/data-model/workspace-and-session-activity.md",
  "docs/policies/project/data-model/usage-and-cost-records.md",
  "docs/policies/project/data-model/local-context-corpus.md",
  "docs/policies/project/data-model/work-organization-and-resources.md",
  "docs/policies/project/data-model/review-and-resume-continuity.md",
  "docs/policies/project/data-model/maintenance-execution.md",
  "docs/policies/project/data-model/workflow-assertions.md",
  "docs/policies/project/data-model/derived-retrieval-index.md",
];

mermaid.initialize({ startOnLoad: false, securityLevel: "strict" });

let diagramCount = 0;
for (const relativePath of DOCUMENTS) {
  const document = await readFile(join(ROOT, relativePath), "utf8");
  const diagrams = [...document.matchAll(/```mermaid\s*\n([\s\S]*?)```/g)];
  if (diagrams.length !== 1) {
    throw new Error(`${relativePath}: expected exactly one Mermaid diagram, found ${diagrams.length}`);
  }
  try {
    await mermaid.parse(diagrams[0][1]);
  } catch (error) {
    throw new Error(`${relativePath}: ${error.message}`, { cause: error });
  }
  diagramCount += 1;
}

if (diagramCount !== 10) {
  throw new Error(`Expected 10 Mermaid diagrams, found ${diagramCount}`);
}
console.log("Parsed 10 data-model Mermaid diagrams with the local bundle.");
