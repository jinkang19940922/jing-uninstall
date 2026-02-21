#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AppImage 后端 - 处理 AppImage 文件相关操作
"""

import os
import subprocess
from typing import Optional, Tuple, List


class AppImageBackend:
    """AppImage 后端"""

    # 常见的 AppImage 存放目录
    SEARCH_PATHS = [
        os.path.expanduser("~/Applications"),
        os.path.expanduser("~/.local/bin"),
        os.path.expanduser("~/bin"),
        "/opt",
        "/usr/local/bin",
        "/usr/bin",
    ]

    def __init__(self):
        pass

    def find_appimages(self) -> List[dict]:
        """查找系统中的 AppImage 文件"""
        appimages = []

        for search_path in self.SEARCH_PATHS:
            if not os.path.exists(search_path):
                continue

            try:
                for filename in os.listdir(search_path):
                    if filename.lower().endswith('.appimage'):
                        filepath = os.path.join(search_path, filename)
                        stat_info = os.stat(filepath)

                        appimages.append({
                            'name': self._parse_name(filename),
                            'filename': filename,
                            'path': filepath,
                            'size': stat_info.st_size,
                            'size_str': self._format_size(stat_info.st_size),
                            'modified': self._timestamp_to_date(stat_info.st_mtime),
                            'executable': os.access(filepath, os.X_OK)
                        })
            except PermissionError:
                pass
            except Exception as e:
                print(f"扫描 {search_path} 失败：{e}")

        return appimages

    def _parse_name(self, filename: str) -> str:
        """从文件名解析应用名称"""
        # 移除 .AppImage 后缀
        name = filename
        if name.lower().endswith('.appimage'):
            name = name[:-9]

        # 替换连字符和下划线为空格
        name = name.replace('-', ' ').replace('_', ' ')

        # 尝试提取版本号和架构
        parts = name.split()
        clean_parts = []
        for part in parts:
            # 跳过纯版本号或架构
            if not (part.replace('.', '').isdigit() or
                    part in ['x86_64', 'amd64', 'arm64', 'aarch64', 'i386']):
                clean_parts.append(part)

        return ' '.join(clean_parts) if clean_parts else name

    def _format_size(self, size_bytes: int) -> str:
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

    def _timestamp_to_date(self, timestamp: float) -> str:
        """将时间戳转换为日期字符串"""
        from datetime import datetime
        try:
            return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
        except:
            return "未知"

    def remove(self, filepath: str) -> Tuple[bool, str]:
        """
        删除 AppImage 文件

        Args:
            filepath: 文件路径

        Returns:
            (成功标志，消息)
        """
        if not os.path.exists(filepath):
            return False, f"文件不存在：{filepath}"

        try:
            # 尝试直接删除
            if os.access(filepath, os.W_OK):
                os.remove(filepath)
                return True, f"{os.path.basename(filepath)} 已删除"
            else:
                # 需要 sudo 权限
                result = subprocess.run(
                    ['sudo', 'rm', '-f', filepath],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    return True, f"{os.path.basename(filepath)} 已删除"
                else:
                    return False, f"删除失败：{result.stderr}"
        except Exception as e:
            return False, f"删除失败：{str(e)}"

    def get_residual_files(self, filepath: str) -> List[str]:
        """获取 AppImage 的残留文件"""
        files = []
        app_name = self._parse_name(os.path.basename(filepath))

        # 可能的残留位置
        residual_paths = [
            os.path.expanduser(f"~/.local/share/{app_name}"),
            os.path.expanduser(f"~/.local/share/applications/{app_name}.desktop"),
            os.path.expanduser(f"~/.config/{app_name}"),
            os.path.expanduser(f"~/.cache/{app_name}"),
            f"/tmp/.mount_{os.path.basename(filepath)}",
        ]

        # 检查用户目录下的相关文件
        home = os.path.expanduser('~')

        # 检查 .local/share/applications/ 中的 desktop 文件
        desktop_dir = os.path.join(home, '.local', 'share', 'applications')
        if os.path.exists(desktop_dir):
            for f in os.listdir(desktop_dir):
                if app_name.lower() in f.lower() and f.endswith('.desktop'):
                    files.append(os.path.join(desktop_dir, f))

        # 检查 .local/share/ 中的目录
        local_share = os.path.join(home, '.local', 'share')
        if os.path.exists(local_share):
            for d in os.listdir(local_share):
                if app_name.lower() in d.lower():
                    files.append(os.path.join(local_share, d))

        # 检查 .config/ 中的目录
        config_dir = os.path.join(home, '.config')
        if os.path.exists(config_dir):
            for d in os.listdir(config_dir):
                if app_name.lower() in d.lower():
                    files.append(os.path.join(config_dir, d))

        # 检查 .cache/ 中的目录
        cache_dir = os.path.join(home, '.cache')
        if os.path.exists(cache_dir):
            for d in os.listdir(cache_dir):
                if app_name.lower() in d.lower():
                    files.append(os.path.join(cache_dir, d))

        return files

    def clean_residual(self, app_name: str) -> Tuple[bool, str]:
        """清理 AppImage 的残留文件"""
        try:
            files = self.get_residual_files(app_name)
            for file_path in files:
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        import shutil
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"清理 {file_path} 失败：{e}")
            return True, "残留清理完成"
        except Exception as e:
            return False, f"清理失败：{str(e)}"

    def make_executable(self, filepath: str) -> bool:
        """使 AppImage 可执行"""
        try:
            os.chmod(filepath, 0o755)
            return True
        except:
            return False
