#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APT/DPKG 后端 - 处理 APT 包管理相关操作
"""

import subprocess
import re
from typing import Optional, Tuple, List


class APTBackend:
    """APT 包管理后端"""

    def __init__(self):
        pass

    def is_installed(self, package_name: str) -> bool:
        """检查包是否已安装"""
        try:
            result = subprocess.run(
                ['dpkg', '-s', package_name],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0 and 'Status: install ok installed' in result.stdout
        except:
            return False

    def get_version(self, package_name: str) -> str:
        """获取已安装包的版本"""
        try:
            result = subprocess.run(
                ['dpkg', '-s', package_name],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith('Version:'):
                        return line.split(':', 1)[1].strip()
        except:
            pass
        return "未知"

    def get_installed_size(self, package_name: str) -> int:
        """获取已安装包的大小（字节）"""
        try:
            result = subprocess.run(
                ['dpkg-query', '-W', '-f', '${Installed-Size}', package_name],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                size_kb = int(result.stdout.strip())
                return size_kb * 1024
        except:
            pass
        return 0

    def get_install_date(self, package_name: str) -> str:
        """获取安装日期"""
        try:
            # 从 dpkg.log 中查找
            result = subprocess.run(
                ['grep', f'install {package_name}:', '/var/log/dpkg.log'],
                capture_output=True, text=True, timeout=10
            )
            if result.stdout:
                # 获取最后一次安装记录
                lines = result.stdout.strip().split('\n')
                if lines:
                    last_line = lines[-1]
                    # 解析日期：2024-01-15 10:30:45
                    match = re.match(r'(\d{4}-\d{2}-\d{2})', last_line)
                    if match:
                        return match.group(1)
        except:
            pass

        # 尝试从状态文件获取
        try:
            result = subprocess.run(
                ['dpkg-query', '-W', '-f', '${Status}\n', package_name],
                capture_output=True, text=True, timeout=10
            )
            # DPKG 不直接提供安装日期，返回未知
        except:
            pass

        return "未知"

    def get_description(self, package_name: str) -> str:
        """获取包描述"""
        try:
            result = subprocess.run(
                ['apt-cache', 'show', package_name],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith('Description:'):
                        desc = line.split(':', 1)[1].strip()
                        # 只返回第一句
                        if '.' in desc:
                            return desc.split('.')[0] + '.'
                        return desc
        except:
            pass
        return ""

    def get_dependencies(self, package_name: str) -> List[str]:
        """获取依赖列表"""
        try:
            result = subprocess.run(
                ['apt-cache', 'depends', package_name],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                deps = []
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line.startswith('Depends:') or line.startswith('PreDepends:'):
                        deps.extend(line.split(':', 1)[1].strip().split(', '))
                    elif line and not line.startswith(('Recommends:', 'Suggests:', 'Conflicts:')):
                        if ',' in line:
                            deps.extend([d.strip() for d in line.split(',')])
                        else:
                            deps.append(line)
                return list(set(deps))
        except:
            pass
        return []

    def remove(self, package_name: str, purge: bool = False) -> Tuple[bool, str]:
        """
        移除包

        Args:
            package_name: 包名
            purge: 是否同时删除配置文件

        Returns:
            (成功标志，消息)
        """
        try:
            cmd = ['sudo', 'apt', 'remove']
            if purge:
                cmd.append('--purge')
            cmd.extend(['-y', package_name])

            result = subprocess.run(
                cmd,
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

    def autoremove(self) -> Tuple[bool, str]:
        """清理未使用的依赖"""
        try:
            result = subprocess.run(
                ['sudo', 'apt', 'autoremove', '-y'],
                capture_output=True, text=True, timeout=300
            )

            if result.returncode == 0:
                return True, "依赖清理完成"
            else:
                return False, result.stderr or result.stdout

        except Exception as e:
            return False, f"清理失败：{str(e)}"

    def get_files(self, package_name: str) -> List[str]:
        """获取包安装的文件列表"""
        try:
            result = subprocess.run(
                ['dpkg', '-L', package_name],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                return [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
        except:
            pass
        return []

    def is_system_package(self, package_name: str) -> bool:
        """检查是否是系统关键包"""
        # 系统关键包白名单
        system_packages = [
            'ubuntu-desktop', 'ubuntu-minimal', 'ubuntu-standard',
            'ubuntu-desktop-minimal', 'ubuntu-desktop-recommended',
            'base-files', 'base-passwd', 'bash', 'coreutils',
            'dpkg', 'apt', 'libc6', 'libstdc++6',
            'systemd', 'dbus', 'login', 'passwd',
            'python3', 'python3-minimal',
        ]

        if package_name in system_packages:
            return True

        # 检查是否是重要依赖
        try:
            result = subprocess.run(
                ['apt-cache', 'rdepends', '--installed', package_name],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                # 如果有大量包依赖它，可能是重要的
                dependents = [l.strip() for l in result.stdout.split('\n')[1:] if l.strip()]
                if len(dependents) > 50:
                    return True
        except:
            pass

        return False
