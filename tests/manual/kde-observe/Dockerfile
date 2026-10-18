# KDE Plasma 6 (KWin X11 and Wayland, plasmashell, KRunner) on Xvfb, for tests/manual/kde-observe/*.sh.
# Base: any Debian sid image with Xvfb, xdotool, ImageMagick and WebKitGTK for Python (python3-gi, gir1.2-webkit2-4.1);
# the one used in October 2026 was the local image corsu-redesign-verify.
#   docker build --build-arg BASE=<image> -t corsu-kde tests/manual/kde-observe
ARG BASE=corsu-redesign-verify:latest
FROM ${BASE}
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends kwin-x11 kwin-wayland plasma-workspace plasma-desktop \
    kglobalacceld dbus-x11 x11-utils xauth breeze-icon-theme breeze kde-cli-tools wmctrl python3-gi gir1.2-gtk-3.0 \
    kio qml6-module-org-kde-kirigami plasma-integration && rm -rf /var/lib/apt/lists/*
