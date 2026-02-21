#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
包信息工具 - 获取软件包详细信息
"""

import subprocess
from typing import Optional, Dict


class PackageInfo:
    """包信息工具类"""

    @staticmethod
    def get_apt_info(package_name: str) -> Dict:
        """获取 APT 包信息"""
        info = {
            'name': package_name,
            'version': '未知',
            'size': '未知',
            'description': '',
            'maintainer': '',
            'installed_date': '未知'
        }

        try:
            # 获取包状态
            result = subprocess.run(
                ['dpkg', '-s', package_name],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith('Version:'):
                        info['version'] = line.split(':', 1)[1].strip()
                    elif line.startswith('Description:'):
                        info['description'] = line.split(':', 1)[1].strip().split('.')[0]
                    elif line.startswith('Maintainer:'):
                        info['maintainer'] = line.split(':', 1)[1].strip()
        except Exception as e:
            print(f"获取 APT 信息失败：{e}")

        # 获取大小
        try:
            result = subprocess.run(
                ['dpkg-query', '-W', '-f', '${Installed-Size}', package_name],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                size_kb = int(result.stdout.strip())
                info['size'] = PackageInfo._format_size(size_kb * 1024)
        except:
            pass

        return info

    @staticmethod
    def get_snap_info(package_name: str) -> Dict:
        """获取 Snap 包信息"""
        info = {
            'name': package_name,
            'version': '未知',
            'size': '未知',
            'description': '',
            'publisher': '',
            'installed_date': '未知'
        }

        try:
            result = subprocess.run(
                ['snap', 'info', package_name],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line.startswith('version:'):
                        info['version'] = line.split(':', 1)[1].strip()
                    elif line.startswith('summary:'):
                        info['description'] = line.split(':', 1)[1].strip()
                    elif line.startswith('publisher:'):
                        info['publisher'] = line.split(':', 1)[1].strip()
        except Exception as e:
            print(f"获取 Snap 信息失败：{e}")

        return info

    @staticmethod
    def get_flatpak_info(package_name: str) -> Dict:
        """获取 Flatpak 包信息"""
        info = {
            'name': package_name,
            'version': '未知',
            'size': '未知',
            'description': '',
            'origin': '',
            'installed_date': '未知'
        }

        try:
            result = subprocess.run(
                ['flatpak', 'info', package_name],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line.startswith('Version:'):
                        info['version'] = line.split(':', 1)[1].strip()
                    elif line.startswith('Description:'):
                        info['description'] = line.split(':', 1)[1].strip()
                    elif line.startswith('Origin:'):
                        info['origin'] = line.split(':', 1)[1].strip()
        except Exception as e:
            print(f"获取 Flatpak 信息失败：{e}")

        return info

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """格式化字节大小"""
        if size_bytes == 0:
            return "0 B"

        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0
        size = float(size_bytes)

        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1

        return f"{size:.1f} {units[unit_index]}"

    @staticmethod
    def get_display_name(package_name: str) -> str:
        """获取可读的显示名称"""
        # 替换连字符和下划线为空格，首字母大写
        return package_name.replace('-', ' ').replace('_', ' ').title()
