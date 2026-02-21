#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JingUninstall 安装脚本
"""

import os
import sys
import subprocess


def check_dependencies():
    """检查依赖"""
    missing = []

    # 检查 PyQt6
    try:
        import PyQt6
    except ImportError:
        missing.append('PyQt6')

    # 检查 python-apt
    try:
        import apt
    except ImportError:
        missing.append('python3-apt')

    return missing


def install_dependencies():
    """安装缺失的依赖"""
    missing = check_dependencies()

    if not missing:
        print("✓ 所有依赖已安装")
        return True

    print(f"发现缺失的依赖：{', '.join(missing)}")
    print("正在安装...")

    # 使用 apt 安装
    packages = {
        'PyQt6': 'python3-pyqt6',
        'python3-apt': 'python3-apt'
    }

    apt_packages = [packages.get(m, m) for m in missing]

    try:
        subprocess.run(
            ['sudo', 'apt', 'install', '-y'] + apt_packages,
            check=True
        )
        print("✓ 依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 依赖安装失败：{e}")
        return False


def create_symlink():
    """创建符号链接"""
    src = os.path.abspath(__file__).replace('install.py', 'main.py')
    dst = '/usr/local/bin/jing-uninstall'

    try:
        if os.path.exists(dst):
            os.remove(dst)
        os.symlink(src, dst)
        print(f"✓ 已创建符号链接：{dst}")
        return True
    except Exception as e:
        print(f"✗ 创建符号链接失败：{e}")
        return False


def main():
    """主函数"""
    print("=" * 50)
    print("  JingUninstall 安装程序")
    print("=" * 50)
    print()

    # 检查是否 root
    if os.geteuid() != 0:
        print("⚠️ 需要管理员权限")
        print("请使用 sudo 运行：sudo python3 install.py")
        sys.exit(1)

    # 安装依赖
    if not install_dependencies():
        sys.exit(1)

    # 创建符号链接
    create_symlink()

    print()
    print("=" * 50)
    print("  ✓ 安装完成！")
    print("=" * 50)
    print()
    print("运行方式:")
    print("  1. 命令行：jing-uninstall")
    print("  2. 直接运行：python3 main.py")
    print()


if __name__ == "__main__":
    main()
