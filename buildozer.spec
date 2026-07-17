[app]

# Informasi aplikasi
title = ZIGZAG_FIBO
package.name = zigzagfibo
package.domain = com.zigzagfibo

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 1.0

# Entry point
entrypoint = main.py

# Dependensi Python
requirements = python3,kivy==2.3.0,requests,websocket-client,certifi,charset-normalizer,idna,urllib3,plyer

# Orientasi
orientation = portrait

# Android permission
android.permissions = INTERNET,FOREGROUND_SERVICE,RECEIVE_BOOT_COMPLETED,VIBRATE,POST_NOTIFICATIONS

# Minimum Android SDK
android.minapi = 21
android.api = 33
android.ndk = 25b
android.ndk_api = 21

# NDK
android.archs = arm64-v8a, armeabi-v7a

# Ikon & splash (opsional, bisa dikosongkan)
#icon.filename = %(source.dir)s/icon.png
#presplash.filename = %(source.dir)s/presplash.png

android.allow_backup = True

# Fullscreen
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1
