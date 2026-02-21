#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
软件扫描模块 - 扫描系统中已安装的软件
"""

import os
import subprocess
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class PackageSource(Enum):
    """软件来源"""
    APT = "APT"
    SNAP = "Snap"
    FLATPAK = "Flatpak"
    APPIMAGE = "AppImage"


@dataclass
class Package:
    """软件包信息"""
    name: str
    display_name: str
    version: str
    size: str
    source: PackageSource
    install_date: str
    description: str
    is_selected: bool = False

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'display_name': self.display_name,
            'version': self.version,
            'size': self.size,
            'source': self.source.value,
            'install_date': self.install_date,
            'description': self.description,
            'is_selected': self.is_selected
        }


class PackageScanner:
    """软件包扫描器"""

    # 系统包白名单 - 这些包不应该被卸载
    SYSTEM_PACKAGES = {
        # 核心系统组件
        'apt', 'dpkg', 'systemd', 'udev', 'dbus', 'polkit',
        'login', 'passwd', 'adduser', 'base-files', 'base-passwd',
        
        # 图形系统
        'xorg', 'xserver', 'wayland', 'mesa', 'libgl',
        
        # 网络
        'networkd', 'networkmanager', 'wpa-supplicant',
        
        # 显示管理器
        'gdm', 'gdm3', 'lightdm', 'sddm',
        
        # 桌面环境核心
        'gnome-core', 'gnome-shell', 'kde-plasma-desktop',
        
        # Python 核心
        'python3', 'python3-minimal', 'libpython3',
        
        # 系统工具
        'bash', 'coreutils', 'findutils', 'grep', 'gzip',
        'sed', 'tar', 'util-linux', 'lsb',
        
        # 固件
        'linux-firmware', 'amd64-microcode', 'intel-microcode',
        
        # 引导
        'grub', 'shim',
        
        # 其他关键包
        'libc6', 'libstdc++', 'libgcc', 'openssl', 'ca-certificates',
    }

    def __init__(self, skip_system_packages: bool = True):
        self.packages: List[Package] = []
        self.progress_callback: Optional[Callable[[str, int], None]] = None
        self.skip_system_packages = skip_system_packages

    def set_progress_callback(self, callback: Callable[[str, int], None]):
        """设置进度回调"""
        self.progress_callback = callback

    def _report_progress(self, message: str, percent: int):
        """报告进度"""
        if self.progress_callback:
            self.progress_callback(message, percent)

    def scan_all(self, sources: Optional[List[PackageSource]] = None) -> List[Package]:
        """
        扫描所有软件包

        Args:
            sources: 指定要扫描的来源，None 表示全部

        Returns:
            软件包列表
        """
        self.packages = []

        if sources is None:
            sources = [PackageSource.APT, PackageSource.SNAP,
                       PackageSource.FLATPAK, PackageSource.APPIMAGE]

        total_sources = len(sources)
        completed = 0

        if PackageSource.APT in sources:
            self._report_progress("正在扫描 APT 软件包...", 0)
            apt_packages = self._scan_apt()
            self.packages.extend(apt_packages)
            self._report_progress(f"APT: {len(apt_packages)} 个软件", 25)
            completed += 1

        if PackageSource.SNAP in sources:
            self._report_progress("正在扫描 Snap 软件包...", 25)
            snap_packages = self._scan_snap()
            self.packages.extend(snap_packages)
            self._report_progress(f"Snap: {len(snap_packages)} 个软件", 50)
            completed += 1

        if PackageSource.FLATPAK in sources:
            self._report_progress("正在扫描 Flatpak 软件包...", 50)
            flatpak_packages = self._scan_flatpak()
            self.packages.extend(flatpak_packages)
            self._report_progress(f"Flatpak: {len(flatpak_packages)} 个软件", 75)
            completed += 1

        if PackageSource.APPIMAGE in sources:
            self._report_progress("正在扫描 AppImage 文件...", 75)
            appimage_packages = self._scan_appimage()
            self.packages.extend(appimage_packages)
            self._report_progress(f"AppImage: {len(appimage_packages)} 个文件", 95)
            completed += 1

        self._report_progress(f"扫描完成，共 {len(self.packages)} 个软件", 100)

        return self.packages

    def _scan_apt(self) -> List[Package]:
        """扫描 APT 安装的软件包"""
        packages = []
        try:
            # 使用 dpkg-query 获取已安装的包
            result = subprocess.run(
                ['dpkg-query', '-W', '-f',
                 '${Package}|${Version}|${Installed-Size}|${Status}\n'],
                capture_output=True, text=True, timeout=60
            )

            # 预先从 dpkg 日志中获取安装日期
            install_dates = self._get_install_dates_from_log()

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if not line:
                        continue
                    parts = line.split('|')
                    if len(parts) >= 4:
                        name = parts[0]
                        version = parts[1]
                        size_kb = int(parts[2]) if parts[2].isdigit() else 0
                        status = parts[3]

                        # 只保留已安装的包
                        if 'install ok installed' in status:
                            # 跳过系统包
                            if self.skip_system_packages and name in self.SYSTEM_PACKAGES:
                                continue

                            # 获取安装日期
                            install_date = install_dates.get(name, "未知")

                            packages.append(Package(
                                name=name,
                                display_name=self._format_package_name(name),
                                version=version,
                                size=self._format_size(size_kb * 1024),
                                source=PackageSource.APT,
                                install_date=install_date,
                                description=""
                            ))
        except Exception as e:
            print(f"APT 扫描错误：{e}")

        return packages

    def _scan_snap(self) -> List[Package]:
        """扫描 Snap 安装的软件包"""
        packages = []
        try:
            # 检查 snap 是否可用
            result = subprocess.run(
                ['which', 'snap'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                return packages

            result = subprocess.run(
                ['snap', 'list'],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                # 跳过标题行
                for line in lines[1:]:
                    if not line:
                        continue
                    parts = line.split()
                    if len(parts) >= 3:
                        name = parts[0]
                        version = parts[1]

                        packages.append(Package(
                            name=name,
                            display_name=self._format_package_name(name),
                            version=version,
                            size="未知",
                            source=PackageSource.SNAP,
                            install_date="未知",
                            description=""
                        ))
        except Exception as e:
            print(f"Snap 扫描错误：{e}")

        return packages

    def _scan_flatpak(self) -> List[Package]:
        """扫描 Flatpak 安装的软件包"""
        packages = []
        try:
            # 检查 flatpak 是否可用
            result = subprocess.run(
                ['which', 'flatpak'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                return packages

            result = subprocess.run(
                ['flatpak', 'list', '--app', '--columns=application,version'],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if not line:
                        continue
                    parts = line.split('\t')
                    if len(parts) >= 1:
                        name = parts[0]
                        version = parts[1] if len(parts) > 1 else "未知"

                        packages.append(Package(
                            name=name,
                            display_name=self._format_package_name(name),
                            version=version,
                            size="未知",
                            source=PackageSource.FLATPAK,
                            install_date="未知",
                            description=""
                        ))
        except Exception as e:
            print(f"Flatpak 扫描错误：{e}")

        return packages

    def _scan_appimage(self) -> List[Package]:
        """扫描 AppImage 文件"""
        packages = []
        search_paths = [
            os.path.expanduser("~/Applications"),
            os.path.expanduser("~/.local/bin"),
            "/opt",
        ]

        for search_path in search_paths:
            if not os.path.exists(search_path):
                continue

            try:
                for filename in os.listdir(search_path):
                    if filename.lower().endswith('.appimage'):
                        filepath = os.path.join(search_path, filename)
                        stat_info = os.stat(filepath)

                        packages.append(Package(
                            name=filename,
                            display_name=filename.replace('.AppImage', '').replace('.appimage', ''),
                            app_name="",  # AppImage 没有启动器
                            version="未知",
                            size=self._format_size(stat_info.st_size),
                            source=PackageSource.APPIMAGE,
                            install_date=self._timestamp_to_date(stat_info.st_mtime),
                            description=f"AppImage: {filepath}"
                        ))
            except Exception as e:
                print(f"AppImage 扫描错误 ({search_path}): {e}")

        return packages

    def _format_package_name(self, name: str) -> str:
        """格式化包名为可读名称"""
        return name.replace('-', ' ').replace('_', ' ').title()

    def _parse_dpkg_date(self, dpkg_date: str) -> str:
        """
        解析 dpkg 日期格式
        
        dpkg 日期格式示例：1699876543 (Unix 时间戳)
        """
        if not dpkg_date:
            return "未知"
        
        try:
            # dpkg 返回的是 Unix 时间戳
            timestamp = int(dpkg_date)
            return self._timestamp_to_date(timestamp)
        except ValueError:
            # 如果不是数字，尝试直接解析
            try:
                from datetime import datetime
                # 尝试解析常见格式
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%a %b %d %H:%M:%S %Y']:
                    try:
                        dt = datetime.strptime(dpkg_date, fmt)
                        return dt.strftime('%Y-%m-%d')
                    except ValueError:
                        continue
            except:
                pass
            return "未知"

    def _get_install_dates_from_log(self) -> Dict[str, str]:
        """
        从 dpkg 日志中获取软件安装日期
        
        Returns:
            包名到安装日期的映射
        """
        dates = {}
        log_files = [
            '/var/log/dpkg.log',
            '/var/log/dpkg.log.1',
        ]
        
        for log_file in log_files:
            if not os.path.exists(log_file):
                continue
            
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        # 格式：2024-01-15 10:30:00 install package-name:amd64 <none> version
                        if ' install ' in line:
                            parts = line.strip().split()
                            if len(parts) >= 4 and parts[2] == 'install':
                                date_str = parts[0]  # 2024-01-15
                                pkg_full = parts[3]  # package-name:amd64
                                # 去掉架构后缀
                                pkg_name = pkg_full.split(':')[0]
                                if pkg_name not in dates:  # 只记录第一次安装
                                    dates[pkg_name] = date_str
            except Exception as e:
                pass
        
        return dates

    def _format_size(self, size_bytes: int) -> str:
        """格式化字节大小"""
        if size_bytes == 0:
            return "0 B"

        units = ['B', 'KB', 'MB', 'GB']
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

    def search(self, keyword: str) -> List[Package]:
        """搜索软件包"""
        keyword = keyword.lower()
        return [
            pkg for pkg in self.packages
            if keyword in pkg.name.lower() or keyword in pkg.display_name.lower()
        ]

    def filter_by_source(self, source: PackageSource) -> List[Package]:
        """按来源过滤软件包"""
        return [pkg for pkg in self.packages if pkg.source == source]
