#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用名称工具 - 从 .desktop 文件获取应用显示名称
"""

import os
import subprocess
from typing import Optional, Dict, List


class AppNameResolver:
    """应用名称解析器"""

    def __init__(self):
        self.desktop_cache = {}  # filename -> desktop info
        self.name_cache = {}  # package_name -> app_name
        self._initialized = False

    def _ensure_initialized(self):
        """确保已初始化"""
        if not self._initialized:
            self._build_desktop_cache()
            self._initialized = True

    def _build_desktop_cache(self):
        """构建 .desktop 文件缓存"""
        desktop_dirs = [
            '/usr/share/applications',
            '/usr/local/share/applications',
            os.path.expanduser('~/.local/share/applications'),
        ]

        for desktop_dir in desktop_dirs:
            if not os.path.exists(desktop_dir):
                continue

            try:
                for filename in os.listdir(desktop_dir):
                    if filename.endswith('.desktop'):
                        filepath = os.path.join(desktop_dir, filename)
                        desktop_info = self._parse_desktop_file(filepath)
                        if desktop_info:
                            # 使用文件名作为 key（去掉 .desktop 后缀）
                            key = filename[:-8].lower()  # 去掉 .desktop
                            self.desktop_cache[key] = desktop_info
            except Exception as e:
                pass

    def _parse_desktop_file(self, filepath: str) -> Optional[Dict]:
        """解析 .desktop 文件"""
        try:
            info = {
                'name': '',
                'name_zh': '',
                'exec': '',
                'icon': '',
                'filename': os.path.basename(filepath)
            }

            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                in_section = False
                for line in f:
                    line = line.strip()
                    if line == '[Desktop Entry]':
                        in_section = True
                        continue
                    if line.startswith('[') and in_section:
                        break
                    if not in_section:
                        continue
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()

                        if key == 'Name':
                            info['name'] = value
                        elif key == 'Name[zh_CN]':
                            info['name_zh'] = value
                        elif key == 'Exec':
                            exec_parts = value.split()
                            if exec_parts:
                                exec_path = exec_parts[0]
                                if exec_path.startswith('/'):
                                    info['exec'] = exec_path
                                else:
                                    info['exec'] = os.path.basename(exec_path)
                        elif key == 'Icon':
                            info['icon'] = value

            return info if info['name'] else None

        except Exception as e:
            return None

    def get_app_name(self, package_name: str) -> str:
        """
        获取包的启动器名称

        Args:
            package_name: 包名

        Returns:
            启动器名称，如果没有则返回空字符串
        """
        self._ensure_initialized()

        # 先检查缓存
        if package_name in self.name_cache:
            return self.name_cache[package_name]

        pkg_name_lower = package_name.lower().replace('-', '').replace('_', '')

        # 1. 精确匹配 .desktop 文件名
        if pkg_name_lower in self.desktop_cache:
            info = self.desktop_cache[pkg_name_lower]
            app_name = info['name_zh'] or info['name']
            self.name_cache[package_name] = app_name
            return app_name

        # 2. 通过 dpkg 查找 .desktop 文件
        try:
            result = subprocess.run(
                ['dpkg', '-L', package_name],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                files = result.stdout.strip().split('\n')
                for filepath in files:
                    if filepath.endswith('.desktop'):
                        info = self._parse_desktop_file(filepath)
                        if info:
                            app_name = info['name_zh'] or info['name']
                            self.name_cache[package_name] = app_name
                            return app_name
        except:
            pass

        # 3. 检查 .desktop 文件名是否包含包名（需要至少 4 个字符匹配）
        if len(pkg_name_lower) >= 4:
            for key, info in self.desktop_cache.items():
                key_clean = key.replace('-', '').replace('_', '')
                if pkg_name_lower == key_clean:
                    app_name = info['name_zh'] or info['name']
                    self.name_cache[package_name] = app_name
                    return app_name

        # 4. 模糊匹配：检查包名是否是 .desktop 文件名的子串
        if len(pkg_name_lower) >= 3:
            for key, info in self.desktop_cache.items():
                key_clean = key.replace('-', '').replace('_', '')
                if pkg_name_lower in key_clean or key_clean in pkg_name_lower:
                    app_name = info['name_zh'] or info['name']
                    self.name_cache[package_name] = app_name
                    return app_name

        # 5. 使用包名作为显示名称（去掉常见后缀）
        display_name = package_name.replace('-', ' ').replace('_', ' ').title()
        # 检查是否有对应的 desktop 文件使用类似的名称
        for key, info in self.desktop_cache.items():
            desktop_name = info['name'].lower().replace('-', ' ').replace('_', '')
            if display_name.lower().replace(' ', '') == desktop_name:
                self.name_cache[package_name] = info['name_zh'] or info['name']
                return info['name_zh'] or info['name']

        # 没有找到，返回格式化的包名作为显示名称
        self.name_cache[package_name] = display_name
        return display_name

    def get_app_names_batch(self, package_names: List[str]) -> Dict[str, str]:
        """
        批量获取应用名称

        Args:
            package_names: 包名列表

        Returns:
            包名到应用名称的映射
        """
        self._ensure_initialized()

        results = {}
        to_resolve = []

        # 检查缓存
        for name in package_names:
            if name in self.name_cache:
                results[name] = self.name_cache[name]
            else:
                to_resolve.append(name)

        # 解析剩余的
        for name in to_resolve:
            results[name] = self.get_app_name(name)

        return results

    def refresh_cache(self):
        """刷新缓存"""
        self.desktop_cache.clear()
        self.name_cache.clear()
        self._initialized = False
        self._build_desktop_cache()


# 全局解析器实例
app_name_resolver = AppNameResolver()
