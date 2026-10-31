#!/usr/bin/env python3
"""Render the real menu with example profiles in an isolated offscreen window."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

project = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='pi-profiles-screenshots-') as directory:
    root = Path(directory)
    for module in ('Ui', 'Commons'):
        (root / module).symlink_to(Path('/usr/share/omarchy/shell') / module, target_is_directory=True)
    (root / 'plugin').mkdir()
    (root / 'runtime').mkdir(mode=0o700)
    (root / 'home').mkdir()
    shutil.copy2(project / 'pi-logo.svg', root / 'plugin/pi-logo.svg')
    source = (project / 'Panel.qml').read_text()
    source = source.replace('    id: root\n', '''    id: root
    readonly property real previewWidth: popup.contentWidth
    readonly property real previewHeight: content.implicitHeight
    component PreviewPanel: Item {
        property var anchorItem
        property var owner
        property var bar
        property bool open
        property Item focusTarget
        property real padding
        property real contentWidth
        property real contentHeight
        width: contentWidth
        height: contentHeight
        function fittedContentWidth(value) { return value }
        function fittedContentHeight(value, maximum) { return value }
    }
''', 1)
    source = source.replace('    KeyboardPanel {', '    PreviewPanel {', 1)
    source = source.replace('function refresh() { execute("list", "") }', 'function refresh() {}')
    source = source.replace('        id: button\n', '        id: button\n        visible: false\n', 1)
    (root / 'plugin/Panel.qml').write_text(source)
    (root / 'shell.qml').write_text('''
import QtQuick
import QtQuick.Window
import Quickshell
import qs.Commons
import qs.Commons as Commons
ShellRoot {
    Component.onCompleted: {
        Commons.Color.background = "#1e1e2e"
        Commons.Color.foreground = "#cdd6f4"
        Commons.Color.accent = "#89b4fa"
        Commons.Color.urgent = "#f38ba8"
        Style.fontFamily = "JetBrainsMono Nerd Font"
        Style.fontBaseSize = 14
    }
    Window {
        visible: true
        width: panel.width
        height: panel.height
        color: "transparent"
        Rectangle {
            id: panel
            width: plugin.item ? plugin.item.previewWidth + 28 : 328
            height: plugin.item ? plugin.item.previewHeight + 28 : 200
            color: Commons.Color.background
            border.color: Commons.Color.accent
            border.width: 1
            Loader {
                id: plugin
                x: 14; y: 14
                source: "plugin/Panel.qml"
                onLoaded: {
                    item.loaded = true
                    item.profiles = [
                        {name: "work", path: "~/.pi/profiles/work", isDefault: true},
                        {name: "personal", path: "~/.pi/profiles/personal", isDefault: false},
                        {name: "experiments", path: "~/.pi/profiles/experiments", isDefault: false}
                    ]
                    if (Quickshell.env("PI_SCREENSHOT_SCENE") === "confirmation") item.pendingRemove = "experiments"
                }
            }
        }
        Timer {
            interval: 500; running: true
            onTriggered: panel.grabToImage(function(result) {
                if (result.saveToFile(Quickshell.env("PI_SCREENSHOT_OUTPUT"))) console.log("SCREENSHOT_SAVED")
                Qt.quit()
            }, Qt.size(panel.width * 2, panel.height * 2))
        }
    }
}
''')
    env = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QPA_PLATFORMTHEME='',
               QT_QUICK_BACKEND='software', HOME=str(root / 'home'),
               XDG_CONFIG_HOME=str(root / 'home/config'), XDG_RUNTIME_DIR=str(root / 'runtime'))
    env.pop('WAYLAND_DISPLAY', None)
    for scene in ('profiles', 'confirmation'):
        destination = project / 'docs/screenshots' / (scene + '.png')
        destination.parent.mkdir(parents=True, exist_ok=True)
        env.update(PI_SCREENSHOT_SCENE=scene, PI_SCREENSHOT_OUTPUT=str(destination))
        result = subprocess.run(['quickshell', '-p', str(root / 'shell.qml')], env=env,
                                capture_output=True, text=True, timeout=10)
        output = result.stdout + result.stderr
        if result.returncode or 'SCREENSHOT_SAVED' not in output or 'WARN scene:' in output:
            raise SystemExit(output)
        print('Rendered', destination.relative_to(project))
