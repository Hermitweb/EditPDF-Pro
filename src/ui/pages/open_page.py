"""打开文件页面——最近文件、快速打开"""

import os
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFileDialog, QPushButton, QListWidget, QListWidgetItem,
)
from qfluentwidgets import (
    PrimaryPushButton, CardWidget, BodyLabel, TitleLabel,
    CaptionLabel, FluentIcon, InfoBar,
)


class OpenPage(QWidget):
    """打开文件页面"""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main = main_window
        self._recent_files = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)

        # 标题
        title = TitleLabel("打开PDF文件")
        layout.addWidget(title)

        # 打开按钮
        btn = PrimaryPushButton(FluentIcon.DOCUMENT, "从文件夹选择...")
        btn.clicked.connect(self.main.open_file_dialog)
        btn.setFixedWidth(240)
        layout.addWidget(btn)

        # 提示
        hint = BodyLabel("或直接拖拽PDF文件到主预览区域")
        hint.setStyleSheet("color: #888;")
        layout.addWidget(hint)

        layout.addSpacing(20)

        # 最近文件
        recent_label = BodyLabel("最近打开的文件")
        layout.addWidget(recent_label)

        self.recent_list = QListWidget()
        self.recent_list.setAlternatingRowColors(True)
        self.recent_list.itemDoubleClicked.connect(self._on_recent_clicked)
        layout.addWidget(self.recent_list, 1)

        layout.addStretch()

        # 初始填充
        self._refresh_recent()

    def _on_recent_clicked(self, item):
        path = item.data(Qt.UserRole)
        if path and os.path.exists(path):
            self.main.engine.open(path)
            self.main.find_panel.setVisible(True)
            self.main.find_input.setFocus()
        else:
            InfoBar.warning(
                title="", content="文件不存在或已被移动",
                orient=Qt.Horizontal, isClosable=True,
                duration=3000, parent=self,
            )
            # 从列表移除
            row = self.recent_list.row(item)
            self.recent_list.takeItem(row)

    def add_recent(self, filepath: str):
        """添加最近文件"""
        if filepath in self._recent_files:
            self._recent_files.remove(filepath)
        self._recent_files.insert(0, filepath)
        if len(self._recent_files) > 10:
            self._recent_files = self._recent_files[:10]
        self._refresh_recent()

    def _refresh_recent(self):
        self.recent_list.clear()
        for fp in self._recent_files:
            name = os.path.basename(fp)
            item = QListWidgetItem(f"📄 {name}")
            item.setData(Qt.UserRole, fp)
            item.setToolTip(fp)
            self.recent_list.addItem(item)
