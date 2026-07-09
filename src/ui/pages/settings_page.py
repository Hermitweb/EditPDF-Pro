"""设置页面——主题切换、关于信息"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (
    PushButton, CardWidget,
    BodyLabel, TitleLabel, CaptionLabel, StrongBodyLabel,
    FluentIcon,
)

from app.constants import APP_NAME, APP_VERSION
from app.theme import ThemeManager


class SettingsPage(QWidget):
    """设置页面"""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main = main_window
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)

        title = TitleLabel("设置")
        layout.addWidget(title)

        # ── 主题 ──
        theme_card = CardWidget(self)
        theme_layout = QHBoxLayout(theme_card)
        theme_layout.addWidget(BodyLabel("主题模式"))
        toggle_btn = PushButton(FluentIcon.PALETTE, "切换深色/浅色主题")
        toggle_btn.clicked.connect(self.main.toggle_theme)
        theme_layout.addWidget(toggle_btn)
        theme_layout.addStretch()
        layout.addWidget(theme_card)

        # ── 快捷键 ──
        shortcut_card = CardWidget(self)
        sc_layout = QVBoxLayout(shortcut_card)
        sc_layout.addWidget(StrongBodyLabel("快捷键"))
        shortcuts = [
            ("Ctrl+O", "打开PDF"),
            ("Ctrl+S", "保存PDF"),
            ("Ctrl+F", "查找替换"),
            ("+ / -", "放大/缩小"),
            ("0", "重置缩放"),
            ("F3 / Shift+F3", "下一个/上一个匹配"),
            ("PageUp / PageDown", "上一页/下一页"),
            ("Esc", "关闭查找面板"),
        ]
        for key, desc in shortcuts:
            row = QHBoxLayout()
            code = CaptionLabel(key)
            code.setStyleSheet(
                "background: #f0f0f0; padding: 2px 8px; "
                "border-radius: 4px; font-family: monospace;"
            )
            row.addWidget(code)
            row.addWidget(BodyLabel(desc))
            row.addStretch()
            sc_layout.addLayout(row)
        layout.addWidget(shortcut_card)

        # ── 关于 ──
        about_card = CardWidget(self)
        about_layout = QVBoxLayout(about_card)
        about_layout.addWidget(StrongBodyLabel(f"{APP_NAME} v{APP_VERSION}"))
        about_layout.addWidget(
            CaptionLabel("基于 Python + PyMuPDF + PyQt5 + QFluentWidgets")
        )
        about_layout.addWidget(
            CaptionLabel("个人免费使用 · 开源项目")
        )
        layout.addWidget(about_card)

        layout.addStretch()
