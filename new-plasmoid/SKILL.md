---
name: new-plasmoid
description: Scaffolds and builds KDE Plasma 6 widgets (plasmoids) for Manny's desktop. Handles pure QML widgets, WebEngineView visualizations, HTTP daemon widgets, and WebSocket wrappers. Use when the user asks to create a new widget, plasmoid, or desktop visualizer, or wants to add something to the KDE desktop.
---

# New Plasmoid

## Key paths
- **Plasmoids**: `~/.local/share/plasma/plasmoids/`
- **Base library**: `~/.local/share/plasma/plasmoids/com.manny.base/`
- **Base scripts**: `~/.local/share/plasma/plasmoids/com.manny.base/scripts/`
- **Projects**: `~/projects/`
- **Test command**: `plasmawindowed com.manny.<name>`
- **Reload all**: `kquitapp6 plasmashell && kstart6 plasmashell`
- **Naming**: always `com.manny.<name>`

## Step 1 — Pick the widget type

| Situation | Type |
|---|---|
| Shows text/data, polls every few seconds | **Pure QML** |
| Needs shell commands to get data | **Pure QML + P5Support** |
| Needs GPU rendering, animations, Canvas2D/WebGL | **WebEngineView** |
| Needs >30fps live data (audio, sensors) | **HTTP daemon + WebEngineView** |
| Wraps an existing app with a WebSocket server | **WebEngineView → ws://localhost** |

## Step 2 — Scaffold

Always create these files:

```
~/.local/share/plasma/plasmoids/com.manny.<name>/
  metadata.json
  contents/
    ui/
      main.qml
    config/              ← only if widget has settings
      main.xml
    ui/
      ConfigForm.qml     ← only if widget has settings
```

See [REFERENCE.md](REFERENCE.md) for every template.

## Step 3 — Critical Plasma 6 rules (never skip)

1. Root of `main.qml` must be **`PlasmoidItem`** — not `Item`, not `Rectangle`
2. Always `import org.kde.plasma.plasmoid 2.0`
3. Shell commands use **`P5Support.DataSource`** — `PlasmaCore.DataSource` was removed in Plasma 6
4. `~` does **not** expand in shell commands — always use `/home/manny/`
5. `metadata.json` uses `"KPackageStructure": "Plasma/Applet"` — not `ServiceTypes`
6. Style/BaseWidget imports use relative path `"../../../com.manny.base/contents/ui"` — needs `qmldir` in base folder to work as singleton

## Step 4 — Test

```bash
plasmawindowed com.manny.<name>
```

If it crashes with no output, the most common causes are:
- Wrong root type (not PlasmoidItem)
- Bad metadata.json format
- Import path wrong

Strip to bare minimum Rectangle first, then add imports back one at a time.
