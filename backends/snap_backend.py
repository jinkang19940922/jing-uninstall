#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Snap 后端 - 处理 Snap 包管理相关操作
"""

import subprocess
import re
from typing import Optional, Tuple, List


class SnapBackend:
    """Snap 包管理后端"""

    def __init__(self):
        pass

    def is_installed(self) -> bool:
        """检查系统是否安装了 Snap"""
        try:
            result = subprocess.run(
                ['which', 'snap'],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except:
            return False

    def list_installed(self) -> List[dict]:
        """列出已安装的 Snap 包"""
        packages = []
        try:
            result = subprocess.run(
                ['snap', 'list'],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                # 跳过标题行
                for line in lines[1:]:
                    if not line.strip():
                        continue
                    parts = line.split()
                    if len(parts) >= 5:
                        packages.append({
                            'name': parts[0],
                            'version': parts[1],
                            'rev': parts[2],
                            'publisher': parts[3],
                            'notes': parts[4] if len(parts) > 4 else ''
                        })
        except Exception as e:
            print(f"Snap 列表获取失败：{e}")
        return packages

    def get_info(self, package_name: str) -> dict:
        """获取 Snap 包详细信息"""
        info = {
            'name': package_name,
            'version': '未知',
            'size': '未知',
            'publisher': '未知',
            'description': '',
            'install_date': '未知'
        }

        try:
            result = subprocess.run(
                ['snap', 'info', package_name],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                output = result.stdout
                for line in output.split('\n'):
                    line = line.strip()
                    if line.startswith('version:'):
                        info['version'] = line.split(':', 1)[1].strip()
                    elif line.startswith('summary:'):
                        info['description'] = line.split(':', 1)[1].strip()
                    elif line.startswith('publisher:'):
                        info['publisher'] = line.split(':', 1)[1].strip()
                    elif line.startswith('installed:'):
                        parts = line.split()
                        if len(parts) >= 2:
                            info['size'] = parts[1]
                        # 尝试获取安装日期
                        info['install_date'] = self._parse_snap_date(package_name)
        except Exception as e:
            print(f"Snap 信息获取失败：{e}")

        return info

    def _parse_snap_date(self, package_name: str) -> str:
        """尝试解析 Snap 包安装日期"""
        try:
            # 从 snap changes 获取
            result = subprocess.run(
                ['snap', 'changes', package_name],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    # 获取最后一行（最新的变更）
                    last_line = lines[-1]
                    parts = last_line.split()
                    if len(parts) >= 3:
                        # 格式：2024-01-15T10:30:45+08:00
                        date_str = parts[2].split('T')[0]
                        return date_str
        except:
            pass
        return "未知"

    def remove(self, package_name: str) -> Tuple[bool, str]:
        """
        移除 Snap 包

        Args:
            package_name: 包名

        Returns:
            (成功标志，消息)
        """
        try:
            result = subprocess.run(
                ['sudo', 'snap', 'remove', package_name],
                capture_output=True, text=True, timeout=300
            )

            if result.returncode == 0:
                return True, f"{package_name} 已成功卸载"
            else:
                return False, result.stderr or result.stdout

        except subprocess.TimeoutExpired:
            return False, "卸载超时"
        except Exception as e:
            return False, f"卸载失败：{str(e)}"

    def get_residual_files(self, package_name: str) -> List[str]:
        """获取 Snap 包的残留文件"""
        files = []

        # Snap 的数据目录
        data_dirs = [
            f"/var/snap/{package_name}",
            f"/root/snap/{package_name}",
        ]

        # 检查用户目录
        import os
        home = os.path.expanduser('~')
        data_dirs.append(f"{home}/snap/{package_name}")

        for dir_path in data_dirs:
            if os.path.exists(dir_path):
                files.append(dir_path)

        return files

    def clean_residual(self, package_name: str) -> Tuple[bool, str]:
        """清理 Snap 包的残留文件"""
        try:
            files = self.get_residual_files(package_name)
            for file_path in files:
                try:
                    import shutil
                    shutil.rmtree(file_path)
                except Exception as e:
                    print(f"清理 {file_path} 失败：{e}")
            return True, "残留清理完成"
        except Exception as e:
            return False, f"清理失败：{str(e)}"
