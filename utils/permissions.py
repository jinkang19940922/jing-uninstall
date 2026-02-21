#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限管理模块 - 管理系统权限
"""

import os
import subprocess
from typing import Tuple


class PermissionManager:
    """权限管理器"""

    def __init__(self):
        self.is_root = os.geteuid() == 0
        self.sudo_available = self._check_sudo()
        self.pkexec_available = self._check_pkexec()

    def _check_sudo(self) -> bool:
        """检查 sudo 是否可用"""
        try:
            result = subprocess.run(
                ['which', 'sudo'],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except:
            return False

    def _check_pkexec(self) -> bool:
        """检查 pkexec 是否可用"""
        try:
            result = subprocess.run(
                ['which', 'pkexec'],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except:
            return False

    def is_admin(self) -> bool:
        """检查是否是管理员"""
        return self.is_root

    def check_admin_access(self, password: str = None) -> bool:
        """
        检查管理员访问权限

        Args:
            password: 密码（可选）

        Returns:
            是否有管理员权限
        """
        if self.is_root:
            return True

        # 测试 sudo 权限
        if self.sudo_available:
            try:
                result = subprocess.run(
                    ['sudo', '-n', 'true'],
                    capture_output=True, timeout=10
                )
                if result.returncode == 0:
                    return True
            except:
                pass

        # 测试 pkexec
        if self.pkexec_available:
            return True

        return False

    def run_as_root(self, command: list, password: str = None) -> Tuple[bool, str]:
        """
        以 root 权限运行命令

        Args:
            command: 命令列表
            password: 密码

        Returns:
            (成功标志，输出)
        """
        if self.is_root:
            # 已经是 root
            try:
                result = subprocess.run(
                    command,
                    capture_output=True, text=True, timeout=300
                )
                return result.returncode == 0, result.stdout
            except Exception as e:
                return False, str(e)

        # 使用 sudo
        if self.sudo_available:
            if password:
                sudo_cmd = ['echo', password, '|', 'sudo', '-S'] + command
                try:
                    result = subprocess.run(
                        ' '.join(sudo_cmd),
                        shell=True,
                        capture_output=True, text=True, timeout=300
                    )
                    return result.returncode == 0, result.stdout
                except Exception as e:
                    return False, str(e)
            else:
                # 无密码 sudo
                try:
                    result = subprocess.run(
                        ['sudo'] + command,
                        capture_output=True, text=True, timeout=300
                    )
                    return result.returncode == 0, result.stdout
                except Exception as e:
                    return False, str(e)

        # 使用 pkexec
        if self.pkexec_available:
            try:
                result = subprocess.run(
                    ['pkexec'] + command,
                    capture_output=True, text=True, timeout=300
                )
                return result.returncode == 0, result.stdout
            except Exception as e:
                return False, str(e)

        return False, "没有可用的提权方式"

    def get_password(self) -> str:
        """
        获取存储的管理员密码

        Returns:
            密码字符串
        """
        # 注意：实际应用中应该使用更安全的方式存储密码
        # 推荐使用 pkexec 进行图形化认证，而不是存储密码
        return ""

    def test_sudo_password(self, password: str) -> bool:
        """
        测试 sudo 密码是否正确

        Args:
            password: 密码

        Returns:
            密码是否正确
        """
        try:
            result = subprocess.run(
                ['echo', password, '|', 'sudo', '-S', 'true'],
                shell=True,
                capture_output=True, timeout=10
            )
            return result.returncode == 0
        except:
            return False

    def request_pkexec_authorization(self) -> bool:
        """
        请求 pkexec 授权

        Returns:
            是否获得授权
        """
        try:
            # 运行一个简单的命令来测试授权
            result = subprocess.run(
                ['pkexec', 'echo', 'authorized'],
                capture_output=True, text=True, timeout=30
            )
            return result.returncode == 0 and result.stdout.strip() == 'authorized'
        except:
            return False


# 全局权限管理器实例
permission_manager = PermissionManager()
