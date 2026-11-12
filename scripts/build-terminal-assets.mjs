import {build} from 'esbuild';
import {readFile, writeFile, mkdir, mkdtemp, rm} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {tmpdir} from 'node:os';
import {join, dirname, resolve} from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const destination = join(root, 'src/localbrain/static/vendor/xterm');
const fonts = {
  'fonts/D2Coding-Regular.woff2': '0fa3ea3b5990782e8e0c124ff6918c64ad057bc87365565405531e010cfdfbaa',
  'fonts/D2Coding-Bold.woff2': 'b79b36b1e53e10da5cfc4142c080c755ccb6ae0d359ab4a6335e50184047479a',
  'fonts/D2Coding-OFL.txt': '1807e8dec4d65f474cbf9be39f5e2254ecb81702babc320749e272ea66ffcc69'
};
const files = ['terminal.esm.js', 'xterm.css', 'xterm-LICENSE.txt', 'fit-LICENSE.txt', 'unicode11-LICENSE.txt',
  ...Object.keys(fonts), 'fonts/provenance.json', 'asset-manifest.json'];
const hash = value => createHash('sha256').update(value).digest('hex');
async function generate(folder) {
  await mkdir(folder, {recursive: true});
  await mkdir(join(folder, 'fonts'), {recursive: true});
  for (const name of [...Object.keys(fonts), 'fonts/provenance.json']) {
    const bytes = await readFile(join(destination, name));
    if (fonts[name] && hash(bytes) !== fonts[name]) throw new Error('Unreviewed terminal font: ' + name);
    await writeFile(join(folder, name), bytes);
  }
  await build({absWorkingDir: root, bundle: true, format: 'esm', platform: 'browser',
    // The pinned ESM build's local enum is miscompiled on re-minification.
    // Bundle the same release's published CommonJS build instead.
    mainFields: ['main'],
    target: ['es2020'], minify: true, legalComments: 'none',
    outfile: join(folder, 'terminal.esm.js'),
    stdin: {contents: "export {Terminal} from '@xterm/xterm'; export {FitAddon} from '@xterm/addon-fit'; export {Unicode11Addon} from '@xterm/addon-unicode11'; export {VERSION as checkpointVersion, restore as restoreCheckpoint} from './src/localbrain/terminal/checkpoint.cjs'; export {attachKoreanInput} from './src/localbrain/terminal/korean-input.cjs'; export {DEFAULT_THEME, suppressColorReports} from './src/localbrain/terminal/colors.cjs';",
      resolveDir: root, sourcefile: 'localbrain-terminal-entry.js'}});
  for (const [from, to] of [
    ['@xterm/xterm/css/xterm.css', 'xterm.css'],
    ['@xterm/xterm/LICENSE', 'xterm-LICENSE.txt'],
    ['@xterm/addon-fit/LICENSE', 'fit-LICENSE.txt'],
    ['@xterm/addon-unicode11/LICENSE', 'unicode11-LICENSE.txt']
  ]) await writeFile(join(folder, to), await readFile(join(root, 'node_modules', from)));
  const outputs = {};
  for (const name of files.slice(0, -1)) outputs[name] = hash(await readFile(join(folder, name)));
  await writeFile(join(folder, 'asset-manifest.json'), JSON.stringify({
    schema: 'localbrain.terminal-assets.v1', dependencies: {xterm: '6.0.0', fit: '0.11.0', unicode11: '0.9.0', d2coding: '1.4.0'},
    mainFields: ['main'], outputs
  }, null, 2) + '\n');
}
async function verifyParser(folder) {
  const {Terminal, Unicode11Addon} = await import(pathToFileURL(join(folder, 'terminal.esm.js')).href);
  const terminal = new Terminal({allowProposedApi: true});
  terminal.loadAddon(new Unicode11Addon());
  terminal.unicode.activeVersion = '11';
  const replies = [];
  terminal.onData(data => replies.push(data));
  try {
    terminal.resize(100, 30);
    await new Promise((resolve, reject) => {
      const timeout = setTimeout(() => reject(new Error('Terminal parser did not finish')), 2000);
      terminal.write('\x1b[?2026$p', () => { clearTimeout(timeout); resolve(); });
    });
    if (replies.join('') !== '\x1b[?2026;2$y') throw new Error('Terminal mode query failed');
    await new Promise(resolve => terminal.write('A🧠한B', resolve));
    if (terminal.buffer.active.cursorX !== 6 || terminal.buffer.active.getLine(0).getCell(1).getWidth() !== 2) {
      throw new Error('Unicode11 cell width failed');
    }
  } finally { terminal.dispose(); }
}
async function rendererImport(folder, update) {
  const manifest = JSON.parse(await readFile(join(folder, 'asset-manifest.json'), 'utf8'));
  const specifier = "'./vendor/xterm/terminal.esm.js?v=" + manifest.outputs['terminal.esm.js'].slice(0, 12) + "'";
  const entry = join(root, 'src/localbrain/static/terminal.js');
  const source = await readFile(entry, 'utf8');
  if (!source.includes("from './vendor/xterm/terminal.esm.js")) throw new Error('Renderer import not found');
  const versioned = source.replace(/'\.\/vendor\/xterm\/terminal\.esm\.js(?:\?v=[^']*)?'/, specifier);
  if (update) await writeFile(entry, versioned);
  else if (versioned !== source) throw new Error('Renderer import version is stale');
  const css = await readFile(join(root, 'src/localbrain/static/terminal.css'), 'utf8');
  for (const [name, digest] of Object.entries(fonts)) {
    if (name.endsWith('.woff2') && !css.includes(name + '?v=' + digest.slice(0, 12))) {
      throw new Error('Terminal font URL is stale: ' + name);
    }
  }
}
const mode = process.argv[2];
if (mode === 'build') { await generate(destination); await rendererImport(destination, true); }
else if (mode === 'check') {
  const temporary = await mkdtemp(join(tmpdir(), 'localbrain-terminal-assets.'));
  try {
    await generate(temporary);
    await writeFile(join(temporary, 'package.json'), '{"type":"module"}\n');
    await verifyParser(temporary);
    await rendererImport(temporary, false);
    for (const name of files) {
      if (!(await readFile(join(temporary, name))).equals(await readFile(join(destination, name)))) {
        throw new Error('Terminal asset is stale: ' + name);
      }
    }
  } finally { await rm(temporary, {recursive: true, force: true}); }
} else throw new Error('Usage: node scripts/build-terminal-assets.mjs build|check');
console.log('Terminal assets ' + mode + ': PASS');
