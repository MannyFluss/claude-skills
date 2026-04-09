# Plasmoid Reference

## metadata.json (Plasma 6)

```json
{
    "KPlugin": {
        "Id": "com.manny.<name>",
        "Name": "Widget Name",
        "Description": "What it does",
        "Version": "0.1",
        "License": "MIT",
        "Authors": [{"Name": "Manny"}],
        "Category": "System Information"
    },
    "KPackageStructure": "Plasma/Applet",
    "X-Plasma-API-Minimum-Version": "6.0"
}
```

---

## Pure QML widget (polling shell commands)

```qml
import QtQuick 2.0
import QtQuick.Layouts 1.1
import org.kde.plasma.plasmoid 2.0
import org.kde.plasma.plasma5support as P5Support
import "../../../com.manny.base/contents/ui" as Base

PlasmoidItem {
    width: 220; height: 80

    P5Support.DataSource {
        id: executable
        engine: "executable"
        connectedSources: []
        onNewData: function(source, data) {
            myLabel.text = data["stdout"].trim()
            disconnectSource(source)
        }
        function run(cmd) { connectSource(cmd) }
    }

    Timer {
        interval: 10000; running: true; repeat: true; triggeredOnStart: true
        onTriggered: executable.run("some-command --with-args")
        // NEVER use ~ in commands — always /home/manny/
    }

    Base.BaseWidget {
        anchors.fill: parent
        Text { id: myLabel; color: Base.Style.textPrimary; font.pixelSize: Base.Style.fontSizeNormal }
    }
}
```

---

## Base library import

`com.manny.base/contents/ui/qmldir` must exist:
```
module com.manny.base
singleton Style 1.0 Style.qml
BaseWidget 1.0 BaseWidget.qml
```

**Style.qml colors:**
- `Base.Style.background`  → `#1a1b26`
- `Base.Style.surface`     → `#24283b`
- `Base.Style.accent`      → `#7aa2f7`
- `Base.Style.textPrimary` → `#c0caf5`
- `Base.Style.textMuted`   → `#565f89`
- `Base.Style.success`     → `#9ece6a`
- `Base.Style.warning`     → `#e0af68`
- `Base.Style.danger`      → `#f7768e`

**BaseWidget** provides: dark rounded container, ColumnLayout children, `pulseRunning` animation property.

---

## HTTP daemon widget (>30fps, real-time data)

Used for: audio visualizers, anything needing 60-144fps data updates.

**Architecture:**
```
Python daemon (parec/sensor → FFT/processing)
  → ThreadingHTTPServer on 127.0.0.1:PORT
    → GET /      serves visualizer HTML
    → GET /data  serves latest JSON
      → HTML fetch('/data') loop inside requestAnimationFrame
        → WebEngineView in QML
```

