#!/usr/bin/env python3
"""Load the real QML and exercise CLI actions against temporary profiles."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

project = Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='pi-profiles-ui-') as directory:
    root = Path(directory)
    for module in ('Ui', 'Commons'):
        (root / module).symlink_to(Path('/usr/share/omarchy/shell') / module, target_is_directory=True)
    (root / 'plugin').mkdir()
    for name in ('Panel.qml', 'backend.py', 'pi-logo.svg'):
        if name == 'Panel.qml':
            source = (project / name).read_text().replace('    id: root\n', '''    id: root
    function testFind(name, node) {
        node = node || content
        if (node.objectName === name) return node
        for (var i = 0; i < node.children.length; i++) {
            var found = testFind(name, node.children[i])
            if (found) return found
        }
        return null
    }
''', 1)
            (root / 'plugin' / name).write_text(source)
        else:
            shutil.copy2(project / name, root / 'plugin' / name)
    profiles = root / 'pi/profiles'
    (profiles / 'work').mkdir(parents=True)
    (profiles / 'personal').mkdir()
    (root / 'shell.qml').write_text('''
import QtQuick
import Quickshell
ShellRoot {
    id: test
    property int stage: 0
    Loader { id: plugin; source: "plugin/Panel.qml" }
    Timer {
        interval: 100; repeat: true; running: true
        onTriggered: {
            var p = plugin.item
            if (!p || p.busy || !p.loaded) return
            if (p.failed) { console.error(p.message); Qt.quit(); return }
            if (test.stage === 0) {
                if (p.profiles.length !== 2 || p.defaultName !== "") throw new Error("initial inventory")
                test.stage = 1
                p.testFind("default-work").clicked()
            } else if (test.stage === 1) {
                if (p.defaultName !== "work") throw new Error("default update")
                test.stage = 2
                p.testFind("remove-work").clicked()
                if (p.pendingRemove !== "work" || p.busy) throw new Error("trash must only request confirmation")
            } else if (test.stage === 2) {
                if (p.profiles.length !== 2 || p.defaultName !== "work") throw new Error("profile changed before confirmation")
                p.testFind("cancel-remove-work").clicked()
                if (p.pendingRemove !== "" || p.busy) throw new Error("cancel must not delete")
                test.stage = 3
            } else if (test.stage === 3) {
                if (p.profiles.length !== 2) throw new Error("cancel removed profile")
                p.testFind("remove-work").clicked()
                p.testFind("confirm-remove-work").clicked()
                test.stage = 4
            } else {
                if (p.defaultName !== "" || p.profiles.length !== 1) throw new Error("delete/default clearing")
                console.log("PI_PROFILES_UI_PASSED")
                Qt.quit()
            }
        }
    }
    Timer { interval: 5000; running: true; onTriggered: Qt.quit() }
}
''')
    env = dict(os.environ, QT_QPA_PLATFORM='wayland', QT_QPA_PLATFORMTHEME='', PPI_PI_ROOT=str(root / 'pi'))
    result = subprocess.run(['quickshell', '-p', str(root / 'shell.qml')], env=env,
                            capture_output=True, text=True, timeout=10)
    output = result.stdout + result.stderr
    if result.returncode or 'PI_PROFILES_UI_PASSED' not in output or 'WARN scene:' in output:
        raise SystemExit(output)
    print('Quickshell confirmation checks passed: trash preserves profile, Cancel preserves profile, explicit confirmation deletes it.')
