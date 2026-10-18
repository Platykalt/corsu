#!/bin/bash
# The menu of Discord's notification-area icon in a real Discord desktop app, inside a container: Discord from its public
# download (https://discord.com/api/download?platform=linux&format=tar.gz, extracted to /discord-dl; never anyone's
# installed Discord), a throwaway HOME, never logged in; Vencord built with the Corsu plugin (/corsu/Vencord/dist).
# cdp.py then calls Discord's own NativeUtils.setSystemTrayStrings (patched by the plugin) with the strings Discord's
# page sends in French, since its tray manager only does so after login. The menu is read where Plasma reads it
# (com.canonical.dbusmenu) and photographed open. Discord sends its usual telemetry while it runs.
#   docker run --rm -e WAIT=30 -v "$PWD":/corsu:ro -v <folder with Discord/>:/discord-dl:ro \
#       -v "$PWD"/tests/manual/kde-observe/discord.sh:/discord.sh:ro -v "$PWD"/tests/manual/kde-observe/cdp.py:/cdp.py:ro \
#       -v /tmp/out:/out corsu-kde bash /discord.sh corsu
set -u
TAG=$1; OUT=/out
export HOME=/tmp/home LANG=fr_FR.UTF-8 LANGUAGE=fr LC_ALL=fr_FR.UTF-8 DISPLAY=:99 XDG_RUNTIME_DIR=/tmp/runtime QT_QPA_PLATFORM=xcb
mkdir -p $HOME $XDG_RUNTIME_DIR && chmod 700 $XDG_RUNTIME_DIR
# A fresh Discord from its public download (bootstrap, then the host it downloads), in the throwaway HOME.
cp -a /discord-dl/Discord /tmp/Discord
mkdir -p $HOME/.config/discord
/tmp/Discord/updater_bootstrap --no-zenity $HOME/.config/discord stable https://updates.discord.com/ >/tmp/bootstrap.log 2>&1
echo "bootstrap: $?"
app_dir=$(ls $HOME/.config/discord | grep '^app-' | tail -1)
export D=$HOME/.config/discord/$app_dir
ls $D/resources
mv $D/resources/app.asar $D/resources/_app.asar
if [ "$TAG" != "no-vencord" ]; then
    # The same loader Vencord's installer writes: an app.asar with index.js requiring the patcher.
    python3 - <<'PY'
import json, struct
files = {'index.js': b'require("/corsu/Vencord/dist/patcher.js")', 'package.json': b'{"name":"discord","main":"index.js"}'}
header, offset, data = {'files': {}}, 0, b''
for name, content in files.items():
    header['files'][name] = {'size': len(content), 'offset': str(offset)}
    offset += len(content); data += content
text = json.dumps(header, separators=(',', ':')).encode()
padded = text + b'\0' * (-len(text) % 4)
pickle = struct.pack('<II', len(padded) + 4, len(text)) + padded
open(__import__('os').environ['D'] + '/resources/app.asar', 'wb').write(struct.pack('<II', 4, len(pickle)) + pickle + data)
PY
    mkdir -p $HOME/.config/Vencord/settings
    echo '{"plugins":{"Corsu":{"enabled":true}}}' > $HOME/.config/Vencord/settings/settings.json
else
    mv $D/resources/_app.asar $D/resources/app.asar
fi
Xvfb :99 -screen 0 1280x800x24 >/tmp/xvfb.log 2>&1 &
for i in $(seq 50); do xdpyinfo >/dev/null 2>&1 && break; sleep 0.2; done
eval "$(dbus-launch --sh-syntax)"
/usr/lib/x86_64-linux-gnu/libexec/kglobalacceld >/dev/null 2>&1 &
kwin_x11 --replace >/tmp/kwin.log 2>&1 &
sleep 3
plasmashell >/tmp/plasma.log 2>&1 &
sleep 10
$D/Discord --no-sandbox --disable-gpu --remote-debugging-port=9222 --remote-allow-origins=* >$D.log 2>&1 &
sleep ${WAIT:-60}
# The page: where it is, whether the Corsu plugin runs, and Discord's own NativeUtils (patched by the plugin) called
# with the strings Discord's page sends in French, the way its system tray manager calls it.
python3 /cdp.py 2>&1 | tee $OUT/$TAG-page.txt
sleep 3
python3 - <<'PY' | tee $OUT/$TAG-tray.txt
import gi
from gi.repository import Gio, GLib
bus = Gio.bus_get_sync(Gio.BusType.SESSION)
names = bus.call_sync('org.freedesktop.DBus', '/org/freedesktop/DBus', 'org.freedesktop.DBus', 'ListNames', None, None, 0, -1).unpack()[0]
items = []
try:
    items = bus.call_sync('org.kde.StatusNotifierWatcher', '/StatusNotifierWatcher', 'org.freedesktop.DBus.Properties', 'Get',
                          GLib.Variant('(ss)', ('org.kde.StatusNotifierWatcher', 'RegisteredStatusNotifierItems')), None, 0, -1).unpack()[0]
except Exception as error:
    print('watcher:', error)
print('items:', items)
def labels(node, depth=0):
    _, props, children = node
    if 'label' in props: print('  ' * depth + repr(props['label']) + ('' if props.get('visible', True) else ' (hidden)'))
    for child in children: labels(child, depth + 1)
for item in items:
    service, _, path = item.partition('/')
    path = '/' + path if path else '/StatusNotifierItem'
    try:
        title = bus.call_sync(service, path, 'org.freedesktop.DBus.Properties', 'Get', GLib.Variant('(ss)', ('org.kde.StatusNotifierItem', 'Title')), None, 0, -1).unpack()[0]
        menu = bus.call_sync(service, path, 'org.freedesktop.DBus.Properties', 'Get', GLib.Variant('(ss)', ('org.kde.StatusNotifierItem', 'Menu')), None, 0, -1).unpack()[0]
        print('item', service, path, 'title', repr(title), 'menu', menu)
        layout = bus.call_sync(service, menu, 'com.canonical.dbusmenu', 'GetLayout', GLib.Variant('(iias)', (0, -1, [])), None, 0, -1).unpack()
        labels(layout[1])
    except Exception as error:
        print('item', item, 'error', error)
PY
import -window root $OUT/$TAG-discord.png
# The menu as Plasma draws it: right click on Discord's icon in the notification area (bottom right of the panel).
xdotool mousemove 1047 772 click 3; sleep 2; import -window root $OUT/$TAG-tray-menu.png; xdotool key Escape
grep -v "^$" $D.log | tail -40
