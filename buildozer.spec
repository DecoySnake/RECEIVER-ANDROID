[app]

title = RECEIVER
package.name = receiver
package.domain = org.decoysnake

source.dir = .
source.include_exts = py,png,jpg,jpeg,ogg,wav,mp3,ttf,json
source.exclude_dirs = .git,.github,bin,.buildozer,__pycache__

version = 1.0.0

# SDL2/Pygame-style Android build.
requirements = python3,pygame-ce
orientation = portrait
fullscreen = 1

# No special Android permissions are needed by RECEIVER.
android.permissions =

# Build a modern Android APK.
android.api = 35
android.minapi = 24
android.archs = arm64-v8a

android.accept_sdk_license = True
android.debug_artifact = apk
android.release_artifact = apk

# SDL2 is the appropriate bootstrap for this type of graphical app.
p4a.bootstrap = sdl2
p4a.branch = master

[buildozer]

log_level = 2
warn_on_root = 1
