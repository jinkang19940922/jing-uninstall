#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
残留扫描模块 - 扫描软件卸载后的残留文件和目录
"""

import os
import subprocess
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ResidueType(Enum):
    """残留类型"""
    CONFIG = "配置文件"
    LOG = "日志文件"
    CACHE = "缓存文件"
    DATA = "数据文件"
    OTHER = "其他"


@dataclass
class ResidueFile:
    """残留文件信息"""
    path: str
    size: int
    size_str: str
    type: ResidueType
    is_selected: bool = True
    is_safe_to_delete: bool = True

    def to_dict(self) -> dict:
        return {
            'path': self.path,
            'size': self.size,
            'size_str': self.size_str,
            'type': self.type.value,
            'is_selected': self.is_selected,
            'is_safe_to_delete': self.is_safe_to_delete
        }


class ResidueScanner:
    """残留文件扫描器"""

    # 扫描路径配置
    SCAN_PATHS = {
        'system_config': ['/etc'],
        'system_log': ['/var/log'],
        'system_data': ['/var/lib', '/opt'],
        'user_config': [os.path.expanduser('~/.config')],
        'user_cache': [os.path.expanduser('~/.cache')],
        'user_data': [os.path.expanduser('~/.local/share'),
                      os.path.expanduser('~/.local/state')],
        'usr_local': ['/usr/local']
    }

    def __init__(self):
        self.residue_files: List[ResidueFile] = []
        self.package_name = ""
        self.keywords = []

    def scan(self, package_name: str) -> List[ResidueFile]:
        """
        扫描指定软件的残留文件

        Args:
            package_name: 软件包名称

        Returns:
            残留文件列表
        """
        self.residue_files = []
        self.package_name = package_name

        # 生成搜索关键词
        self.keywords = self._generate_keywords(package_name)

        # 扫描各个路径
        for category, paths in self.SCAN_PATHS.items():
            for path in paths:
                if os.path.exists(path):
                    self._scan_path(path, category)

        # 按路径排序
        self.residue_files.sort(key=lambda x: (x.type.value, x.path))

        return self.residue_files

    def _generate_keywords(self, package_name: str) -> List[str]:
        """生成搜索关键词"""
        keywords = [package_name]

        # 添加变体
        keywords.append(package_name.replace('-', ''))
        keywords.append(package_name.replace('_', ''))
        keywords.append(package_name.lower())
        keywords.append(package_name.upper())

        # 添加显示名变体
        display_name = package_name.replace('-', ' ').replace('_', ' ')
        keywords.append(display_name)
        keywords.append(display_name.lower())
        keywords.append(display_name.upper())

        # 去重
        return list(set(keywords))

    def _scan_path(self, base_path: str, category: str) -> None:
        """
        扫描指定路径

        Args:
            base_path: 基础路径
            category: 类别
        """
        try:
            for root, dirs, files in os.walk(base_path, followlinks=False):
                # 检查目录名
                for dir_name in dirs:
                    if self._is_match(dir_name):
                        dir_path = os.path.join(root, dir_name)
                        size = self._get_dir_size(dir_path)
                        residue_type = self._get_residue_type(category, dir_path)

                        self.residue_files.append(ResidueFile(
                            path=dir_path,
                            size=size,
                            size_str=self._format_size(size),
                            type=residue_type,
                            is_selected=True,
                            is_safe_to_delete=self._is_safe_to_delete(category, dir_path)
                        ))

                # 检查文件名
                for file_name in files:
                    if self._is_match(file_name):
                        file_path = os.path.join(root, file_name)
                        try:
                            size = os.path.getsize(file_path)
                        except:
                            size = 0
                        residue_type = self._get_residue_type(category, file_path)

                        self.residue_files.append(ResidueFile(
                            path=file_path,
                            size=size,
                            size_str=self._format_size(size),
                            type=residue_type,
                            is_selected=True,
                            is_safe_to_delete=self._is_safe_to_delete(category, file_path)
                        ))
        except PermissionError:
            pass
        except Exception as e:
            print(f"扫描路径 {base_path} 时出错：{e}")

    def _is_match(self, name: str) -> bool:
        """检查名称是否匹配关键词"""
        name_lower = name.lower()

        for keyword in self.keywords:
            if keyword.lower() in name_lower:
                return True

        return False

    def _get_residue_type(self, category: str, path: str) -> ResidueType:
        """根据路径判断残留类型"""
        path_lower = path.lower()

        if 'config' in category or '/etc/' in path or '.config' in path:
            return ResidueType.CONFIG
        elif 'log' in category or '/log/' in path or path_lower.endswith('.log'):
            return ResidueType.LOG
        elif 'cache' in category or '/cache/' in path:
            return ResidueType.CACHE
        elif 'data' in category:
            return ResidueType.DATA
        else:
            return ResidueType.OTHER

    def _is_safe_to_delete(self, category: str, path: str) -> bool:
        """判断是否可以安全删除"""
        # 系统关键目录不建议删除
        unsafe_paths = ['/etc/systemd', '/etc/init.d', '/etc/rc', '/usr/local/bin']
        for unsafe in unsafe_paths:
            if path.startswith(unsafe):
                return False

        # 日志和缓存通常是安全的
        if category in ['system_log', 'user_cache']:
            return True

        # 用户配置通常是安全的
        if category == 'user_config':
            return True

        return True

    def _get_dir_size(self, dir_path: str) -> int:
        """获取目录总大小"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(dir_path):
                for filename in filenames:
                    try:
                        filepath = os.path.join(dirpath, filename)
                        if os.path.isfile(filepath) and not os.path.islink(filepath):
                            total_size += os.path.getsize(filepath)
                    except:
                        pass
        except:
            pass
        return total_size

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

    def get_total_size(self) -> int:
        """获取所有选中文件的总大小"""
        return sum(f.size for f in self.residue_files if f.is_selected)

    def get_total_size_str(self) -> str:
        """获取总大小的格式化字符串"""
        return self._format_size(self.get_total_size())

    def get_selected_count(self) -> int:
        """获取选中的文件数量"""
        return sum(1 for f in self.residue_files if f.is_selected)

    def get_total_count(self) -> int:
        """获取总文件数量"""
        return len(self.residue_files)
