"""全局信号总线——跨组件通信"""

from PyQt5.QtCore import QObject, pyqtSignal


class SignalBus(QObject):
    """应用级别的全局信号总线（单例）"""

    # 文件操作
    file_opened = pyqtSignal(str, int)       # 文件路径, 页数
    file_saved = pyqtSignal(str)              # 文件路径

    # 导航
    page_navigated = pyqtSignal(int, int)     # 当前页, 总页数
    zoom_changed = pyqtSignal(int)            # 缩放百分比

    # 查找替换
    find_requested = pyqtSignal(str)          # 查找文本
    replace_requested = pyqtSignal(str, str)  # 旧文本, 新文本

    # 状态
    status_message = pyqtSignal(str)          # 状态栏消息
    operation_started = pyqtSignal(str)       # 操作名称
    operation_finished = pyqtSignal(str)      # 操作名称
    progress_updated = pyqtSignal(int, int)   # 当前值, 总值

    # 主题
    theme_changed = pyqtSignal(str)           # "light" / "dark"


# 全局单例
signal_bus = SignalBus()
