# EVAL-0160: Terminal Korean And Embedded Terminal Audit

- Status: `complete`
- Result: `FAIL`
- Evidence Coverage: `partial`
- Feature: [FEAT-0166](../feature/feat-0166-web-terminal-work-area.md)
- Spec: [SPEC-0166](../spec/spec-0166-web-terminal-work-area.md)
- Run: [RUN-244](../run/run-20261111-244-terminal-korean-and-embedded-audit.md)
- Parent PRD: [PRD-0028](../prd/prd-0028-web-terminal-work-area.md)
- Profile: `fullstack-product`; attempt1.

The reported box-glyph case is reproduced and repaired. The whole embedded
terminal cannot receive a completeness/compatibility pass: a new view loses
required VT state. The successful corrections and automated suite below do not
erase that failure. Eval0158/0159 remain historical evidence within their scope.

## Korean And Font Diagnosis

The actual iTerm2 regular/non-ASCII font configuration and installed app versions
were inspected read-only and retained at the private evidence owner. LocalBrain
previously used the system mono stack at13px. Font names, sizes and fallback
behavior are distinct; the correction prefers an installed font without importing
the iTerm profile or claiming identical sizing. No local font files were copied
into the repository. The shareable reproduction uses synthetic text and D2Coding.

Private read-only output classification informed a synthetic Powerline U+E0B0
reproduction. Its scope does not establish that all user Korean history is intact;
raw user output was neither printed nor persisted. Synthetic PTY input/output preserved NFC/NFD Hangul and a
UTF-8 charmap. CoreText with resolved font names and an ASCII positive control
shows Menlo lacks U+E0B0, while D2Coding includes it and ordinary Hangul. An
earlier sandbox-only font probe returned unusable results; the resolved-font
probe and actual Chrome glyph comparison supersede it.

The same codepoints rendered boxes under the previous mono stack and arrows
under D2Coding. Latin/Hangul natural-width ratio was about1:1.437 under the prior
fallback versus1:2 under D2Coding. This supports a font/glyph cause for the
reproduced symptom, independently of the separate emoji-width defect. Physical
Korean IME composition/Enter/Backspace remains unverified; program output, paste
or browser text insertion cannot replace that evidence.

## Embedded Terminal Comparison

