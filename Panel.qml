import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Commons as Commons
import qs.Ui

Panel {
    id: root
    moduleName: "ianzano.pi-profiles"
    ipcTarget: moduleName
    property var profiles: []
    property string pendingRemove: ""
    property string message: ""
    property bool failed: false
    property bool loaded: false
    readonly property bool busy: worker.running
    readonly property string defaultName: {
        var current = profiles.find(p => p.isDefault)
        return current ? current.name : ""
    }
    readonly property string bridge: decodeURIComponent(Qt.resolvedUrl("backend.py").toString().replace(/^file:\/\//, ""))
    implicitWidth: button.implicitWidth
    implicitHeight: button.implicitHeight

    function execute(action, name) {
        if (busy) return
        message = ""
        failed = false
        worker.action = action
        worker.received = false
        worker.command = ["python3", bridge, action].concat(name ? [name] : [])
        worker.running = true
    }
    function refresh() { execute("list", "") }
    Component.onCompleted: refresh()
    onOpenedChanged: {
        pendingRemove = ""
        if (opened) refresh()
    }
    Timer { interval: 10000; repeat: true; running: true; onTriggered: root.refresh() }
    Process {
        id: worker
        property string action: "list"
        property bool received: false
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    var result = JSON.parse(text)
                    worker.received = true
                    root.failed = !result.ok
                    root.message = result.message || ""
                    if (result.ok && result.profiles !== undefined) {
                        root.profiles = result.profiles
                        root.loaded = true
                        if (!root.profiles.some(p => p.name === root.pendingRemove)) root.pendingRemove = ""
                    }
                    if (result.ok && worker.action === "launch") root.close()
                } catch (error) {
                    root.failed = true
                    root.message = "Could not read profile information: " + error
                }
            }
        }
        stderr: StdioCollector {
            onStreamFinished: if (text.trim()) { root.failed = true; root.message = text.trim() }
        }
        onExited: function(code, status) {
            if (code !== 0 && !root.failed) { root.failed = true; root.message = "Profile command failed (" + code + ")" }
        }
    }
    WidgetButton {
        id: button
        anchors.fill: parent
        bar: root.bar
        labelVisible: false
        hasVisualContent: true
        implicitWidth: vertical ? barSize : Style.space(28)
        tooltipText: "Pi Profiles" + (root.defaultName ? " · Default: " + root.defaultName : " · No default")
        Image {
            anchors.centerIn: parent
            width: Style.space(20); height: width
            source: Qt.resolvedUrl("pi-logo.svg")
            sourceSize: Qt.size(width, height)
            fillMode: Image.PreserveAspectFit
        }
        onPressed: function(code) { if (code === Qt.MiddleButton) root.refresh(); else root.toggle() }
    }
    component Action: Controls.Button {
        id: action
        property bool danger: false
        property bool selected: false
        property string tooltipText: ""
        property bool iconOnly: false
        font.family: Style.font.family
        font.pixelSize: iconOnly ? Style.space(14) : Style.font.caption
        implicitWidth: iconOnly ? Style.space(28) : implicitContentWidth + Style.space(16)
        implicitHeight: Style.space(28)
        padding: 0
        hoverEnabled: true
        HoverHandler { cursorShape: action.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor }
        Accessible.name: tooltipText || text
        Controls.ToolTip.visible: hovered && tooltipText !== ""
        Controls.ToolTip.text: tooltipText
        Controls.ToolTip.delay: 450
        contentItem: Item {
            implicitWidth: glyph.implicitWidth
            implicitHeight: glyph.implicitHeight
            TextMetrics {
                id: metrics
                font: action.font
                text: action.text
            }
            Text {
                id: glyph
                text: action.text
                textFormat: Text.PlainText
                font: action.font
                color: action.danger && (action.hovered || action.activeFocus) ? Commons.Color.urgent : action.selected ? Commons.Color.accent : Commons.Color.foreground
                anchors.centerIn: parent
                // Center the painted icon, excluding its font side bearings and baseline space.
                anchors.horizontalCenterOffset: action.iconOnly
                    ? implicitWidth / 2 - (metrics.tightBoundingRect.x + metrics.tightBoundingRect.width / 2) : 0
                anchors.verticalCenterOffset: action.iconOnly
                    ? implicitHeight / 2 - (baselineOffset + metrics.tightBoundingRect.y + metrics.tightBoundingRect.height / 2) : 0
                opacity: action.enabled || action.selected ? 1 : 0.45
            }
        }
        background: Rectangle {
            radius: Style.space(4)
            color: Util.alpha(action.danger ? Commons.Color.urgent : Commons.Color.accent,
                              action.down ? 0.22 : action.hovered || action.activeFocus ? 0.13 : action.selected ? 0.08 : 0)
            border.width: action.activeFocus ? 1 : 0
            border.color: Commons.Color.accent
        }
    }
    component Caption: Text {
        textFormat: Text.PlainText
        color: Commons.Color.foreground
        font.family: Style.font.family
        font.pixelSize: Style.font.caption
        wrapMode: Text.Wrap
    }
    KeyboardPanel {
        id: popup
        anchorItem: button
        owner: root
        bar: root.bar
        open: root.opened
        focusTarget: content
        padding: Style.space(10)
        contentWidth: fittedContentWidth(Style.space(300))
        contentHeight: fittedContentHeight(content.implicitHeight, Style.space(520))
        Flickable {
            anchors.fill: parent
            clip: true
            contentWidth: width
            contentHeight: content.implicitHeight
            boundsBehavior: Flickable.StopAtBounds
            Controls.ScrollBar.vertical: Controls.ScrollBar {}
            Column {
                id: content
                width: parent.width
                spacing: Style.space(6)
                focus: true
                Keys.onEscapePressed: {
                    if (root.pendingRemove) root.pendingRemove = ""
                    else root.close()
                }
                RowLayout {
                    width: parent.width
                    spacing: Style.space(4)
                    Caption { text: "PROFILES"; font.pixelSize: Style.font.caption; font.letterSpacing: 1.2; opacity: 0.6; Layout.fillWidth: true }
                    Caption { text: root.profiles.length; opacity: 0.4 }
                    Action { text: ""; iconOnly: true; tooltipText: "Refresh profiles"; enabled: !root.busy; onClicked: root.refresh() }
                }
                Caption {
                    width: parent.width
                    visible: root.failed && !!root.message
                    text: root.message
                    color: Commons.Color.urgent
                }
                Caption {
                    visible: !root.profiles.length
                    width: parent.width
                    text: root.loaded ? "No profiles yet. Run ppi create <name> in a terminal." : "Loading…"
                }
                Repeater {
                    model: root.profiles
                    delegate: Rectangle {
                        id: row
                        required property var modelData
                        width: content.width
                        implicitHeight: details.implicitHeight + Style.space(8)
                        radius: Style.space(6)
                        color: Util.alpha(Commons.Color.accent, launchName.hovered || launchName.activeFocus ? 0.10 : row.modelData.isDefault ? 0.045 : 0)
                        Column {
                            id: details
                            anchors { left: parent.left; right: parent.right; top: parent.top; margins: Style.space(4) }
                            spacing: Style.space(6)
                            RowLayout {
                                width: parent.width
                                spacing: Style.space(2)
                                Controls.Button {
                                    id: launchName
                                    Layout.fillWidth: true
                                    Layout.minimumWidth: 0
                                    implicitHeight: Style.space(36)
                                    padding: Style.space(4)
                                    enabled: !root.busy
                                    hoverEnabled: true
                                    HoverHandler { cursorShape: launchName.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor }
                                    Accessible.name: "Launch " + row.modelData.name
                                    Controls.ToolTip.visible: hovered
                                    Controls.ToolTip.text: "New session · " + row.modelData.path
                                    Controls.ToolTip.delay: 450
                                    contentItem: RowLayout {
                                        spacing: Style.space(6)
                                        Caption {
                                            text: row.modelData.name
                                            font.bold: true
                                            Layout.fillWidth: true
                                            Layout.minimumWidth: 0
                                            elide: Text.ElideRight
                                            wrapMode: Text.NoWrap
                                        }
                                        Rectangle {
                                            visible: row.modelData.isDefault
                                            Layout.alignment: Qt.AlignVCenter
                                            implicitWidth: defaultMetrics.tightBoundingRect.width + Style.space(12)
                                            implicitHeight: Style.space(18)
                                            radius: Style.space(4)
                                            color: Util.alpha(Commons.Color.accent, 0.1)
                                            TextMetrics {
                                                id: defaultMetrics
                                                font: defaultLabel.font
                                                text: defaultLabel.text
                                            }
                                            Caption {
                                                id: defaultLabel
                                                anchors.centerIn: parent
                                                anchors.horizontalCenterOffset: implicitWidth / 2 - (defaultMetrics.tightBoundingRect.x + defaultMetrics.tightBoundingRect.width / 2)
                                                anchors.verticalCenterOffset: implicitHeight / 2 - (baselineOffset + defaultMetrics.tightBoundingRect.y + defaultMetrics.tightBoundingRect.height / 2)
                                                text: "Default"
                                                font.pixelSize: Math.max(1, Math.round(Style.font.caption - 1))
                                                color: Commons.Color.accent
                                            }
                                        }
                                    }
                                    background: Item {}
                                    onClicked: root.execute("launch", row.modelData.name)
                                }
                                Action {
                                    objectName: "default-" + row.modelData.name
                                    text: ""; iconOnly: true
                                    tooltipText: "Set as default"
                                    visible: !row.modelData.isDefault
                                    enabled: !root.busy
                                    onClicked: root.execute("set-default", row.modelData.name)
                                }
                                Action {
                                    objectName: "remove-" + row.modelData.name
                                    text: ""; iconOnly: true
                                    tooltipText: "Remove " + row.modelData.name
                                    danger: true; enabled: !root.busy
                                    onClicked: root.pendingRemove = root.pendingRemove === row.modelData.name ? "" : row.modelData.name
                                }
                            }
                            Column {
                                width: parent.width
                                spacing: Style.space(4)
                                visible: root.pendingRemove === row.modelData.name
                                Caption {
                                    width: parent.width
                                    text: "Delete “" + row.modelData.name + "” and its settings and sessions?"
                                          + (row.modelData.isDefault ? " This also clears the default." : "")
                                    color: Commons.Color.urgent
                                }
                                Row {
                                    spacing: Style.space(6)
                                    Action { objectName: "cancel-remove-" + row.modelData.name; text: "Cancel"; onClicked: root.pendingRemove = "" }
                                    Action {
                                        objectName: "confirm-remove-" + row.modelData.name
                                        text: "Delete profile"; danger: true; enabled: !root.busy
                                        onClicked: { var name = root.pendingRemove; root.pendingRemove = ""; root.execute("remove", name) }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
