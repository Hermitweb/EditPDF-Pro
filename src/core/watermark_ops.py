"""水印操作——文字水印和图片水印"""

import fitz
import os
from core.models import WatermarkConfig


class WatermarkOps:
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
        pages = cls._get_page_range(doc, config.pages)
        count = 0
        total = len(pages)
        for i, page_num in enumerate(pages):
            target_page = doc[page_num]
            rect = target_page.rect
            src_doc = fitz.open()
            src_page = src_doc.new_page(width=rect.width, height=rect.height)
            if config.position == "tile":
                cls._tile_text_on_page(src_page, rect, config)
            else:
                pos = cls.POSITIONS.get(config.position, (0.35, 0.45))
                x = rect.width * pos[0]
                y = rect.height * pos[1]
                src_page.insert_text(
                    (x, y), config.text,
                    fontsize=config.font_size,
                    fontname="china-ss",
                    color=tuple(c / 255 for c in config.color),
                    rotate=int(config.rotation),
                )
            try:
                target_page.show_pdf_page(rect, src_doc, 0, overlay=True)
            except Exception:
                if config.position == "tile":
                    cls._tile_text_on_page(target_page, rect, config)
                else:
                    pos = cls.POSITIONS.get(config.position, (0.35, 0.45))
                    x = rect.width * pos[0]; y = rect.height * pos[1]
                    target_page.insert_text((x, y), config.text,
                        fontsize=config.font_size, fontname="china-ss",
                        color=tuple(c/255 for c in config.color),
                        rotate=int(config.rotation))
            src_doc.close()
            count += 1
            if progress_callback:
                progress_callback(i + 1, total)
        return count

    @classmethod
    def _tile_text_on_page(cls, page, page_rect, config):
        step_x = 200
        step_y = 150
        angle = int(config.rotation)
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
                page.insert_image(img_rect, filename=config.image_path, overlay=True)
            count += 1
            if progress_callback:
                progress_callback(i + 1, total)
        return count

    @staticmethod
    def _tile_image(page, page_rect, config):
        if not config.image_path: return
        step_x = 200; step_y = 200
        for x in range(0, int(page_rect.width), step_x):
            for y in range(0, int(page_rect.height), step_y):
                img_rect = fitz.Rect(x, y, x + 80, y + 40)
                page.insert_image(img_rect, filename=config.image_path, overlay=True)

    @staticmethod
    def _get_page_range(doc, pages_setting: str) -> list[int]:
        all_pages = list(range(doc.page_count))
        if pages_setting == "all": return all_pages
        if pages_setting == "current": return [0]
        if pages_setting.startswith("range:"):
            try:
                parts = pages_setting.replace("range:", "").split("-")
                return [p for p in all_pages if int(parts[0])-1 <= p <= int(parts[1])-1]
            except: return all_pages
        return all_pages
