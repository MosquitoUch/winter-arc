#!/usr/bin/env bash
# Baut die Android-App auf GitHub Actions. Alles landet zusätzlich in build.log.
set -euo pipefail
cd "$(dirname "$0")/.."
LOG="$GITHUB_WORKSPACE/build.log"
exec > >(tee -a "$LOG") 2>&1
echo "== npm ci"; npm ci --no-audit --no-fund
echo "== www"; BUILD_ID="${GITHUB_SHA:0:7}" npm run www
echo "== cap sync"; npx cap sync android
echo "== gradle"; cd android && chmod +x gradlew && ./gradlew assembleRelease --no-daemon --stacktrace --warning-mode=summary
cd ..
echo "== Pakete"
mkdir -p "$GITHUB_WORKSPACE/out"
cp android/app/build/outputs/apk/release/app-release.apk "$GITHUB_WORKSPACE/out/winter-arc.apk"
(cd www && zip -qr "$GITHUB_WORKSPACE/out/www.zip" .)
# version.json für die App: Build plus SHA-256 der Zip (der Updater prüft sie)
SUM=$(sha256sum "$GITHUB_WORKSPACE/out/www.zip" | cut -d' ' -f1)
node -e 'const fs=require("fs");const v=JSON.parse(fs.readFileSync("www/version.json","utf8"));v.sha256=process.argv[1];fs.writeFileSync(process.argv[2],JSON.stringify(v)+"\n")' "$SUM" "$GITHUB_WORKSPACE/out/version.json"
cat "$GITHUB_WORKSPACE/out/version.json"
ls -la "$GITHUB_WORKSPACE/out"
