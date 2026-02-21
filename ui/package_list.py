#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
软件列表组件 - 使用 Model/View 架构提升性能

功能特性：
- 支持列宽自定义调整
- 复选框选中显示对勾
- 滚动条仅支持滚轮滚动
- 选中项高亮显示
- 点击复选框列才触发选择
"""

from PyQt6.QtWidgets import (QTableView, QAbstractItemView, QHeaderView, QStyledItemDelegate)
from PyQt6.QtCore import Qt, QAbstractTableModel, pyqtSignal, QModelIndex, QRect, QSize
from PyQt6.QtGui import QColor, QFont, QBrush, QPainter, QPen

from core.scanner import Package, PackageSource


# 列定义
COLUMN_COUNT = 6
COLUMN_HEADERS = ['', '包名', '大小', '来源', '安装日期', '版本']

# 列宽配置 - 固定宽度列
COLUMN_WIDTHS = {
    0: 50,    # 选择框
    2: 85,    # 大小
    3: 75,    # 来源
    4: 100,   # 安装日期
    5: 90,    # 版本
}

# 来源颜色配置 - 极淡色，几乎看不出
SOURCE_COLORS = {
    PackageSource.APT: QColor(253, 254, 255),
    PackageSource.SNAP: QColor(255, 253, 250),
    PackageSource.FLATPAK: QColor(250, 253, 250),
    PackageSource.APPIMAGE: QColor(253, 250, 254),
}

# 选中状态颜色 - 明显的紫色高亮
SELECTION_BACKGROUND = QColor(195, 205, 235)


class CheckboxDelegate(QStyledItemDelegate):
    """复选框委托 - 绘制带对勾的复选框"""

    def paint(self, painter, option, index):
        """绘制复选框"""
        package = index.data(Qt.ItemDataRole.UserRole)
        if not package:
            return

        is_checked = package.is_selected
        row = index.row()

        # 绘制背景 - 选中项用高亮色
        if is_checked:
            painter.fillRect(option.rect, SELECTION_BACKGROUND)
        else:
            base_color = SOURCE_COLORS.get(package.source, QColor(250, 250, 250))
            if row % 2 == 1:
                base_color = base_color.darker(102)
            painter.fillRect(option.rect, base_color)

        # 绘制复选框
        checkbox_size = 20
        checkbox_rect = QRect(
            option.rect.left() + (option.rect.width() - checkbox_size) // 2,
            option.rect.center().y() - checkbox_size // 2,
            checkbox_size,
            checkbox_size
        )

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 复选框背景
        painter.setPen(QPen(QColor(170, 170, 170), 2))
        painter.setBrush(QColor(255, 255, 255))
        painter.drawRoundedRect(checkbox_rect, 4, 4)

        # 如果选中，绘制填充和对勾
        if is_checked:
            # 填充蓝色背景
            painter.setBrush(QColor(102, 126, 234))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(checkbox_rect, 4, 4)

            # 绘制白色对勾
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            check_rect = checkbox_rect.adjusted(5, 5, -5, -5)
            # 对勾：左下 → 中间 → 右上
            painter.drawLine(
                check_rect.left() + 2, check_rect.center().y() + 1,
                check_rect.center().x(), check_rect.bottom() - 3
            )
            painter.drawLine(
                check_rect.center().x(), check_rect.bottom() - 3,
                check_rect.right() - 2, check_rect.top() + 3
            )

        painter.restore()

    def sizeHint(self, option, index):
        """设置尺寸提示"""
        return QSize(50, 40)


class TextDelegate(QStyledItemDelegate):
    """文本委托 - 绘制其他列"""

    def paint(self, painter, option, index):
        """绘制文本"""
        package = index.data(Qt.ItemDataRole.UserRole)
        if not package:
            return

        is_selected = package.is_selected
        col = index.column()
        row = index.row()

        # 绘制背景
        if is_selected:
            painter.fillRect(option.rect, SELECTION_BACKGROUND)
        else:
            base_color = SOURCE_COLORS.get(package.source, QColor(250, 250, 250))
            if row % 2 == 1:
                base_color = base_color.darker(102)
            painter.fillRect(option.rect, base_color)

        # 获取文本
        text = index.data(Qt.ItemDataRole.DisplayRole)
        if not text:
            return

        # 设置字体
        font = QFont()
        if is_selected:
            font.setBold(True)
        painter.setFont(font)

        # 设置颜色
        if col == 1:  # 包名灰色
            painter.setPen(QColor(100, 100, 100))
        elif is_selected:  # 选中状态深色
            painter.setPen(QColor(30, 30, 30))
        else:
            painter.setPen(QColor(50, 50, 50))

        # 绘制文本
        text_rect = option.rect.adjusted(8, 4, -8, -4)
        alignment = index.data(Qt.ItemDataRole.TextAlignmentRole)
        if alignment is None:
            alignment = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        painter.drawText(text_rect, alignment, text)


class PackageTableModel(QAbstractTableModel):
    """软件列表数据模型"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.packages = []

    def set_packages(self, packages: list):
        """设置软件包列表"""
        self.beginResetModel()
        self.packages = packages
        self.endResetModel()

    def update_package_selection(self, row: int, selected: bool):
        """更新软件选择状态"""
        if 0 <= row < len(self.packages):
            self.packages[row].is_selected = selected
            left = self.index(row, 0)
            right = self.index(row, COLUMN_COUNT - 1)
            self.dataChanged.emit(left, right, [Qt.ItemDataRole.CheckStateRole])

    def get_selected_packages(self) -> list:
        """获取选中的软件包"""
        return [p for p in self.packages if p.is_selected]

    def get_package(self, row: int) -> Package:
        """获取指定行的软件包"""
        if 0 <= row < len(self.packages):
            return self.packages[row]
        return None

    def rowCount(self, parent: QModelIndex = None) -> int:
        return len(self.packages)

    def columnCount(self, parent: QModelIndex = None) -> int:
        return COLUMN_COUNT

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        """获取数据"""
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()
        package = self.packages[row]

        # 文本对齐
        if role == Qt.ItemDataRole.TextAlignmentRole:
            if col in [2, 3, 4, 5]:
                return Qt.AlignmentFlag.AlignCenter
            return Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft

        # 显示数据
        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return ""
            elif col == 1:
                return package.display_name
            elif col == 2:
                return package.size
            elif col == 3:
                return package.source.value
            elif col == 4:
                return package.install_date
            elif col == 5:
                return package.version

        # 复选框状态
        if role == Qt.ItemDataRole.CheckStateRole and col == 0:
            return Qt.CheckState.Checked if package.is_selected else Qt.CheckState.Unchecked

        # 用户数据
        if role == Qt.ItemDataRole.UserRole:
            return package

        return None

    def setData(self, index: QModelIndex, value, role: int = Qt.ItemDataRole.EditRole) -> bool:
        """设置数据"""
        if not index.isValid():
            return False

        row = index.row()
        if 0 <= row < len(self.packages):
            if role == Qt.ItemDataRole.CheckStateRole and index.column() == 0:
                self.packages[row].is_selected = (value == Qt.CheckState.Checked.value)
                left = self.index(row, 0)
                right = self.index(row, COLUMN_COUNT - 1)
                self.dataChanged.emit(left, right, [Qt.ItemDataRole.CheckStateRole])
                return True

        return False

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        """获取标志 - 移除复选框标志，使用自定义绘制"""
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        # 只返回启用和可选标志，不复选框标志
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def headerData(self, section: int, orientation: Qt.Orientation,
                   role: int = Qt.ItemDataRole.DisplayRole):
        """获取表头数据"""
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if 0 <= section < COLUMN_COUNT:
                return COLUMN_HEADERS[section]
        return None


