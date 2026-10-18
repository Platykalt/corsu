#!/bin/sh
# Corsu installed from a release archive on Linux, when the computer has no usable Python, or loses it later.
# POSIX sh only, so it runs where there is no Python at all. It installs into the home folder of whoever runs it:
# run it as an ordinary user of a throwaway container, never on a real account.
#
#   check_standalone.sh install DIR [PART...]   DIR's corsu-linux.tar.gz checked against its .sha256, extracted to a
#                                                temporary folder, installed (PART defaults to firefox), the folder
#                                                deleted; Corsu's own copy of the archive's Python must be kept
#   check_standalone.sh launchers system|bundled Firefox Corsu starts Firefox and the Corsu menu entry starts the
#                                                window, with the system's Python or with Corsu's copy of the bundled one
#   check_standalone.sh update DIR               the installed copy's update.py, started with the menu entry's Python as
#                                                the window does, installs DIR's archive again; nothing left in tmp/
#
# The Python is removed between steps by root, for example (Debian image with Firefox in /opt/firefox):
#   docker run -d --name corsu-standalone -e CORSU_FIREFOX=/opt/firefox -v "$PWD/dist:/archives:ro" -v "$PWD:/work:ro" IMAGE sleep infinity
#   docker exec -u tester corsu-standalone sh /work/tests/e2e/check_standalone.sh install /archives firefox
#   docker exec -u tester corsu-standalone sh /work/tests/e2e/check_standalone.sh launchers system
#   docker exec -u root corsu-standalone apt-get purge -y libpython3.13-stdlib    # python3-minimal stays: unusable
#   docker exec -u tester corsu-standalone sh /work/tests/e2e/check_standalone.sh launchers bundled
#   docker exec -u root corsu-standalone sh -c "apt-get purge -y 'python3*' 'libpython3*'"
#   docker exec -u tester corsu-standalone sh /work/tests/e2e/check_standalone.sh update /archives
#   docker exec -u tester corsu-standalone sh /work/tests/e2e/check_standalone.sh launchers bundled
set -u
data=$HOME/.local/share/corsu
entry=$HOME/.local/share/applications/corsu-setup.desktop

check() {
    if [ "$1" = 0 ]; then echo "PASS: $2"; else echo "FAIL: $2" >&2; exit 1; fi
}

menu_command() {
    sed -n 's/^Exec=//p' "$entry" | head -n 1
}

case "${1:-}" in
install)
    archives=$2
    shift 2
    [ $# -gt 0 ] || set -- firefox
    download=$(mktemp -d "${TMPDIR:-/tmp}/corsu-download.XXXXXX")
    cp "$archives/corsu-linux.tar.gz" "$archives/corsu-linux.tar.gz.sha256" "$download/"
    (cd "$download" && sha256sum -c corsu-linux.tar.gz.sha256 >/dev/null)
    check $? 'the archive matches its .sha256'
    tar xzf "$download/corsu-linux.tar.gz" -C "$download"
    "$download/corsu/Install for Linux.sh" --text --yes --components "$@" >"$download.log" 2>&1
    status=$?
    tail -n 5 "$download.log"
    check $status "installed: $*"
    rm -rf "$download" "$download.log"
    check $? 'the extracted archive and the download are deleted'
    ls "$data"/runtime/*/python/bin/python3 >/dev/null 2>&1
    check $? "Corsu's copy of the archive's Python is kept"
    ;;
launchers)
    expected=$2
    set -- $(menu_command)
    python=$(cd / && "$1" -c 'import sys; print(sys.executable)' 2>/dev/null)
    echo "the menu entry starts $1, which runs ${python:-nothing}"
    case "$python" in
        "$data"/runtime/*) found=bundled ;;
        '') found=none ;;
        *) found=system ;;
    esac
    [ "$found" = "$expected" ]
    check $? "Corsu runs on the $expected Python"
    version=$(timeout 300 "$HOME/.local/bin/firefox-corsu" --version 2>/dev/null)
    check $? "Firefox Corsu starts Firefox: $version"
    log=$(mktemp)
    setsid "$@" >"$log" 2>&1 &
    app=$!
    address=
    for _ in $(seq 1 60); do
        address=$(sed -n 's|.*\(http://localhost:[0-9]*/\).*|\1|p' "$log" | head -n 1)
        [ -n "$address" ] && break
        sleep 1
    done
    code=$(curl -s -o /dev/null -w '%{http_code}' "$address" 2>/dev/null)
    kill -TERM -"$app" 2>/dev/null
    rm -f "$log"
    [ "$code" = 200 ]
    check $? "the Corsu menu entry starts the window (${address:-no address}, HTTP $code)"
    ;;
update)
    archives=$2
    set -- $(menu_command)
    copy=$(dirname "$(dirname "$2")")
    result=$(cd / && CORSU_DOWNLOAD_BASE="file://$archives" "$1" "$copy/src/update.py" --install 2>&1 | sed -n 's/^@result //p')
    echo "$result"
    case "$result" in *'"corsu": "failed"'*|'') false ;; *) true ;; esac
    check $? 'the installed update.py installed the archive'
    [ -z "$(ls -A "$data/tmp" 2>/dev/null)" ]
    check $? 'no download left in the data folder'
    ;;
*)
    sed -n '2,/^set -u/p' "$0" | sed '$d'
    exit 2
    ;;
esac
