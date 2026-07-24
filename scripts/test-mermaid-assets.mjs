import assert from "node:assert/strict";
import { appendFile, mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import {
  clampSchemaZoom,
  schemaAnchoredScroll,
  schemaZoomFromWheel,
} from "../src/localbrain/static/schema-explorer.js";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const BUILDER = join(ROOT, "scripts/build-mermaid-assets.mjs");

function runBuilder(mode, outputDir) {
  return spawnSync(process.execPath, [BUILDER, mode], {
    cwd: ROOT,
    encoding: "utf8",
    env: { ...process.env, LOCALBRAIN_MERMAID_OUTPUT_DIR: outputDir },
  });
}

const temporaryOutput = await mkdtemp(join(tmpdir(), "localbrain-mermaid-test-"));

try {
  const buildResult = runBuilder("build", temporaryOutput);
  assert.equal(buildResult.status, 0, buildResult.stderr);

  const currentResult = runBuilder("check", temporaryOutput);
  assert.equal(currentResult.status, 0, currentResult.stderr);

  await appendFile(join(temporaryOutput, "asset-manifest.json"), "\n");
  const staleResult = runBuilder("check", temporaryOutput);
  assert.notEqual(staleResult.status, 0, "A modified asset must fail freshness validation.");
  assert.match(`${staleResult.stdout}${staleResult.stderr}`, /stale/);

  const adapter = await readFile(
    join(ROOT, "src/localbrain/static/mermaid-adapter.js"),
    "utf8",
  );
  assert.match(adapter, /securityLevel:\s*"strict"/);
  assert.match(adapter, /startOnLoad:\s*false/);
  assert.match(adapter, /suppressErrorRendering:\s*true/);
  assert.match(adapter, /data-localbrain-mermaid="owned"/);
  assert.doesNotMatch(adapter, /mermaid\.run\s*\(/);

  assert.equal(clampSchemaZoom(0), 0.1);
  assert.equal(clampSchemaZoom(4), 3);
  assert.ok(schemaZoomFromWheel(1, -100) > 1);
  assert.ok(schemaZoomFromWheel(1, 100) < 1);
  assert.equal(schemaAnchoredScroll(200, 100, 1, 2), 500);

  console.log("LocalBrain Mermaid asset contract tests passed.");
} finally {
  await rm(temporaryOutput, { recursive: true, force: true });
}
