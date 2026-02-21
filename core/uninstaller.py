#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
卸载器模块 - 执行软件卸载操作
"""

import subprocess
import os
from typing import Callable, Optional, Tuple
from .scanner import Package, PackageSource


class Uninstaller:
    """软件卸载器"""

    def __init__(self):
        self.progress_callback: Optional[Callable[[str, int], None]] = None
        self.error_callback: Optional[Callable[[str], None]] = None

    def set_progress_callback(self, callback: Callable[[str, int], None]):
        """设置进度回调"""
        self.progress_callback = callback

    def set_error_callback(self, callback: Callable[[str], None]):
        """设置错误回调"""
        self.error_callback = callback

    def _report_progress(self, message: str, percent: int = 0):
        """报告进度"""
        if self.progress_callback:
            self.progress_callback(message, percent)

    def _report_error(self, message: str):
        """报告错误"""
        if self.error_callback:
            self.error_callback(message)

    def uninstall(self, package: Package, force: bool = False) -> Tuple[bool, str]:
        """
        卸载软件包

        Args:
            package: 要卸载的软件包
            force: 是否强制卸载

        Returns:
            (成功标志，消息)
        """
        try:
            if package.source == PackageSource.APT:
                return self._uninstall_apt(package, force)
            elif package.source == PackageSource.SNAP:
                return self._uninstall_snap(package, force)
            elif package.source == PackageSource.FLATPAK:
                return self._uninstall_flatpak(package, force)
            elif package.source == PackageSource.APPIMAGE:
                return self._uninstall_appimage(package, force)
            else:
                return False, f"不支持的软件来源：{package.source.value}"
        except Exception as e:
            error_msg = f"卸载失败：{str(e)}"
            self._report_error(error_msg)
            return False, error_msg

    def _run_pkexec_command(self, cmd: list) -> subprocess.CompletedProcess:
        """使用 pkexec 运行命令"""
        # 优先使用 pkexec（图形化提权，适合 GUI 应用）
        pkexec_cmd = ['pkexec'] + cmd
        return subprocess.run(
            pkexec_cmd,
            capture_output=True, text=True, timeout=300
        )

    def _uninstall_apt(self, package: Package, force: bool) -> Tuple[bool, str]:
        """卸载 APT 包"""
        self._report_progress(f"正在停止 {package.name} 相关服务...", 10)

        # 尝试停止相关服务
        try:
            subprocess.run(
                ['pkexec', 'systemctl', 'stop', package.name],
                capture_output=True, timeout=10
            )
        except:
            pass

        if force:
            self._report_progress(f"正在强制卸载 {package.name}...", 30)
            # 强制卸载 - 直接 purge
            result = self._run_pkexec_command(['apt', 'remove', '--purge', '-y', package.name])
        else:
            self._report_progress(f"正在卸载 {package.name}...", 30)
            # 标准卸载
            result = self._run_pkexec_command(['apt', 'remove', '-y', package.name])

        self._report_progress(f"正在清理依赖...", 80)

        # 清理未使用的依赖
        self._run_pkexec_command(['apt', 'autoremove', '-y'])

        self._report_progress("卸载完成", 100)

        if result.returncode == 0:
            return True, f"{package.name} 已成功卸载"
        else:
            error_msg = result.stderr or result.stdout
            return False, f"卸载失败：{error_msg}"

    def _uninstall_snap(self, package: Package, force: bool) -> Tuple[bool, str]:
        """卸载 Snap 包"""
        self._report_progress(f"正在卸载 {package.name}...", 30)

        # Snap 卸载需要 sudo 权限
        result = self._run_pkexec_command(['snap', 'remove', package.name])

        self._report_progress("卸载完成", 100)

        if result.returncode == 0:
            return True, f"{package.name} 已成功卸载"
        else:
            error_msg = result.stderr or result.stdout
            return False, f"卸载失败：{error_msg}"

    def _uninstall_flatpak(self, package: Package, force: bool) -> Tuple[bool, str]:
        """卸载 Flatpak 包"""
        self._report_progress(f"正在卸载 {package.name}...", 30)

        # Flatpak 卸载
        cmd = ['flatpak', 'uninstall', '-y', package.name]
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=300
        )

        # 如果需要 sudo，尝试带 pkexec
        if result.returncode != 0:
            result = self._run_pkexec_command(['flatpak', 'uninstall', '-y', package.name])

        self._report_progress("卸载完成", 100)

        if result.returncode == 0:
            return True, f"{package.name} 已成功卸载"
        else:
            error_msg = result.stderr or result.stdout
            return False, f"卸载失败：{error_msg}"

    def _uninstall_appimage(self, package: Package, force: bool) -> Tuple[bool, str]:
        """卸载 AppImage 文件"""
        self._report_progress(f"正在删除 {package.name}...", 30)

        # 从描述中获取文件路径
        filepath = package.description.replace('AppImage: ', '')

        if os.path.exists(filepath):
            try:
                # 尝试直接删除
                os.remove(filepath)
                self._report_progress("卸载完成", 100)
                return True, f"{package.name} 已成功删除"
            except PermissionError:
                # 需要 root 权限
                result = self._run_pkexec_command(['rm', '-f', filepath])
                self._report_progress("卸载完成", 100)
                if result.returncode == 0:
                    return True, f"{package.name} 已成功删除"
                else:
                    return False, f"删除失败：{result.stderr}"
        else:
            return False, f"文件不存在：{filepath}"

    def force_remove_package(self, package: Package) -> Tuple[bool, str]:
        """
        强制移除软件包（不经过包管理器）

        Args:
            package: 要移除的软件包

        Returns:
            (成功标志，消息)
        """
        if package.source != PackageSource.APT:
            return False, "强制卸载仅支持 APT 包"

        try:
            self._report_progress(f"正在强制移除 {package.name}...", 20)

            # 1. 获取包的文件列表
            result = subprocess.run(
                ['dpkg', '-L', package.name],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                files = result.stdout.strip().split('\n')
                self._report_progress(f"发现 {len(files)} 个文件", 40)

                # 2. 删除文件
                deleted = 0
                for filepath in files:
                    try:
                        if os.path.isfile(filepath):
                            subprocess.run(
                                ['pkexec', 'rm', '-f', filepath],
                                capture_output=True, timeout=5
                            )
                            deleted += 1
                        elif os.path.isdir(filepath) and not os.listdir(filepath):
                            subprocess.run(
                                ['pkexec', 'rmdir', filepath],
                                capture_output=True, timeout=5
                            )
                            deleted += 1
                    except:
                        pass

                self._report_progress(f"已删除 {deleted} 个文件", 70)

            # 3. 从 dpkg 状态中移除
            subprocess.run(
                ['pkexec', 'dpkg', '--remove', '--force-remove-reinstreq', package.name],
                capture_output=True, timeout=30
            )

            self._report_progress("强制卸载完成", 100)
            return True, f"{package.name} 已强制移除"

        except Exception as e:
            return False, f"强制卸载失败：{str(e)}"
