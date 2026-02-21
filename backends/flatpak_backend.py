#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flatpak 后端 - 处理 Flatpak 包管理相关操作
"""

import subprocess
import os
from typing import Optional, Tuple, List


class FlatpakBackend:
    """Flatpak 包管理后端"""

    def __init__(self):
        pass

    def is_installed(self) -> bool:
        """检查系统是否安装了 Flatpak"""
        try:
            result = subprocess.run(
                ['which', 'flatpak'],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except:
            return False

    def list_installed(self) -> List[dict]:
        """列出已安装的 Flatpak 包"""
        packages = []
        try:
            result = subprocess.run(
                ['flatpak', 'list', '--app', '--columns=application,version,origin,installation'],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if not line.strip():
                        continue
                    parts = line.split('\t')
                    if len(parts) >= 1:
                        packages.append({
                            'name': parts[0],
                            'version': parts[1] if len(parts) > 1 else '未知',
                            'origin': parts[2] if len(parts) > 2 else '未知',
                            'installation': parts[3] if len(parts) > 3 else 'system'
                        })
        except Exception as e:
            print(f"Flatpak 列表获取失败：{e}")
        return packages

    def get_info(self, package_name: str) -> dict:
        """获取 Flatpak 包详细信息"""
        info = {
            'name': package_name,
            'version': '未知',
            'size': '未知',
            'origin': '未知',
            'description': '',
            'install_date': '未知'
        }

        try:
            result = subprocess.run(
                ['flatpak', 'info', package_name],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                output = result.stdout
                for line in output.split('\n'):
                    line = line.strip()
                    if line.startswith('Version:'):
                        info['version'] = line.split(':', 1)[1].strip()
                    elif line.startswith('Description:'):
                        info['description'] = line.split(':', 1)[1].strip()
                    elif line.startswith('Origin:'):
                        info['origin'] = line.split(':', 1)[1].strip()
                    elif line.startswith('Installed:'):
                        parts = line.split()
                        if len(parts) >= 2:
                            info['size'] = f"{parts[1]} {parts[2]}" if len(parts) > 2 else parts[1]
        except Exception as e:
            print(f"Flatpak 信息获取失败：{e}")

        return info

    def remove(self, package_name: str) -> Tuple[bool, str]:
        """
        移除 Flatpak 包

        Args:
            package_name: 包名

        Returns:
            (成功标志，消息)
        """
        try:
            # 先尝试普通卸载
            result = subprocess.run(
                ['flatpak', 'uninstall', '-y', package_name],
                capture_output=True, text=True, timeout=300
            )

            if result.returncode == 0:
                return True, f"{package_name} 已成功卸载"

            # 如果需要 sudo，尝试带 sudo 的命令
            result = subprocess.run(
                ['sudo', 'flatpak', 'uninstall', '-y', package_name],
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
        """获取 Flatpak 包的残留文件"""
        files = []

        # Flatpak 的数据目录
        data_dirs = [
            os.path.expanduser(f"~/.var/app/{package_name}"),
            f"/var/lib/flatpak/app/{package_name}",
            f"/var/lib/flatpak/runtime/{package_name}",
        ]

        for dir_path in data_dirs:
            if os.path.exists(dir_path):
                files.append(dir_path)

        return files

    def clean_residual(self, package_name: str) -> Tuple[bool, str]:
        """清理 Flatpak 包的残留文件"""
        try:
            files = self.get_residual_files(package_name)
            for file_path in files:
                try:
                    import shutil
                    if file_path.startswith(os.path.expanduser('~')):
                        # 用户目录可以直接删除
                        shutil.rmtree(file_path)
                    else:
                        # 系统目录需要 sudo
                        subprocess.run(
                            ['sudo', 'rm', '-rf', file_path],
                            capture_output=True, timeout=30
                        )
                except Exception as e:
                    print(f"清理 {file_path} 失败：{e}")
            return True, "残留清理完成"
        except Exception as e:
            return False, f"清理失败：{str(e)}"

    def repair(self, package_name: str) -> Tuple[bool, str]:
        """修复 Flatpak 包"""
        try:
            # Flatpak 可以通过 reinstall 修复
            result = subprocess.run(
                ['flatpak', 'install', '--reinstall', '-y', package_name],
                capture_output=True, text=True, timeout=300
            )

            if result.returncode == 0:
                return True, f"{package_name} 已修复"
            else:
                return False, result.stderr or result.stdout
        except Exception as e:
            return False, f"修复失败：{str(e)}"
