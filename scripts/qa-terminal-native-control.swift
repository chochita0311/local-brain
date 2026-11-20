// Only drive the explicitly supplied, task-owned app. Never request AX/TCC grants.
import AppKit
import ApplicationServices
import Carbon

enum ProbeError: Error { case failed(String) }
func attribute(_ element: AXUIElement, _ name: String) -> CFTypeRef? {
    var result: CFTypeRef?
    let status = AXUIElementCopyAttributeValue(element, name as CFString, &result)
    guard status == .success else { return nil }
    return result
}
func label(_ element: AXUIElement, _ target: String) -> Bool {
    [kAXTitleAttribute, kAXDescriptionAttribute, kAXHelpAttribute, kAXValueAttribute].contains {
        (attribute(element, $0) as? String)?.contains(target) == true
    }
}
func find(_ root: AXUIElement, target: String, role: String? = nil, eligible: (AXUIElement) -> Bool = {_ in true}) -> AXUIElement? {
    var pending: [(AXUIElement, Int)] = [], visited = 0
    if let windows=attribute(root,kAXWindowsAttribute) as? [AXUIElement] { pending.append(contentsOf:windows.map{($0,0)}) }
    var seen: [AXUIElement] = []
    let deadline = Date().addingTimeInterval(8)
    while let (item, depth) = pending.popLast(), visited < 12000, Date() < deadline {
        if seen.contains(where:{CFEqual($0,item)}) { continue };seen.append(item)
        visited += 1
        if label(item, target), role == nil || (attribute(item, kAXRoleAttribute) as? String) == role, eligible(item) { return item }
        if depth < 32, let children = attribute(item, kAXChildrenAttribute) as? [AXUIElement] {
            pending.append(contentsOf: children.reversed().map { ($0, depth + 1) })
        }
    }
    return nil
}
func sourceID(_ source: TISInputSource) -> String {
    guard let raw = TISGetInputSourceProperty(source, kTISPropertyInputSourceID) else { return "" }
    return Unmanaged<CFString>.fromOpaque(raw).takeUnretainedValue() as String
}
func key(_ code: CGKeyCode, pid: pid_t, shift: Bool = false) throws {
    guard NSWorkspace.shared.frontmostApplication?.processIdentifier == pid else { throw ProbeError.failed("owned app lost focus") }
    for down in [true, false] {
        guard let event = CGEvent(keyboardEventSource: nil, virtualKey: code, keyDown: down) else { throw ProbeError.failed("keyboard event") }
        if shift { event.flags = .maskShift }
        event.postToPid(pid)
        usleep(45000)
    }
}
func ascii(_ value: String, pid: pid_t) throws {
    let codes: [Character: CGKeyCode] = ["a":0,"b":11,"c":8,"d":2,"e":14,"f":3,"g":5,"h":4,"i":34,"j":38,"k":40,"l":37,"m":46,"n":45,"o":31,"p":35,"q":12,"r":15,"s":1,"t":17,"u":32,"v":9,"w":13,"x":7,"y":16,"z":6,"0":29,"1":18,"2":19,"3":20,"4":21,"5":23,"6":22,"7":26,"8":28,"9":25," ":49,"'":39,"\\":42,"/":44,".":47,"-":27,"=":24,",":43,";":41,"[":33,"]":30,"`":50]
    for char in value {
        if char == "\n" { try key(36,pid:pid);continue }
        let lower = Character(String(char).lowercased())
        let base: Character = char == "_" ? "-" : char == "%" ? "5" : lower
        guard let code = codes[base] else { throw ProbeError.failed("unsupported synthetic key") }
        try key(code,pid:pid,shift:char.isUppercase || char == "_" || char == "%")
    }
}
func main() throws -> Int32 {
    let arguments = Array(CommandLine.arguments.dropFirst())
    if arguments == ["frontmost"] { print(NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0);return 0 }
    if arguments == ["launch"] {
        guard let path=ProcessInfo.processInfo.environment["LOCALBRAIN_QA_APP_PATH"],
              let environment=try JSONSerialization.jsonObject(with:FileHandle.standardInput.readDataToEndOfFile()) as? [String:String] else { throw ProbeError.failed("launch scope") }
        let configuration=NSWorkspace.OpenConfiguration()
        configuration.environment=environment;configuration.createsNewApplicationInstance=true
        configuration.addsToRecentItems=false;configuration.activates=true
        var result: NSRunningApplication?, failure: Error?, finished=false
        NSWorkspace.shared.openApplication(at:URL(fileURLWithPath:path),configuration:configuration) { app,error in
            result=app;failure=error;finished=true
        }
        let deadline=Date().addingTimeInterval(30)
        while !finished && Date()<deadline { RunLoop.current.run(until:Date().addingTimeInterval(0.05)) }
        guard let opened=result, failure==nil else { throw ProbeError.failed("LaunchServices open failed") }
        print(opened.processIdentifier);return 0
    }
    guard arguments.count >= 2, let pid = pid_t(arguments[0]), let running = NSRunningApplication(processIdentifier:pid) else { throw ProbeError.failed("owned app not running") }
    let mode = arguments[1]
    if mode == "restore" { _ = running.activate(options:[]);return 0 }
    let environment = ProcessInfo.processInfo.environment
    guard let raw = environment["LOCALBRAIN_QA_APP_PATH"],
          running.executableURL?.standardizedFileURL.path == URL(fileURLWithPath:raw).appendingPathComponent("Contents/MacOS/localbrain-desktop").standardizedFileURL.path else { throw ProbeError.failed("unexpected app executable") }
    guard AXIsProcessTrusted() else { throw ProbeError.failed("AX permission unavailable") }
    if mode == "terminal-ready" {
        guard NSWorkspace.shared.frontmostApplication?.processIdentifier == pid else { throw ProbeError.failed("owned app lost focus") }
        let own = AXUIElementCreateApplication(pid)
        var value: CFTypeRef?
        guard AXUIElementCopyAttributeValue(own,kAXFocusedUIElementAttribute as CFString,&value) == .success,
              let value = value, CFGetTypeID(value) == AXUIElementGetTypeID() else { throw ProbeError.failed("terminal focus unavailable") }
        let focused = value as! AXUIElement
        var owner: pid_t = 0
        guard AXUIElementGetPid(focused,&owner) == .success, owner == pid,
              (attribute(focused,kAXRoleAttribute) as? String) == "AXTextArea",
              (attribute(focused,kAXTitleAttribute) as? String) == "Terminal input" || (attribute(focused,kAXDescriptionAttribute) as? String) == "Terminal input" else { throw ProbeError.failed("owned terminal input not focused") }
        if arguments.count > 2 {
            guard let workspace = find(own,target:arguments[2],role:"AXCheckBox"),
                  (attribute(workspace,kAXValueAttribute) as? NSNumber)?.intValue == 1 else { throw ProbeError.failed("target workspace not selected") }
        }
        return 0
    }
    if mode == "quit" { guard running.terminate() else { throw ProbeError.failed("normal quit refused") };return 0 }
    if !["has","enabled","visible","screenshot-inactive","terminal-ready"].contains(mode) { _ = running.activate(options:[]);usleep(150000) }
    let app = AXUIElementCreateApplication(pid)
    AXUIElementSetMessagingTimeout(app, 2)
    _ = AXUIElementSetAttributeValue(app,"AXEnhancedUserInterface" as CFString,kCFBooleanTrue)
    if mode == "diagnose" {
        var windows: CFTypeRef?
        let status = AXUIElementCopyAttributeValue(app,kAXWindowsAttribute as CFString,&windows)
        let all = CGWindowListCopyWindowInfo([.excludeDesktopElements],kCGNullWindowID) as? [[String:Any]] ?? []
        let owned = all.filter { ($0[kCGWindowOwnerPID as String] as? Int) == Int(pid) }
        let details: [String:Any] = ["active":running.isActive,"hidden":running.isHidden,
            "finishedLaunching":running.isFinishedLaunching,"activationPolicy":running.activationPolicy.rawValue,
            "axWindowsResult":status.rawValue,"axWindowsCount":(windows as? [AXUIElement])?.count ?? -1,
            "windows":owned,"axWindows":(windows as? [AXUIElement] ?? []).map { window -> [String:Any] in
                ["role":attribute(window,kAXRoleAttribute) as? String ?? "?", "equalsApp":CFEqual(app,window),
                 "title":attribute(window,kAXTitleAttribute) as? String ?? "?",
                 "children":(attribute(window,kAXChildrenAttribute) as? [AXUIElement] ?? []).map { attribute($0,kAXRoleAttribute) as? String ?? "?" }]
            }]
        print(String(data:try JSONSerialization.data(withJSONObject:details,options:[.prettyPrinted,.sortedKeys]),encoding:.utf8)!);return 0
    }
    if mode == "dump" {
        var pending: [(AXUIElement,Int)]=[],rows:[[String:String]]=[]
        var seen: [AXUIElement]=[]
        if let windows=attribute(app,kAXWindowsAttribute) as? [AXUIElement] {pending.append(contentsOf:windows.map{($0,0)})}
        while let (element,depth)=pending.popLast(),rows.count<300 {
            if seen.contains(where:{CFEqual($0,element)}) {continue};seen.append(element)
            var row=["role":attribute(element,kAXRoleAttribute) as? String ?? "?","depth":String(depth)]
            for name in [kAXTitleAttribute,kAXDescriptionAttribute,kAXValueAttribute] {
                if let value=attribute(element,name) as? String {row[name]=String(value.prefix(120))}
            }
            rows.append(row)
            if depth<12,let children=attribute(element,kAXChildrenAttribute) as? [AXUIElement] {pending.append(contentsOf:children.reversed().map{($0,depth+1)})}
        }
        print(String(data:try JSONSerialization.data(withJSONObject:rows,options:[.prettyPrinted,.sortedKeys]),encoding:.utf8)!);return 0
    }
    switch mode {
    case "press", "has", "enabled", "set":
        guard arguments.count >= 3, let element = find(app,target:arguments[2],role:arguments.count > 4 ? arguments[4] : nil,eligible:{ item in
            if mode == "press" || mode == "enabled" {
                var actions: CFArray?;return AXUIElementCopyActionNames(item,&actions) == .success && (actions as? [String])?.contains(kAXPressAction) == true
            }
            if mode == "set" { var settable: DarwinBoolean = false;return AXUIElementIsAttributeSettable(item,kAXValueAttribute as CFString,&settable) == .success && settable.boolValue }
            return true
        }) else { throw ProbeError.failed("synthetic control not found") }
        if mode == "has" { return 0 }
        if mode == "enabled" {
            guard (attribute(element,kAXEnabledAttribute) as? Bool) == true else { throw ProbeError.failed("synthetic control disabled") };return 0
        }
        if mode == "set" {
            guard arguments.count > 3, AXUIElementSetAttributeValue(element,kAXValueAttribute as CFString,arguments[3] as CFString) == .success else { throw ProbeError.failed("input update") };return 0
        }
        guard AXUIElementPerformAction(element,kAXPressAction as CFString) == .success else { throw ProbeError.failed("control action") }
    case "close", "minimize":
        guard let windows = attribute(app,kAXWindowsAttribute) as? [AXUIElement], let window = windows.first else { throw ProbeError.failed("owned window missing") }
        if mode == "minimize" {
            guard AXUIElementSetAttributeValue(window,kAXMinimizedAttribute as CFString,kCFBooleanTrue) == .success else { throw ProbeError.failed("minimize") }
        } else {
            guard let button = attribute(window,kAXCloseButtonAttribute) else { throw ProbeError.failed("close button") }
            guard AXUIElementPerformAction(button as! AXUIElement,kAXPressAction as CFString) == .success else { throw ProbeError.failed("close action") }
        }
    case "enter": try key(36,pid:pid)
    case "tab": try key(48,pid:pid)
    case "backtab": try key(48,pid:pid,shift:true)
    case "space": try key(49,pid:pid)
    case "pane-menu": try key(53,pid:pid,shift:true)
    case "up": try key(126,pid:pid)
    case "down": try key(125,pid:pid)
    case "escape": try key(53,pid:pid)
    case "type":
        guard arguments.count > 2 else { throw ProbeError.failed("synthetic text missing") }
        let original = TISCopyCurrentKeyboardInputSource().takeRetainedValue()
        defer { TISSelectInputSource(original) }
        let sources = TISCreateInputSourceList(nil,false).takeRetainedValue() as! [TISInputSource]
        guard let english = sources.first(where:{["com.apple.keylayout.ABC","com.apple.keylayout.US"].contains(sourceID($0))}),
              TISSelectInputSource(english) == noErr else { throw ProbeError.failed("enabled English input source unavailable") }
        usleep(300000)
        try ascii(arguments[2],pid:pid)
    case "ime":
        let original = TISCopyCurrentKeyboardInputSource().takeRetainedValue()
        defer { TISSelectInputSource(original) }
        let sources = TISCreateInputSourceList(nil,false).takeRetainedValue() as! [TISInputSource]
        guard let english = sources.first(where:{["com.apple.keylayout.ABC","com.apple.keylayout.US"].contains(sourceID($0))}),
              let korean = sources.first(where:{sourceID($0) == "com.apple.inputmethod.Korean.2SetKorean"}) else { throw ProbeError.failed("enabled US/Korean input source unavailable") }
        guard TISSelectInputSource(english) == noErr else { throw ProbeError.failed("English input source") };usleep(300000)
        try ascii("printf 'LB_IME_%s\\n' ",pid:pid)
        guard TISSelectInputSource(korean) == noErr else { throw ProbeError.failed("Korean input source") };usleep(300000)
        for code: CGKeyCode in [5,40,1,15,46,3] { try key(code,pid:pid) } // gksrmf → 한글
        try key(49,pid:pid);usleep(100000)
        guard TISSelectInputSource(english) == noErr else { throw ProbeError.failed("input source return") }
        try key(36,pid:pid)
    case "visible":
        let windows = CGWindowListCopyWindowInfo([.optionOnScreenOnly,.excludeDesktopElements],kCGNullWindowID) as? [[String:Any]] ?? []
        guard windows.contains(where:{($0[kCGWindowOwnerPID as String] as? Int)==Int(pid) && ($0[kCGWindowLayer as String] as? Int)==0}) else { throw ProbeError.failed("owned window is hidden") }
    case "screenshot", "screenshot-inactive":
        guard arguments.count == 3, CGPreflightScreenCaptureAccess() else { throw ProbeError.failed("screen capture unavailable") }
        let windows = CGWindowListCopyWindowInfo([.optionOnScreenOnly,.excludeDesktopElements],kCGNullWindowID) as? [[String:Any]] ?? []
        guard let window = windows.filter({($0[kCGWindowOwnerPID as String] as? Int)==Int(pid) && ($0[kCGWindowLayer as String] as? Int)==0}).max(by:{a,b in
            func area(_ item:[String:Any])->Double {let bounds=item[kCGWindowBounds as String] as? [String:Double] ?? [:];return (bounds["Width"] ?? 0)*(bounds["Height"] ?? 0)}
            return area(a)<area(b)
        }),
              let number = window[kCGWindowNumber as String] as? Int else { throw ProbeError.failed("owned visible window missing") }
        let capture = Process();capture.executableURL = URL(fileURLWithPath:"/usr/sbin/screencapture")
        capture.arguments = ["-x","-l",String(number),arguments[2]]
        try capture.run();capture.waitUntilExit();guard capture.terminationStatus==0 else { throw ProbeError.failed("owned capture failed") }
    default: throw ProbeError.failed("unknown action")
    }
    return 0
}
do { exit(try main()) } catch { print("FAIL: \(error)");exit(1) }