class PackageListWidget(QTableView):
    """软件列表组件"""

    selection_changed = pyqtSignal(list)
    package_double_clicked = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.model = PackageTableModel(self)
        self.setModel(self.model)

        # 设置委托
        self.setItemDelegateForColumn(0, CheckboxDelegate(self))
        for col in range(1, COLUMN_COUNT):
            self.setItemDelegateForColumn(col, TextDelegate(self))

        self._setup_ui()

    def _setup_ui(self):
        """设置 UI"""
        header = self.horizontalHeader()
        header.setStretchLastSection(False)
        header.setHighlightSections(False)

        # 固定宽度列 - 允许用户拖动调整
        for col, width in COLUMN_WIDTHS.items():
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
            self.setColumnWidth(col, width)

        # 拉伸列 - 填充剩余空间
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # 包名
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # 版本

        # 行高
        self.verticalHeader().setDefaultSectionSize(40)
        self.verticalHeader().setVisible(False)

        # 选择行为 - 禁用默认选择，使用自定义
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # 禁用内置排序（使用自定义）
        self.setSortingEnabled(False)

        # 样式
        self.setAlternatingRowColors(False)
        self.setShowGrid(False)
        self.setGridStyle(Qt.PenStyle.NoPen)

        self.setStyleSheet("""
            QTableView {
                background-color: white;
                border: none;
                gridline-color: #f0f0f0;
                selection-background-color: transparent;
            }
            QTableView::item {
                padding: 4px;
            }
            QHeaderView::section {
                background-color: #fafafa;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #e0e0e0;
                font-weight: bold;
                color: #555;
                font-size: 13px;
            }
            QScrollBar:vertical {
                background-color: #f5f5f5;
                width: 12px;
                border-radius: 6px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background-color: #c0c0c0;
                border-radius: 6px;
                min-height: 30px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #a0a0a0;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0;
            }
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: none;
            }
            QScrollBar:horizontal {
                background-color: #f5f5f5;
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background-color: #c0c0c0;
                border-radius: 6px;
                min-width: 30px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #a0a0a0;
            }
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                width: 0;
            }
            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)

        # 滚动模式
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

        # 连接信号
        self.doubleClicked.connect(self._on_double_clicked)

    def mousePressEvent(self, event):
        """处理鼠标按下事件 - 只响应复选框列的点击"""
        from PyQt6.QtCore import QEvent
        
        # 检查是否点击在复选框列
        index = self.indexAt(event.pos())
        if index.isValid() and index.column() == 0:
            # 切换复选框状态
            current = self.model.packages[index.row()].is_selected
            self.model.update_package_selection(index.row(), not current)
            self._emit_selection_changed()
            event.accept()
            return
        
        # 其他情况交给基类处理（包括滚动条）
        super().mousePressEvent(event)

    def load_packages(self, packages: list):
        """加载软件列表"""
        self.model.set_packages(packages)
        self._emit_selection_changed()

    def _on_double_clicked(self, index: QModelIndex):
        """双击事件"""
        package = self.model.get_package(index.row())
        if package:
            self.package_double_clicked.emit(package)

    def _emit_selection_changed(self):
        """发送选择改变信号"""
        selected = self.model.get_selected_packages()
        self.selection_changed.emit(selected)

    def get_selected_packages(self) -> list:
        """获取选中的软件包"""
        return self.model.get_selected_packages()

    def select_all(self):
        """全选"""
        for pkg in self.model.packages:
            pkg.is_selected = True
        self.model.layoutAboutToBeChanged.emit()
        self.model.layoutChanged.emit()
        self.viewport().update()
        self._emit_selection_changed()

    def deselect_all(self):
        """取消全选"""
        for pkg in self.model.packages:
            pkg.is_selected = False
        self.model.layoutAboutToBeChanged.emit()
        self.model.layoutChanged.emit()
        self.viewport().update()
        self._emit_selection_changed()

    def invert_selection(self):
        """反选"""
        for pkg in self.model.packages:
            pkg.is_selected = not pkg.is_selected
        self.model.layoutAboutToBeChanged.emit()
        self.model.layoutChanged.emit()
        self.viewport().update()
        self._emit_selection_changed()

    def get_package_count(self) -> int:
        """获取软件包总数"""
        return self.model.rowCount()

    def get_selected_count(self) -> int:
        """获取选中的软件包数量"""
        return sum(1 for p in self.model.packages if p.is_selected)