**Port assignments (don't reuse):**
- 29401 — audio-in
- 29402 — audio-out
- 29403+ — available for new widgets

**Daemon startup pattern in QML:**
```qml
P5Support.DataSource {
    id: starter; engine: "executable"; connectedSources: []
    function run(cmd) { connectSource(cmd) }
    onNewData: function(source, data) { disconnectSource(source) }
}
Component.onCompleted: {
    starter.run(
        "bash -c 'PIDFILE=/tmp/manny_<name>.pid; " +
        "if [ -f \"$PIDFILE\" ] && kill -0 \"$(cat $PIDFILE)\" 2>/dev/null; then exit 0; fi; " +
        "python3 /home/manny/.local/share/plasma/plasmoids/com.manny.base/scripts/<daemon>.py " +
        "--args &>/dev/null & echo $! > \"$PIDFILE\"'"
    )
}
```

**WebEngineView with cover + retry:**
```qml
Timer { id: retryTimer; interval: 500; repeat: false; onTriggered: webView.reload() }

WebEngineView {
    id: webView
    anchors.fill: parent
    url: "http://127.0.0.1:PORT/"
    backgroundColor: "#1a1b26"
    settings.showScrollBars: false
    settings.javascriptEnabled: true
    onLoadingChanged: function(req) {
        if (req.status === WebEngineLoadingInfo.LoadFailedStatus)  retryTimer.start()
        if (req.status === WebEngineLoadingInfo.LoadSucceededStatus) coverFade.start()
    }
}

Rectangle {
    id: cover; anchors.fill: parent; color: "#1a1b26"; opacity: 1
    NumberAnimation {
        id: coverFade; target: cover; property: "opacity"
        to: 0; duration: 800; easing.type: Easing.InQuad
        onStopped: cover.visible = false
    }
}
```

**HTML fetch loop (no out-of-order responses):**
```javascript
async function fetchLoop() {
    while (true) {
        try {
            const res = await fetch('/data')
            if (res.ok) target = await res.json()
        } catch(_) { await new Promise(r => setTimeout(r, 50)) }
    }
}
fetchLoop()
```

**Lerp pattern (smooth 144fps visuals from slower data):**
```javascript
// In requestAnimationFrame render loop:
const ATTACK = 0.35   // fast rise
const DECAY  = 0.12   // slow fall
current[i] += (target[i] - current[i]) * (current[i] < target[i] ? ATTACK : DECAY)
```

---

## WebSocket widget (wrapping existing app)

Used for: Sensel, any existing Python/Node server using WebSocket.

```qml
WebEngineView {
    url: "file:///home/manny/projects/<AppName>/visualizer.html?widget"
    // HTML auto-reconnects via its own ws.onclose → setTimeout(connect, 2000)
}
```

If the HTML has a side panel to hide in widget mode, add to the HTML:
```javascript
const IS_WIDGET = new URLSearchParams(window.location.search).has('widget')
if (IS_WIDGET) document.getElementById('panel').style.display = 'none'
```

Add `setConfig(cfg)` function to HTML so QML can push Plasma config values.

---

## Config system (settings dialog)

**`contents/config/main.xml`:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<kcfg xmlns="http://www.kde.org/standards/kcfg/1.0">
  <kcfgfile name=""/>
  <group name="General">
    <entry name="myValue" type="Double"><default>1.0</default></entry>
    <entry name="myFlag"  type="Bool"><default>true</default></entry>
  </group>
</kcfg>
```

**`contents/ui/ConfigForm.qml`:**
```qml
import QtQuick 2.0
import QtQuick.Controls 2.5
import QtQuick.Layouts 1.1
import org.kde.kirigami as Kirigami

Kirigami.FormLayout {
    property alias cfg_myValue: mySlider.value   // cfg_ prefix = auto save/load
    property alias cfg_myFlag:  myCheck.checked

    RowLayout {
        Kirigami.FormData.label: "My value:"
        Slider { id: mySlider; from: 0.1; to: 10.0; stepSize: 0.1; implicitWidth: 180 }
        Label  { text: mySlider.value.toFixed(1) }
    }
    CheckBox { id: myCheck; Kirigami.FormData.label: "My flag:"; text: "Enabled" }
}
```

**Reading config in main.qml:**
```qml
Plasmoid.configuration.myValue   // read
Connections {
    target: Plasmoid.configuration
    function onMyValueChanged() { /* react */ }
}
```

---

## Environment

`~/.config/plasma-workspace/env/qml.sh` contains:
```bash
export QML_XHR_ALLOW_FILE_READ=1
```
Required for XHR file reads from QML. Already set — don't remove it.

## Accessing widget settings on desktop

WebEngineView fills the widget so right-click is captured by the browser.
To reach Plasma's Configure dialog: right-click desktop → Unlock Widgets → hover widget → wrench icon.
Or add `anchors.topMargin: 4` to WebEngineView to leave a sliver for the Plasma toolbar.

## Debugging

- `plasmawindowed com.manny.<name>` — test without touching the desktop
- Strip to bare `PlasmoidItem { Rectangle { Text { text: "ok" } } }` to confirm widget loads, then add back
- Kill daemons before testing: `pkill -f audio_daemon.py`
- Daemon PID files live in `/tmp/manny_*.pid`
