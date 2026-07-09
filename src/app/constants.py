"""应用常量和配置定义"""

# 应用信息
APP_NAME = "EditPDF Pro"
APP_VERSION = "0.1.0"
APP_DESCRIPTION = "一站式PDF桌面编辑器"
ORG_NAME = "EditPDF"

# 渲染DPI
PREVIEW_DPI = 120       # 预览渲染DPI
THUMBNAIL_DPI = 40      # 缩略图渲染DPI
EXPORT_DPI = 200         # 导出渲染DPI

# 缓存
MAX_CACHE_PAGES = 3      # 预览缓存页数
THUMBNAIL_CACHE_SIZE = 50  # 缩略图缓存上限

# 文件
FILE_EXTENSIONS = ["*.pdf"]
FILE_FILTER = "PDF文件 (*.pdf)"

# 页面尺寸预设 (mm)
PAGE_SIZES = {
    "A3": (297, 420),
    "A4": (210, 297),
    "A5": (148, 210),
    "Letter": (216, 279),
    "Legal": (216, 356),
}

# 水印
WATERMARK_DEFAULT_OPACITY = 0.3
WATERMARK_DEFAULT_ROTATION = 45
WATERMARK_DEFAULT_FONT_SIZE = 24

# 缩放
ZOOM_LEVELS = [50, 75, 100, 125, 150, 200]
ZOOM_DEFAULT = 100

# 旋转
ROTATION_ANGLES = [90, 180, 270]

# 快捷键（仅用于文档显示，实际绑定在UI层）
SHORTCUTS = {
    "open": "Ctrl+O",
    "save": "Ctrl+S",
    "find": "Ctrl+F",
    "find_next": "F3",
    "find_prev": "Shift+F3",
    "replace": "Ctrl+H",
    "replace_all": "Ctrl+Shift+H",
    "zoom_in": "Ctrl+Plus",
    "zoom_out": "Ctrl+Minus",
    "fit_width": "Ctrl+0",
}
