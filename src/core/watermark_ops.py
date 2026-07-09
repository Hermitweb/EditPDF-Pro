"""水印操作——文字水印和图片水印"""

import fitz
import os
from core.models import WatermarkConfig


class WatermarkOps:
    """水印添加操作"""

    POSITIONS = {
        "top-left": (0.05, 0.05),
        "top-right": (0.85, 0.05),
        "center": (0.35, 0.45),
        "bottom-left": (0.05, 0.85),
        "bottom-right": (0.85, 0.85),
    }

    @classmethod
    def add_text_watermark(cls, doc, config: WatermarkConfig,
                           progress_callback=None) -> int:
        """使用图层叠加方式添加文字水印（支持任意角度旋转）"""
        pages = cls._get_page_range(doc, config.pages)
        count = 0
        total = len(pages)

        for i, page_num in enumerate(pages):
            target_page = doc[page_num]
            rect = target_page.rect

            # 创建临时页面作为水印源
            src_doc = fitz.open()
            src_page = src_doc.new_page(width=rect.width, height=rect.height)

            if config.position == "tile":
                cls._tile_text_on_page(src_page, rect, config)
            else:
                pos = cls.POSITIONS.get(config.position, (0.35, 0.45))
                x = rect.width * pos[0]
                y = rect.height * pos[1]
                alpha = max(0.05, config.opacity)
                src_page.insert_text(
                    (x, y), config.text,
                    fontsize=config.font_size,
                    fontname="china-ss",
                    color=tuple(c / 255 for c in config.color),
                    rotate=int(config.rotation // 90 * 90),
                )

            # 叠加到目标页面
            target_page.show_pdf_page(rect, src_doc, 0, overlay=True)
            src_doc.close()
            count += 1
            if progress_callback:
                progress_callback(i + 1, total)

        return count

    @classmethod
    def _tile_text_on_page(cls, page, page_rect, config):
        """在临时页面上平铺文字"""
        step_x = 200
        step_y = 150
        angle = int(config.rotation // 90 * 90)
        color = tuple(c / 255 for c in config.color)
        for x in range(0, int(page_rect.width), step_x):
            for y in range(0, int(page_rect.height), step_y):
                page.insert_text(
                    (x, y), config.text,
                    fontsize=config.font_size * 6 // 10,
                    fontname="china-ss",
                    color=color,
                    rotate=angle,
                )

    @classmethod
    def add_image_watermark(cls, doc, config: WatermarkConfig,
                            progress_callback=None) -> int:
        """添加图片水印"""
        if not os.path.exists(config.image_path):
            raise FileNotFoundError(f"图片文件不存在: {config.image_path}")

        pages = cls._get_page_range(doc, config.pages)
        count = 0
        total = len(pages)

        for i, page_num in enumerate(pages):
            page = doc[page_num]
            rect = page.rect

            if config.position == "tile":
                cls._tile_image(page, rect, config)
            else:
                pos = cls.POSITIONS.get(config.position, (0.35, 0.45))
                img_width = rect.width * 0.2
                img_rect = fitz.Rect(
                    rect.width * pos[0], rect.height * pos[1],
                    rect.width * pos[0] + img_width,
                    rect.height * pos[1] + img_width * 0.3,
                )
                page.insert_image(
                    img_rect, filename=config.image_path, overlay=True,
                )
            count += 1
            if progress_callback:
                progress_callback(i + 1, total)

        return count

    @staticmethod
    def _tile_image(page, page_rect, config):
        if not config.image_path:
            return
        step_x = 200
        step_y = 200
        for x in range(0, int(page_rect.width), step_x):
            for y in range(0, int(page_rect.height), step_y):
                img_rect = fitz.Rect(x, y, x + 80, y + 40)
                page.insert_image(img_rect, filename=config.image_path,
                                  overlay=True)

    @staticmethod
    def _get_page_range(doc, pages_setting: str) -> list[int]:
        all_pages = list(range(doc.page_count))
        if pages_setting == "all":
            return all_pages
        if pages_setting == "current":
            return [0]
        if pages_setting.startswith("range:"):
            try:
                parts = pages_setting.replace("range:", "").split("-")
                start = int(parts[0]) - 1
                end = int(parts[1]) - 1
                return [p for p in all_pages if start <= p <= end]
            except (ValueError, IndexError):
                return all_pages
        return all_pages
