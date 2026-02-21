#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进度对话框 - 显示操作进度
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QProgressBar,
                             QPushButton, QTextEdit, QWidget, QHBoxLayout)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QTextCursor


class ProgressThread(QThread):
    """后台任务线程"""
    progress_update = pyqtSignal(str, int)
    task_complete = pyqtSignal(bool, str)

    def __init__(self, task_func, *args, **kwargs):
        super().__init__()
        self.task_func = task_func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.task_func(
                lambda msg, pct: self.progress_update.emit(msg, pct),
                lambda msg: self.progress_update.emit(msg, -1),
                *self.args,
                **self.kwargs
            )
            self.task_complete.emit(True, result)
        except Exception as e:
            self.task_complete.emit(False, str(e))


class ProgressDialog(QDialog):
    """进度对话框"""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(500, 300)
        self.setModal(True)

        self._setup_ui()

    def _setup_ui(self):
        """设置 UI"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        self.setLayout(layout)

        # 标题
        self.title_label = QLabel(self.windowTitle())
        self.title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(self.title_label)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # 状态标签
        self.status_label = QLabel("准备中...")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # 日志区域
        log_group = QWidget()
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(0, 0, 0, 0)

        log_label = QLabel("详细日志:")
        log_label.setStyleSheet("font-weight: bold;")
        log_layout.addWidget(log_label)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setFont(QFont("Consolas", 9))
        log_layout.addWidget(self.log_text)

        layout.addWidget(log_group)

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.close_btn = QPushButton("关闭")
        self.close_btn.setEnabled(False)
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

    def start_task(self, task_func, *args, **kwargs):
        """启动后台任务"""
        self.thread = ProgressThread(task_func, *args, **kwargs)
        self.thread.progress_update.connect(self._on_progress_update)
        self.thread.task_complete.connect(self._on_task_complete)
        self.thread.start()

    def _on_progress_update(self, message: str, percent: int):
        """进度更新"""
        self.status_label.setText(message)

        if percent >= 0:
            self.progress_bar.setValue(percent)

        # 添加到日志
        self._append_log(message)

    def _append_log(self, message: str):
        """添加日志"""
        self.log_text.append(message)
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)

    def _on_task_complete(self, success: bool, message: str):
        """任务完成"""
        if success:
            self.progress_bar.setValue(100)
            self.status_label.setText("[完成] 操作完成")
            self._append_log(f"[完成] {message}")
        else:
            self.status_label.setText(f"[失败] 操作失败：{message}")
            self._append_log(f"[失败] 错误：{message}")

        self.close_btn.setEnabled(True)

    def get_result(self):
        """获取结果"""
        return self.log_text.toPlainText()
