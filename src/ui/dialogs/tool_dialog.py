"""对话框包装器——将工具页面包装为弹出对话框"""

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import Qt
from qfluentwidgets import PrimaryPushButton, FluentIcon


class ToolDialog(QDialog):
    """通用工具对话框"""

    def __init__(self, title: str, page_widget, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowModality(Qt.ApplicationModal)
        self.resize(520, 450)
        self.setMinimumSize(400, 300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 嵌入页面
        layout.addWidget(page_widget, 1)

        # 底部关闭按钮
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()
        close_btn = PrimaryPushButton(FluentIcon.CLOSE, "关闭")
        close_btn.clicked.connect(self.close)
        btn_bar.addWidget(close_btn)
        btn_bar.setContentsMargins(16, 8, 16, 8)
        layout.addLayout(btn_bar)
