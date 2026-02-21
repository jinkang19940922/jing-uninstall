# 🚀 净卸 JingUninstall

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-green.svg)
![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-red.svg)
![Platform](https://img.shields.io/badge/platform-Linux-orange.svg)
![GitHub Stars](https://img.shields.io/github/stars/jinkang19940922/jing-uninstall?style=flat&logo=github)

**专业的 Linux 软件卸载工具**

一款仿照 Windows Geek Uninstaller 的 Linux 卸载工具

[功能特点](#-功能特点) • [安装说明](#-安装说明) • [使用指南](#-使用指南) • [更新日志](#-更新日志)

</div>

---

## 📖 简介

**净卸 JingUninstall** 是一款专为 Linux 系统设计的软件卸载工具，提供强大的软件卸载和残留清理功能。

### 🎯 设计理念

- **简洁高效** - 直观的现代化界面，一键操作
- **彻底清理** - 扫描并清理配置文件、日志、缓存等残留
- **多包支持** - 支持 APT、Snap、Flatpak、AppImage
- **安全可靠** - 系统包保护机制，防止误删重要组件

---

## ✨ 功能特点

| 功能 | 描述 |
|------|------|
| 📦 **多包管理支持** | 支持 APT/DPKG、Snap、Flatpak、AppImage 四种包格式 |
| 🗑️ **标准卸载** | 通过包管理器正常卸载软件 |
| ⚡ **强制卸载** | 针对无法正常卸载的软件进行强制移除 |
| 🧹 **残留扫描** | 自动扫描配置文件、日志、缓存等残留 |
| 📊 **软件列表** | 按名称、大小、来源、安装日期排序和筛选 |
| 🔍 **快速搜索** | 实时搜索过滤软件 |
| 🛡️ **系统保护** | 系统关键包白名单保护，防止误删 |
| 📱 **美观界面** | 现代化 GUI 界面，渐变紫色主题 |
| ✅ **多选操作** | 支持批量选择和批量操作 |
| 🔒 **滚动条优化** | 仅支持滚轮滚动，防止误点击跳转 |

---

## 📦 安装说明

### 方式一：DEB 包安装（推荐）

```bash
# 下载 DEB 包后执行
sudo dpkg -i jing-uninstall_1.0.0_all.deb

# 如有依赖问题，执行
sudo apt install -f
```

### 方式二：源码安装

```bash
# 1. 安装依赖
sudo apt install python3-pyqt6 python3-apt pkexec

# 可选：安装 Snap 和 Flatpak 支持
sudo apt install snapd flatpak

# 2. 运行程序
cd JingUninstall
python3 main.py
```

### 方式三：使用打包脚本

```bash
# 安装打包工具
sudo apt install debhelper devscripts dh-python

# 构建 DEB 包
cd packaging
bash build.sh

# 安装生成的包
sudo dpkg -i ../jing-uninstall_1.0.0_all.deb
```

---

## 🚀 使用指南

### 启动程序

```bash
# 命令行启动
jing-uninstall

# 或者
python3 main.py

# 或者在应用程序菜单中找到 "净卸 JingUninstall"
```

### 基本操作

1. **查看软件列表**
   - 程序启动后自动扫描已安装的软件
   - 系统包自动过滤，不显示在列表中
   - 点击刷新按钮重新扫描

2. **搜索软件**
   - 在搜索框输入关键词
   - 使用来源过滤器筛选

3. **卸载软件**
   - 点击第一列复选框勾选要卸载的软件
   - 点击底部「卸载」按钮
   - 确认后即可卸载

4. **强制卸载**
   - 当正常卸载失败时使用
   - 勾选软件后点击「强制卸载」
   - ⚠️ 注意：可能导致系统状态不一致

5. **扫描残留**
   - 选择一个已卸载的软件
   - 点击「扫描残留」
   - 勾选要清理的文件
   - 点击「清理选中」

### 多选操作

- **单选** - 点击第一列复选框
- **全选** - 菜单 `编辑` → `全选` 或 `Ctrl+A`
- **取消全选** - 菜单 `编辑` → `取消全选` 或 `Ctrl+Shift+A`
- **反选** - 菜单 `编辑` → `反选` 或 `Ctrl+I`

### 列表操作

- **调整列宽** - 拖动表头分隔线
- **滚动列表** - 使用鼠标滚轮或拖动滚动条滑块
- **注意** - 点击滚动条空白处不会跳转（防止误操作）

---

## 🏗️ 项目结构

```
JingUninstall/
├── main.py                 # 程序入口
├── core/                   # 核心模块
│   ├── scanner.py          # 软件扫描（含系统包过滤）
│   ├── uninstaller.py      # 卸载器
│   ├── residue_scan.py     # 残留扫描
│   └── cleaner.py          # 清理器
├── backends/               # 包管理后端
│   ├── apt_backend.py      # APT 后端
│   ├── snap_backend.py     # Snap 后端
│   ├── flatpak_backend.py  # Flatpak 后端
│   └── appimage_backend.py # AppImage 后端
├── ui/                     # 用户界面
│   ├── main_window.py      # 主窗口（现代化设计）
│   ├── package_list.py     # 软件列表（自定义绘制）
│   ├── residue_dialog.py   # 残留对话框
│   └── progress_dialog.py  # 进度对话框
├── utils/                  # 工具模块
│   ├── app_name_resolver.py # 应用名称解析
│   └── package_info.py     # 包信息
├── config/                 # 配置文件
│   ├── scan_paths.yaml     # 扫描路径
│   └── whitelist.yaml      # 保护白名单
├── resources/              # 资源文件
│   ├── jing-uninstall.svg  # 图标
│   ├── styles.qss          # 样式表
│   └── jing-uninstall.desktop
├── packaging/              # 打包配置
│   └── debian/             # DEB 打包文件
├── requirements.txt        # Python 依赖
└── README.md               # 说明文档
```

---

## 🔧 更新日志

### v1.0.0 (2026-02-19)

**新增功能**
- ✨ 现代化渐变紫色主题界面
- ✨ 系统包自动过滤（50+ 关键包）
- ✨ 复选框自定义绘制（选中显示蓝色背景 + 白色对勾）
- ✨ 选中行紫色高亮显示
- ✨ 列宽支持拖动调整
- ✨ 滚动条优化（仅滚轮滚动，防止误点击）

**界面优化**
- 🎨 移除所有 emoji，使用纯文本
- 🎨 圆角搜索框和按钮设计
- 🎨 流畅的进度条动画
- 🎨 无方框叉叉标记

**性能优化**
- ⚡ 使用 Model/View 架构提升列表性能
- ⚡ 后台解析应用名称，不阻塞界面
- ⚡ 优化进度更新频率

**Bug 修复**
- 🐛 修复滚动条无法拖动问题
- 🐛 修复多选误触发问题
- 🐛 修复列宽设置冲突问题

---

## ⚠️ 注意事项

1. **系统包保护**
   - 系统关键包已加入白名单（apt, dpkg, systemd, python3 等）
   - 这些包不会显示在列表中，防止误删

2. **强制卸载风险**
   - 强制卸载不经过包管理器，可能导致依赖问题
   - 仅在正常卸载失败时使用

3. **权限要求**
   - 卸载软件需要管理员权限
   - 程序会自动请求权限

---

## 📄 许可证

本项目采用 GPL-3.0 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📞 联系方式

- 项目主页：https://github.com/jinkang19940922/jing-uninstall
- 问题反馈：https://github.com/jinkang19940922/jing-uninstall/issues

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给个 Star 支持一下！⭐**

© 2025 JingUninstall Team

</div>
