"""EditPDF Pro — 应用入口"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from qfluentwidgets import setTheme, Theme

from app.constants import APP_NAME, ORG_NAME
from app.theme import ThemeManager
from ui.main_window import MainWindow


def run():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)

    # 加载 Qt 中文翻译
    try:
        from PyQt5.QtCore import QTranslator
        translator = QTranslator()
        local_qt = os.path.join(os.path.dirname(__file__), "res", "qt_zh_CN.qm")
        if not os.path.exists(local_qt):
            local_qt = os.path.join(getattr(sys, '_MEIPASS', ''), "res", "qt_zh_CN.qm")
        if os.path.exists(local_qt):
            translator.load(local_qt)
        else:
            from PyQt5.QtCore import QLibraryInfo
            translator.load("qt_zh_CN", QLibraryInfo.location(QLibraryInfo.TranslationsPath))
        app.installTranslator(translator)
    except: pass

    ThemeManager.init()

    style_path = os.path.join(os.path.dirname(__file__), "app", "style.qss")
    if os.path.exists(style_path):
        with open(style_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    run()
