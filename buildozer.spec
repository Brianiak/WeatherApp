[app]

title = EigenerTitel
package.name = eigenesPaket
package.domain = gsog.eigeneDomain

source.dir = src
source.include_exts = py,png,jpg,kv,atlas

version = 0.1
requirements = python3,kivy,plyer,requests,certifi

orientation = portrait
# Permissions required for GPS and network access on Android
android.permissions = INTERNET,ACCESS_COARSE_LOCATION,ACCESS_FINE_LOCATION
fullscreen = 0

# Support 64-bit ARM devices (most modern phones)
android.archs = arm64-v8a

# Android API configuration
android.api = 33
android.minapi = 21
android.ndk = 25b

# Accept SDK license automatically
android.accept_sdk_license = True

# iOS specific
ios.kivy_ios_url = https://github.com/kivy/kivy-ios
ios.kivy_ios_branch = main
ios.ios_deploy_url = https://github.com/phonegap/ios-deploy
ios.ios_deploy_branch = 1.7.0

[buildozer]
log_level = 2
