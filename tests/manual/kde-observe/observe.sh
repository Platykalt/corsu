#!/bin/bash
# Corsu's window in KDE Plasma 6, inside a container: KWin X11, or KWin Wayland nested in an X11 window, on Xvfb; a
# throwaway HOME; Corsu from $CODE (read-only), its menu entry written by corsu.setup_shortcut. Writes to /out/$TAG-*:
# the desktop (title bar, taskbar), Alt+Tab (KWin's switcher, with a second program), KRunner searching "Corsu", and
# KWin's own view of each window (resourceClass, the desktop entry it associated: desktopFileName).
#   docker run --rm -v "$PWD":/corsu:ro -v "$PWD"/tests/manual/kde-observe/observe.sh:/observe.sh:ro -v /tmp/out:/out \
#       corsu-kde bash /observe.sh wayland /corsu after-wayland      (or: x11 ...)
set -u
MODE=$1; CODE=$2; TAG=$3; OUT=/out
export HOME=/tmp/home LANG=C.UTF-8 LC_ALL=C.UTF-8 DISPLAY=:99 XDG_RUNTIME_DIR=/tmp/runtime
mkdir -p $HOME $XDG_RUNTIME_DIR && chmod 700 $XDG_RUNTIME_DIR
Xvfb :99 -screen 0 1280x800x24 >/tmp/xvfb.log 2>&1 &
for i in $(seq 50); do xdpyinfo >/dev/null 2>&1 && break; sleep 0.2; done
eval "$(dbus-launch --sh-syntax)"
python3 -c "import sys; sys.path.insert(0, '$CODE/src'); import corsu; corsu.setup_shortcut(corsu.Installer())"
entry=$(ls $HOME/.local/share/applications/*.desktop)
echo "== entry $entry"; grep -E '^(Exec|Icon|StartupWMClass)=' $entry
kbuildsycoca6 >/tmp/sycoca.log 2>&1
# A second program, so that the window switcher has two windows to show.
cat > /tmp/other.py <<'PY'
import gi; gi.require_version('Gtk', '3.0')
from gi.repository import GLib
GLib.set_prgname('other-program')
from gi.repository import Gtk
w = Gtk.Window(title='Other program'); w.set_default_size(500, 300); w.connect('destroy', Gtk.main_quit); w.show_all(); Gtk.main()
PY
if [ "$MODE" = wayland ]; then
    cp /usr/bin/kwin_wayland /tmp/kwin_wayland  # the copy drops its file capabilities, which a container refuses
    /tmp/kwin_wayland --x11-display :99 --socket wayland-1 --width 1280 --height 800 --no-lockscreen >/tmp/kwin.log 2>&1 &
    for i in $(seq 50); do [ -S $XDG_RUNTIME_DIR/wayland-1 ] && break; sleep 0.2; done
    export WAYLAND_DISPLAY=wayland-1 QT_QPA_PLATFORM=wayland GDK_BACKEND=wayland
    sleep 3
else
    export QT_QPA_PLATFORM=xcb GDK_BACKEND=x11
    /usr/lib/x86_64-linux-gnu/libexec/kglobalacceld >/tmp/kglobalaccel.log 2>&1 &
    sleep 1
    kwin_x11 --replace >/tmp/kwin.log 2>&1 &
    sleep 4
fi
plasmashell >/tmp/plasma.log 2>&1 &
sleep 12
python3 /tmp/other.py >/tmp/other.log 2>&1 &
sleep 2
exec_line=$(grep '^Exec=' $entry | cut -d= -f2-)
eval "$exec_line" >/tmp/corsu.log 2>&1 &
sleep 14
cat > /tmp/dump.js <<'JS'
for (const w of workspace.windowList()) if (w.normalWindow)
    print("KWIN caption=" + w.caption + " resourceClass=" + w.resourceClass + " desktopFileName=" + w.desktopFileName);
JS
qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.loadScript /tmp/dump.js dump >/dev/null
qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.start >/dev/null
sleep 2
grep -o 'KWIN .*' /tmp/kwin.log | sort -u | tee $OUT/$TAG-kwin.txt
if [ "$MODE" = x11 ]; then
    id=$(xdotool search --class corsu 2>/dev/null | tail -1)
    [ -n "$id" ] && xprop -id "$id" WM_CLASS | tee -a $OUT/$TAG-kwin.txt
    [ -n "$id" ] && echo "_NET_WM_ICON sizes: $(xprop -id "$id" _NET_WM_ICON | grep -o 'Icon ([0-9]* x [0-9]*)' | tr '\n' ' ')" | tee -a $OUT/$TAG-kwin.txt
fi
import -window root $OUT/$TAG-desktop.png
# Alt+Tab held: KWin's window switcher.
xdotool mousemove 640 400; xdotool keydown alt; sleep 0.3; xdotool key Tab; sleep 1.5
import -window root $OUT/$TAG-alt-tab.png
xdotool keyup alt; sleep 1
# The applications menu's search (KRunner), for "Corsu".
krunner >/tmp/krunner.log 2>&1 &
sleep 4
qdbus6 org.kde.krunner /App org.kde.krunner.App.query Corsu >/dev/null
sleep 4
import -window root $OUT/$TAG-search.png
echo "== corsu log"; tail -3 /tmp/corsu.log
