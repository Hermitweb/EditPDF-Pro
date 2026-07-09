"""主题管理——亮色/暗色切换"""

from PyQt5.QtCore import QObject, pyqtSignal
from qfluentwidgets import setTheme, setThemeColor, Theme


class ThemeManager(QObject):
    """全局主题管理"""

    theme_changed = pyqtSignal(str)  # "light" / "dark"

    _current_theme: str = "light"

    @classmethod
    def init(cls):
        """初始化主题"""
        setTheme(Theme.LIGHT)
        setThemeColor("#0078D4")  # Fluent Blue
        cls._current_theme = "light"

    @classmethod
    def toggle(cls) -> str:
        """切换亮/暗主题"""
        if cls._current_theme == "light":
            setTheme(Theme.DARK)
            cls._current_theme = "dark"
        else:
            setTheme(Theme.LIGHT)
            cls._current_theme = "light"
        return cls._current_theme

    @classmethod
    def set_light(cls):
        setTheme(Theme.LIGHT)
        cls._current_theme = "light"

    @classmethod
    def set_dark(cls):
        setTheme(Theme.DARK)
        cls._current_theme = "dark"

    @classmethod
    def is_dark(cls) -> bool:
        return cls._current_theme == "dark"
