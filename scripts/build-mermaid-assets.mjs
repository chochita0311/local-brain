import { createHash } from "node:crypto";
import { mkdtemp, mkdir, readFile, readdir, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { build as bundle } from "esbuild";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const OUTPUT_DIR = resolve(
  process.env.LOCALBRAIN_MERMAID_OUTPUT_DIR
    || join(ROOT, "src/localbrain/static/vendor/mermaid"),
);
const OUTPUT_FILES = [
  "asset-manifest.json",
  "elkjs-LICENSE.txt",
  "esbuild-LICENSE.txt",
  "layout-elk-LICENSE.txt",
  "mermaid-LICENSE.txt",
  "mermaid.esm.min.js",
];

function sha256(content) {
  return createHash("sha256").update(content).digest("hex");
}

async function packageMetadata(name) {
  return JSON.parse(await readFile(join(ROOT, "node_modules", name, "package.json"), "utf8"));
}

async function packageLicense(name, candidates) {
  for (const candidate of candidates) {
    try {
      return await readFile(join(ROOT, "node_modules", name, candidate));
    } catch (error) {
      if (error.code !== "ENOENT") throw error;
    }
  }
  throw new Error(`License file not found for ${name}`);
}

async function generate(destination) {
  await mkdir(destination, { recursive: true });
  const bundlePath = join(destination, "mermaid.esm.min.js");

  await bundle({
    absWorkingDir: ROOT,
    bundle: true,
    charset: "utf8",
    format: "esm",
    legalComments: "none",
    minify: true,
    outfile: bundlePath,
    platform: "browser",
    sourcemap: false,
    stdin: {
      contents: [
        'import mermaid from "mermaid";',
        'import elkLayouts from "@mermaid-js/layout-elk";',
        "export { elkLayouts };",
        "export default mermaid;",
      ].join("\n"),
      loader: "js",
      resolveDir: ROOT,
      sourcefile: "localbrain-mermaid-entry.js",
    },
    target: ["es2020"],
  });

  const [
    lockfile,
    mermaidMetadata,
    layoutElkMetadata,
    elkjsMetadata,
    esbuildMetadata,
    mermaidLicense,
    layoutElkLicense,
    elkjsLicense,
    esbuildLicense,
  ] = await Promise.all([
    readFile(join(ROOT, "package-lock.json")),
    packageMetadata("mermaid"),
    packageMetadata("@mermaid-js/layout-elk"),
    packageMetadata("elkjs"),
    packageMetadata("esbuild"),
    packageLicense("mermaid", ["LICENSE", "LICENSE.md"]),
    packageLicense("@mermaid-js/layout-elk", ["LICENSE", "LICENSE.md"]),
    packageLicense("elkjs", ["LICENSE.md", "LICENSE"]),
    packageLicense("esbuild", ["LICENSE.md", "LICENSE"]),
  ]);

  await writeFile(join(destination, "mermaid-LICENSE.txt"), mermaidLicense);
  await writeFile(join(destination, "layout-elk-LICENSE.txt"), layoutElkLicense);
  await writeFile(join(destination, "elkjs-LICENSE.txt"), elkjsLicense);
  await writeFile(join(destination, "esbuild-LICENSE.txt"), esbuildLicense);

  const outputs = {};
  for (const name of [
    "mermaid.esm.min.js",
    "mermaid-LICENSE.txt",
    "layout-elk-LICENSE.txt",
    "elkjs-LICENSE.txt",
    "esbuild-LICENSE.txt",
  ]) {
    outputs[name] = sha256(await readFile(join(destination, name)));
  }

  const manifest = {
    schema: "localbrain.mermaid-assets.v1",
    build: {
      command: "npm run build:mermaid",
      node: ">=20",
      packageLockSha256: sha256(lockfile),
    },
    dependencies: {
      esbuild: { license: esbuildMetadata.license, version: esbuildMetadata.version },
      elkjs: { license: elkjsMetadata.license, version: elkjsMetadata.version },
      layoutElk: {
        license: layoutElkMetadata.license,
        version: layoutElkMetadata.version,
      },
      mermaid: { license: mermaidMetadata.license, version: mermaidMetadata.version },
    },
    outputs,
  };
  await writeFile(
    join(destination, "asset-manifest.json"),
    `${JSON.stringify(manifest, null, 2)}\n`,
  );
}

async function compareGenerated(generatedDir) {
  let existingNames;
  try {
    existingNames = (await readdir(OUTPUT_DIR)).sort();
  } catch (error) {
    if (error.code === "ENOENT") {
      throw new Error("Mermaid assets are missing; run `npm run build:mermaid`.");
    }
    throw error;
  }

  if (JSON.stringify(existingNames) !== JSON.stringify(OUTPUT_FILES)) {
    throw new Error("Mermaid asset set is stale; run `npm run build:mermaid` and review unexpected files.");
  }

  for (const name of OUTPUT_FILES) {
    const [expected, actual] = await Promise.all([
      readFile(join(generatedDir, name)),
      readFile(join(OUTPUT_DIR, name)),
    ]);
    if (!expected.equals(actual)) {
      throw new Error(`Mermaid asset is stale: ${name}; run \`npm run build:mermaid\`.`);
    }
  }
}

async function main() {
  const mode = process.argv[2];
  if (mode !== "build" && mode !== "check") {
    throw new Error("Usage: node scripts/build-mermaid-assets.mjs <build|check>");
  }

  if (mode === "build") {
    await generate(OUTPUT_DIR);
    const names = (await readdir(OUTPUT_DIR)).sort();
    if (JSON.stringify(names) !== JSON.stringify(OUTPUT_FILES)) {
      throw new Error("Unexpected files exist in the Mermaid output directory; review them before rebuilding.");
    }
    console.log("Built LocalBrain Mermaid assets.");
    return;
  }

  const temporaryRoot = await mkdtemp(join(tmpdir(), "localbrain-mermaid-"));
  await generate(temporaryRoot);
  await compareGenerated(temporaryRoot);
  console.log("LocalBrain Mermaid assets are current.");
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
