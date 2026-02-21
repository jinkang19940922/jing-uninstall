#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理器模块 - 执行残留文件删除操作
"""

import os
import shutil
import subprocess
from typing import Callable, Optional, Tuple, List
from .residue_scan import ResidueFile


class Cleaner:
    """残留文件清理器"""

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

    def clean(self, files: List[ResidueFile]) -> Tuple[bool, int, int]:
        """
        清理选中的残留文件

        Args:
            files: 要清理的文件列表

        Returns:
            (成功标志，删除的文件数，删除的总大小)
        """
        selected_files = [f for f in files if f.is_selected]
        total_files = len(selected_files)
        total_size = sum(f.size for f in selected_files)
        deleted_files = 0
        deleted_size = 0

        if total_files == 0:
            return True, 0, 0

        self._report_progress(f"准备清理 {total_files} 个文件...", 0)

        for i, residue_file in enumerate(selected_files):
            try:
                percent = int((i / total_files) * 100)
                self._report_progress(
                    f"正在删除：{residue_file.path}",
                    percent
                )

                if self._delete_path(residue_file.path):
                    deleted_files += 1
                    deleted_size += residue_file.size
                else:
                    self._report_error(f"无法删除：{residue_file.path}")

            except Exception as e:
                self._report_error(f"删除失败 {residue_file.path}: {str(e)}")

        self._report_progress("清理完成", 100)

        return True, deleted_files, deleted_size

    def _delete_path(self, path: str) -> bool:
        """
        删除文件或目录

        Args:
            path: 要删除的路径

        Returns:
            是否成功
        """
        try:
            if not os.path.exists(path):
                return True

            if os.path.isfile(path) or os.path.islink(path):
                # 删除文件
                if os.access(path, os.W_OK):
                    os.remove(path)
                else:
                    # 需要 root 权限，使用 pkexec
                    result = subprocess.run(
                        ['pkexec', 'rm', '-f', path],
                        capture_output=True,
                        timeout=30
                    )
                    return result.returncode == 0
                return True

            elif os.path.isdir(path):
                # 删除目录
                if os.access(path, os.W_OK):
                    shutil.rmtree(path)
                else:
                    # 需要 root 权限，使用 pkexec
                    result = subprocess.run(
                        ['pkexec', 'rm', '-rf', path],
                        capture_output=True,
                        timeout=30
                    )
                    return result.returncode == 0
                return True

        except PermissionError:
            # 尝试使用 pkexec
            if os.path.isfile(path):
                result = subprocess.run(
                    ['pkexec', 'rm', '-f', path],
                    capture_output=True,
                    timeout=30
                )
                return result.returncode == 0
            else:
                result = subprocess.run(
                    ['pkexec', 'rm', '-rf', path],
                    capture_output=True,
                    timeout=30
                )
                return result.returncode == 0

        except Exception as e:
            print(f"删除 {path} 失败：{e}")
            return False

    def clean_single(self, path: str) -> bool:
        """
        删除单个文件或目录

        Args:
            path: 要删除的路径

        Returns:
            是否成功
        """
        return self._delete_path(path)

    def backup_file(self, path: str, backup_dir: Optional[str] = None) -> Optional[str]:
        """
        备份文件

        Args:
            path: 要备份的文件
            backup_dir: 备份目录，默认为 ~/jing_backup

        Returns:
            备份文件路径，失败返回 None
        """
        if backup_dir is None:
            backup_dir = os.path.expanduser('~/jing_backup')

        try:
            os.makedirs(backup_dir, exist_ok=True)

            # 生成备份文件名
            basename = os.path.basename(path)
            timestamp = subprocess.check_output(['date', '+%Y%m%d_%H%M%S'], text=True).strip()
            backup_path = os.path.join(backup_dir, f"{basename}.{timestamp}")

            if os.path.isfile(path):
                shutil.copy2(path, backup_path)
                return backup_path
            elif os.path.isdir(path):
                shutil.copytree(path, backup_path)
                return backup_path

        except Exception as e:
            print(f"备份失败：{e}")

        return None
