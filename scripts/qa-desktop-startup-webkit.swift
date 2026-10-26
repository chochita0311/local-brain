// macOS-only startup regression check against an isolated synthetic backend.
// Set LOCALBRAIN_START_URL to its /desktop/start?token=... URL. The secret and
// page contents are never printed. Optional LOCALBRAIN_QA_STALE_COOKIE=1 checks
// replacing a prior launch cookie. Screenshots are opt-in synthetic evidence.
import AppKit
import WebKit

func finish(_ passed: Bool, _ message: String) {
    print(message)
    fflush(stdout)
    exit(passed ? 0 : 1)
}

final class StartupProbe: NSObject, WKNavigationDelegate, WKURLSchemeHandler {
    let target: URL
    var transitioned = false
    var status = 0

    init(target: URL) { self.target = target }

    func webView(_ view: WKWebView, start task: WKURLSchemeTask) {
        let html = "<!doctype html><meta charset=utf-8><title>Startup check</title>".data(using: .utf8)!
        task.didReceive(URLResponse(url: task.request.url!, mimeType: "text/html",
                                   expectedContentLength: html.count, textEncodingName: "utf-8"))
        task.didReceive(html)
        task.didFinish()
    }

    func webView(_ view: WKWebView, stop task: WKURLSchemeTask) {}

    func webView(_ view: WKWebView, decidePolicyFor response: WKNavigationResponse,
                 decisionHandler: @escaping (WKNavigationResponsePolicy) -> Void) {
        if response.isForMainFrame, let http = response.response as? HTTPURLResponse {
            status = http.statusCode
        }
        decisionHandler(.allow)
    }

    func webView(_ view: WKWebView, didFinish navigation: WKNavigation!) {
        if !transitioned {
            transitioned = true
            view.load(URLRequest(url: target))
            return
        }
        guard status == 200 else { finish(false, "FAIL: landing HTTP \(status)"); return }
        view.evaluateJavaScript("""
            window.__startupQA = null;
            (async () => {
              try {
                const health = await fetch('/api/health');
                const settings = await fetch('/api/settings');
                const onboarding = document.body.dataset.onboarding === 'true';
                const dialog = document.querySelector('#settings-dialog');
                if (!onboarding) document.querySelector('[data-settings-open]')?.click();
                const opened = !!dialog?.open;
                // Set up later persists completion. A startup probe must not
                // dismiss an unfinished wizard or change the user's settings.
                if (!onboarding) document.querySelector('[data-settings-close]')?.click();
                window.__startupQA = {
                  shell: !!document.querySelector('.app-shell'),
                  utf8: document.characterSet === 'UTF-8',
                  health: health.status === 200, settings: settings.status === 200,
                  dialog: opened && (onboarding
                    ? dialog.matches(':modal') && document.querySelector('.app-shell').inert
                    : !dialog.open),
                  cleanURL: !location.search.includes('token=')
                };
              } catch { window.__startupQA = {requestFailed: false}; }
            })(); void 0;
            """) { _, error in
                if error != nil { finish(false, "FAIL: startup JavaScript") }
                self.poll(view)
            }
    }

    func poll(_ view: WKWebView) {
        view.evaluateJavaScript("window.__startupQA") { result, error in
            if error != nil { finish(false, "FAIL: result read") }
            guard let checks = result as? [String: Bool] else {
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) { self.poll(view) }
                return
            }
            let passed = checks.count == 6 && checks.values.allSatisfy { $0 }
            let summary = checks.keys.sorted().map { "\($0)=\(checks[$0]!)" }.joined(separator: ", ")
            if let path = ProcessInfo.processInfo.environment["LOCALBRAIN_QA_SCREENSHOT"], passed {
                view.takeSnapshot(with: nil) { image, error in
                    guard let tiff = image?.tiffRepresentation,
                          let bitmap = NSBitmapImageRep(data: tiff),
                          let png = bitmap.representation(using: .png, properties: [:]) else {
                        finish(false, "FAIL: synthetic WebView snapshot"); return
                    }
                    do { try png.write(to: URL(fileURLWithPath: path)) }
                    catch { finish(false, "FAIL: snapshot output") }
                    finish(passed, "PASS: \(summary)")
                }
            } else {
                finish(passed, "\(passed ? "PASS" : "FAIL"): \(summary)")
            }
        }
    }

    func webView(_ view: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
        finish(false, "FAIL: navigation did not start")
    }
}

let environment = ProcessInfo.processInfo.environment
guard let raw = environment["LOCALBRAIN_START_URL"], let target = URL(string: raw),
      target.scheme == "http", target.host == "127.0.0.1", target.port != nil,
      target.path == "/desktop/start" else {
    finish(false, "Set LOCALBRAIN_START_URL to the isolated loopback desktop handshake URL.")
    fatalError()
}
let application = NSApplication.shared
application.setActivationPolicy(.accessory)
let probe = StartupProbe(target: target)
let configuration = WKWebViewConfiguration()
configuration.websiteDataStore = .nonPersistent()
configuration.setURLSchemeHandler(probe, forURLScheme: "tauri")
let view = WKWebView(frame: NSRect(x: 0, y: 0, width: 1100, height: 800), configuration: configuration)
view.navigationDelegate = probe
let window = NSWindow(contentRect: view.frame, styleMask: [.titled, .closable, .resizable], backing: .buffered, defer: false)
window.title = "LocalBrain synthetic startup check"
window.contentView = view
window.orderFront(nil)
func start() { view.load(URLRequest(url: URL(string: "tauri://localhost/index.html")!)) }
if environment["LOCALBRAIN_QA_STALE_COOKIE"] == "1" {
    let cookie = HTTPCookie(properties: [.domain: "127.0.0.1", .path: "/", .name: "localbrain-desktop", .value: "previous-launch"])!
    configuration.websiteDataStore.httpCookieStore.setCookie(cookie, completionHandler: start)
} else { start() }
DispatchQueue.main.asyncAfter(deadline: .now() + 30) { finish(false, "FAIL: startup timeout") }
application.run()
