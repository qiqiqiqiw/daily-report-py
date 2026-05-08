#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

APP_NAME="GitDailyReport"
DIST_DIR="dist"
BUILD_DIR="build"
DMG_NAME="${APP_NAME}.dmg"

echo "=== Step 1: Clean previous builds ==="
rm -rf "$BUILD_DIR/$APP_NAME" "$DIST_DIR/$APP_NAME.app" "$DIST_DIR/$DMG_NAME"

echo "=== Step 2: Convert icon to .icns ==="
ICONSET_DIR="$BUILD_DIR/AppIcon.iconset"
mkdir -p "$ICONSET_DIR"

for size in 16 32 64 128 256 512; do
    sips -z "$size" "$size" static/app.ico --out "$ICONSET_DIR/icon_${size}x${size}.png" 2>/dev/null || true
    double=$((size * 2))
    if [ "$double" -le 1024 ]; then
        sips -z "$double" "$double" static/app.ico --out "$ICONSET_DIR/icon_${size}x${size}@2x.png" 2>/dev/null || true
    fi
done

ICNS_FILE="$BUILD_DIR/AppIcon.icns"
if command -v iconutil &>/dev/null; then
    iconutil -c icns "$ICONSET_DIR" -o "$ICNS_FILE" 2>/dev/null || true
fi

echo "=== Step 3: Run PyInstaller ==="
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

python -m pip install pyinstaller Pillow --quiet 2>/dev/null || true

python -m PyInstaller daily-report.spec \
    --noconfirm \
    --clean \
    --distpath "$DIST_DIR" \
    --workpath "$BUILD_DIR"

echo "=== Step 4: Create data directory ==="
APP_MACOS_DIR="$DIST_DIR/$APP_NAME.app/Contents/MacOS"
mkdir -p "$APP_MACOS_DIR/data"

echo "=== Step 5: Create DMG ==="
DMG_STAGING="$BUILD_DIR/dmg-staging"
rm -rf "$DMG_STAGING"
mkdir -p "$DMG_STAGING"

cp -R "$DIST_DIR/$APP_NAME.app" "$DMG_STAGING/"
ln -s /Applications "$DMG_STAGING/Applications"

hdiutil create -volname "$APP_NAME" \
    -srcfolder "$DMG_STAGING" \
    -ov -format UDZO \
    "$DIST_DIR/$DMG_NAME"

echo ""
echo "=== Build complete ==="
echo "  App bundle: $DIST_DIR/$APP_NAME.app"
echo "  DMG image:  $DIST_DIR/$DMG_NAME"
