# RECEIVER — Android cloud-build folder

This folder is intended to let GitHub build an Android APK for RECEIVER without requiring you to install the Android SDK/NDK locally.

The game code in `main.py` is unchanged from the final Pygame build.

## Easiest route

1. Create a new empty GitHub repository.
2. Upload **everything in this folder**, including the hidden `.github` folder.
3. Make sure the files are on the repository's `main` branch.
4. Open the repository's **Actions** tab.
5. Choose **Build RECEIVER Android APK**.
6. Press **Run workflow**.
7. Wait for the build to finish.
8. Open the completed workflow run.
9. Under **Artifacts**, download **RECEIVER-Android-APK**.
10. Unzip that artifact. The `.apk` inside is the Android installer.

Android may warn that the APK came from outside Google Play. That is normal for a directly downloaded debug APK.

## Files

- `main.py` — final RECEIVER game.
- `buildozer.spec` — Android package configuration.
- `.github/workflows/android.yml` — cloud APK build workflow.
- `.gitignore` — excludes generated build files.

## Important caveat

Pygame Android packaging is less mature than ordinary desktop Pygame packaging. This folder provides a sensible Buildozer/python-for-android SDL2 configuration, but the first GitHub build may expose an Android-specific dependency or pygame-ce recipe issue.

If the Action fails, copy the red error section from the GitHub Actions log back into ChatGPT and it can be adjusted without changing the game itself.

## Current package details

- App title: RECEIVER
- Package: `org.decoysnake.receiver`
- Orientation: portrait
- Architecture: arm64-v8a
- Android minimum API: 24
- Output: debug APK