Official documentation/source establishes expected categories, not observed
native IDE runtime parity. Current [IntelliJ Help](https://www.jetbrains.com/help/idea/terminal-emulator.html)
identifies itself as2026.3 and says libghostty, while Classic is JediTerm; that
does not establish an installed app's active engine. The2025 architecture article
is historical. Private application metadata is retained outside Git; no installed
IDE was launched or modified for comparison.

| Category | LocalBrain result / evidence limit |
| --- | --- |
| Real terminal architecture | Real PTY, shell startup, VT parser/renderer and text/binary transport are present. This is an ordinary embedded-terminal structure, not a command-output widget. Source plus real PTY/browser checks support this boundary. |
| UTF-8 and glyphs | Synthetic Korean round-trip and NFC/NFD cells pass. Font fallback for the reproduced Powerline box case is repaired. Actual glyph coverage, locale and cell width are separate concerns. |
| Unicode/cursor width | Ordinary Hangul was already width2. Modern emoji U+1F9E0 was width1 while macOS wcwidth expected2; both new engines now select pinned Unicode11. Complex emoji/ZWJ and arbitrary OS versions are not established by this repair. |
| IME and keyboard | xterm contains Korean composition handling and the wrapper preserves composing/229 events. Shift+Escape focus escape was exercised. Physical OS IME, comprehensive modifier/clipboard and assistive-tool matrices remain open. |
| Paste and congested input | Bounded queuing/framing preserves ordered Korean input and surrogate pairs. Overflow is explicit; disconnect/ownership loss cancels unsent input. An interrupted zsh bracketed paste recovered with Ctrl+C; this is not every application's paste recovery. |
| VT, resize, reconnect | Ordinary text/alternate-screen, resize and same-PID background paths pass within observations. Partial CSI/OSC, scroll region, saved cursor and custom tab stops fail restoration; new-page CSI failure is also reproduced in Chrome. This blocks a broad compatibility pass. |
| Lifecycle and ownership | Independent manager, one input/resize owner, scoped termination and bounded buffers remain implemented. Baseline process tests and selected current lease/flood/binary checks support observed paths, not universal process/security approval. |
| Setup and updates | Missing main modules reopen setup; clean public-registry install succeeds without starting a manager. Content-hash renderer import and reciprocal width admission handle tested update paths. Deeper dependency corruption is outside the existence check. |
| IDE conveniences | Per-terminal font controls, profile arguments, output search, plain-URL detection addon, injected command detection/decorations/navigation and IDE completion are absent. Cwd updates depend on shell-reported OSC7; no injected integration supplies it. The library's built-in OSC8 link behavior is not fully evaluated; absence of a link addon does not prove all links are unsupported. Shell-native completion still follows the existing shell. These are customization/workflow differences, not all mandatory terminal correctness requirements. |
| Product exclusions | Native/Windows first delivery, external iTerm attachment, remote terminals, cold recovery/command replay, persistent transcripts and output-triggered clipboard/image/network effects remain outside the agreed product scope. Their absence is not a defect to silently implement here. |

Primary comparator sources: [VS Code basics](https://code.visualstudio.com/docs/terminal/basics),
[appearance](https://code.visualstudio.com/docs/terminal/appearance),
[advanced](https://code.visualstudio.com/docs/terminal/advanced),
[profiles](https://code.visualstudio.com/docs/terminal/profiles),
[shell integration](https://code.visualstudio.com/docs/terminal/shell-integration),
[IntelliJ terminal](https://www.jetbrains.com/help/idea/terminal-emulator.html),
[settings](https://www.jetbrains.com/help/idea/settings-tools-terminal.html),
[JetBrains2025 architecture](https://blog.jetbrains.com/idea/2025/04/jetbrains-terminal-a-new-architecture/),
[iTerm text settings](https://iterm2.com/documentation-preferences-profiles-text.html),
[xterm encoding](https://xtermjs.org/docs/guides/encoding/),
[xterm6 Unicode source](https://github.com/xtermjs/xterm.js/blob/6.0.0/src/common/input/UnicodeV6.ts),
[composition source](https://github.com/xtermjs/xterm.js/blob/6.0.0/src/browser/input/CompositionHelper.ts),
[Unicode addon](https://github.com/xtermjs/xterm.js/blob/6.0.0/addons/addon-unicode11/README.md)
and [node-pty1.1 source](https://github.com/microsoft/node-pty/blob/v1.1.0/src/unixTerminal.ts).

## Independent Review And Adjudication

Explicit user authorization admitted three named workers with no author history:
research_worker for official criteria/alternative explanations, review_challenger
for frozen whole-code inspection, bounded_verifier for exact baseline checks.
Primary owns requirements, architecture, persistence, implementation, source
reconciliation and acceptance. Research/code workers executed no reviewed code,
builds/tests/runtime changes, dependency installs, private preference reads or
publication. Role contracts are not a separately established OS sandbox; actual
serving model identifiers are unavailable. Supplied runtime witnesses are primary/
verifier evidence, not independent challenger executions.

| Claim | Status / action and evidence |
| --- | --- |
| Default Unicode6 disagrees with modern emoji width | Supported / fixed for new matching views/managers. New browser→legacy manager retains6; old client→new manager is refused before input grant. Real browser/PTY and direct claim witnesses cover both directions. |
| SerializeAddon is not a complete checkpoint | Supported / retained technical blocker. Five standalone differential cases fail; a fresh Chrome view renders mRED after partial CSI where uninterrupted parsing yields RED. Same-renderer reconnect retaining some parser state is counterevidence to an all-reconnect failure claim. No full-VT completion claimed. |
| Outgoing socket pressure silently drops input | Supported / fixed on inspected paths. Korean input waits/drains in order,63k escaped NUL text becomes8 frames (max49178 bytes), surrogate boundaries stay intact, oversize events send zero packets with feedback, and disconnect never replays queued input. |
| Matching marker hides missing runtime modules | Supported / fixed for main-file loss. Unit cases and actual stopped-QA module removal show installed=false and the component-install action. Deeper integrity is not established. |
| New addon lock uses corporate tarball host | Supported / fixed. Both locks use official public tarball/integrity, unchanged existing entries; empty-cache public setup succeeds. No corporate access is required by the new locked URL. |
| Cached older vendor lacks the new export | Supported / fixed. Generated/checked content-hash import works with a fresh cache containing the baseline unversioned module. Chrome confirms that old module remains cached (transferSize0), while the new entry loads/creates successfully. |
| Old browser/new manager still disagree | Supported / fixed. Width declaration is checked before lease grant, missing declarations default6, and mismatches receive refresh feedback. New browser/old manager width6 was also observed without changing the user's manager. |

Interrupted bracketed paste began as a coverage question. A controlled8192-unit
first chunk followed by cancellation/reconnect was tested in zsh; feedback now
states possible partial delivery and Ctrl+C recovery. Successful recovery is
bounded to that application and condition, not evidence of rollback or universal
paste recovery. The snapshot defect requires a separate checkpoint design/fix
under the unchanged retention and performance constraints; no private-state hack
or unlimited replay log was introduced to mask the gap.

Frozen baseline1844 manifest: `b424d6c7fafcf66a3347827ad48bd33860f3a13aa47f2fb56ae3e9fadaf3aaac`.
First repair1847: `568c5b1a4ef8920272dbddfe05e804c8fdfa1a31a70f36c286a43602926d17e9`.
Final code1847: `66719fa70a8a5707dec9729888098c27fcf7af862841cf6d0a9ea8098879f073`.
The fresh pass plus two evidence-driven confirmations validated complete contents/
inventories; the last return found no additional source-backed regression within
that bounded delta. Guidance changes retain the compatibility blocker rather than
weaken it. Initial validation generated bytecode in the source bundle; its list
was retained and exact source inventory restored before subsequent confirmation.

## Verification And Remaining Gate

- Final Python suite: **1,637 tests, OK (24 skipped)**. Those24 require the prepared
  macOS PTY engine. Six unique current real-PTY methods pass separately: Unicode,
  incompatible claims, alternate/snapshot/background, binary, lease and flood.
- Baseline Terminal38: initial restricted execution had21 startup errors. The
  escalated run passed37 and failed one writable-copy fixture because its source
  had been frozen read-only. That exact method passes in a separate writable
  execution copy. Baseline settings12 pass. Preserve all initial logs; these
  failures are not reported as production regressions or silently discarded.
- JS syntax and reproducible asset/parser/hash checks pass; actual Chrome covers
  same-codepoint fonts, cache upgrade, legacy widths, input pressure/framing,
  interrupted paste, focus escape, resize/narrow320px and module-loss recovery.
  Actual fresh-view and differential restoration failures remain explicit.
- Clean public component installation succeeds without manager start. Final web
  wheel17 relevant files byte-match source; actual native collection retains125
  data files/234 modules and excludes Terminal/Unicode assets. Privacy1847 and
  catalog checks pass. No native build, publication or actual-user service restart.

Contract/whole-compatibility evaluation is FAIL because of the demonstrated VT
checkpoint gap; corrected-path functional/design/interaction checks pass only in
their stated observations. Physical IME, Safari, complete assistive/clipboard
coverage, long-soak and representative corpus/performance acceptance remain open.
The audit is delivered with these supported limits; full Feature acceptance is
blocked. Next technical work must preserve partial parser state and independent
VT modes across bounded checkpoints, then renew the failing differential and
fresh-view witnesses before claiming normal TUI reconnect compatibility.
