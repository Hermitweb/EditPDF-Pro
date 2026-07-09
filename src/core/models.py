"""数据模型定义"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FindResult:
    """查找结果——PDF中一处文字匹配"""

    id: int
    page_num: int
    rect: tuple[float, float, float, float]  # (x0, y0, x1, y1)
    matched_text: str
    context_before: str = ""
    context_after: str = ""
    replaced: bool = False

    @property
    def page_label(self) -> str:
        return f"第 {self.page_num + 1} 页"

    @property
    def snippet(self) -> str:
        """显示用的摘要文本"""
        ctx = self.context_before[-20:] + \
            f"【{self.matched_text}】" + \
            self.context_after[:20]
        return ctx.strip()


@dataclass
class WatermarkConfig:
    """水印配置"""

    # 文字水印
    text: str = ""
    font_size: int = 24
    font_name: str = "china-s"  # PyMuPDF 内置CJK字体

    # 图片水印
    image_path: str = ""

    # 通用
    color: tuple[int, int, int] = (128, 128, 128)
    opacity: float = 0.3
    rotation: float = 45
    position: str = "center"  # center / tile / top-left / top-right / bottom-left / bottom-right
    pages: str = "all"        # "all" / "range:1-5" / "current"

    @property
    def is_text_mode(self) -> bool:
        return bool(self.text) and not bool(self.image_path)

    @property
    def is_image_mode(self) -> bool:
        return bool(self.image_path)


@dataclass
class DocumentInfo:
    """PDF文档元信息"""

    filepath: str = ""
    filename: str = ""
    page_count: int = 0
    file_size: int = 0
    is_encrypted: bool = False
    title: str = ""
    author: str = ""
    subject: str = ""

    @property
    def file_size_str(self) -> str:
        if self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        return f"{self.file_size / (1024 * 1024):.1f} MB"


@dataclass
class PageThumbnail:
    """缩略图信息"""

    page_num: int
    pixmap: object = None  # QPixmap，运行时赋值避免导入Qt
