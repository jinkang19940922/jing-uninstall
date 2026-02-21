#!/bin/bash
# JingUninstall DEB 打包脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PACKAGE_NAME="jing-uninstall"
VERSION="1.0.0"

echo "======================================"
echo "  JingUninstall DEB 打包工具"
echo "======================================"
echo ""

# 创建构建目录
DEB_BUILD_DIR="$PROJECT_ROOT/debian-build"

echo "[1/5] 清理旧的构建文件..."
rm -rf "$DEB_BUILD_DIR"

echo "[2/5] 创建构建目录..."
mkdir -p "$DEB_BUILD_DIR/opt/$PACKAGE_NAME"
mkdir -p "$DEB_BUILD_DIR/usr/share/applications"
mkdir -p "$DEB_BUILD_DIR/usr/share/icons/hicolor/scalable/apps"

echo "[3/5] 复制项目文件..."
# 从项目根目录复制（不是从 debian-build）
cp -r "$PROJECT_ROOT/core" "$DEB_BUILD_DIR/opt/$PACKAGE_NAME/"
cp -r "$PROJECT_ROOT/ui" "$DEB_BUILD_DIR/opt/$PACKAGE_NAME/"
cp -r "$PROJECT_ROOT/backends" "$DEB_BUILD_DIR/opt/$PACKAGE_NAME/"
cp -r "$PROJECT_ROOT/utils" "$DEB_BUILD_DIR/opt/$PACKAGE_NAME/"
cp -r "$PROJECT_ROOT/config" "$DEB_BUILD_DIR/opt/$PACKAGE_NAME/"
cp -r "$PROJECT_ROOT/resources" "$DEB_BUILD_DIR/opt/$PACKAGE_NAME/"
cp "$PROJECT_ROOT/main.py" "$DEB_BUILD_DIR/opt/$PACKAGE_NAME/"
cp "$PROJECT_ROOT/resources/jing-uninstall" "$DEB_BUILD_DIR/opt/$PACKAGE_NAME/"
chmod +x "$DEB_BUILD_DIR/opt/$PACKAGE_NAME/jing-uninstall"

echo "[4/5] 复制桌面文件和图标..."
cp "$PROJECT_ROOT/resources/jing-uninstall.desktop" "$DEB_BUILD_DIR/usr/share/applications/"
cp "$PROJECT_ROOT/resources/jing-uninstall.svg" "$DEB_BUILD_DIR/usr/share/icons/hicolor/scalable/apps/"

echo "[5/5] 复制 debian 打包文件并构建..."
cp -r "$SCRIPT_DIR/debian" "$DEB_BUILD_DIR/"

cd "$DEB_BUILD_DIR"

# 构建
if command -v debuild >/dev/null 2>&1; then
    debuild -us -uc -b
    echo ""
    echo "======================================"
    echo "  ✓ DEB 包构建完成！"
    echo "======================================"
    echo ""
    echo "  包文件位置：$PROJECT_ROOT/"
    ls -lh "$PROJECT_ROOT"/*.deb 2>/dev/null || echo "  未找到 .deb 文件"
    echo ""
    echo "  安装命令：sudo dpkg -i ${PACKAGE_NAME}_${VERSION}_all.deb"
else
    echo "  错误：未找到 debuild 命令"
    echo "  请安装：sudo apt install debhelper devscripts"
    exit 1
fi
