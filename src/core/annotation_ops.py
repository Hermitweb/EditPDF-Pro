"""注释操作——高亮、下划线、添加文本注释"""

import fitz


class AnnotationOps:
    """PDF注释（批注）操作"""

    @staticmethod
    def add_highlight(page, rect: tuple,
                      color: tuple = (1, 1, 0)) -> bool:
        """添加高亮注释"""
        try:
            annot = page.add_highlight_annot(
                fitz.Rect(rect[0], rect[1], rect[2], rect[3])
            )
            annot.set_colors(stroke=color)
            annot.update()
            return True
        except Exception as e:
            print(f"添加高亮失败: {e}")
            return False

    @staticmethod
    def add_underline(page, rect: tuple,
                      color: tuple = (0, 1, 0)) -> bool:
        """添加下划线注释"""
        try:
            annot = page.add_underline_annot(
                fitz.Rect(rect[0], rect[1], rect[2], rect[3])
            )
            annot.set_colors(stroke=color)
            annot.update()
            return True
        except Exception as e:
            print(f"添加下划线失败: {e}")
            return False

    @staticmethod
    def add_strikeout(page, rect: tuple,
                      color: tuple = (1, 0, 0)) -> bool:
        """添加删除线注释"""
        try:
            annot = page.add_strikeout_annot(
                fitz.Rect(rect[0], rect[1], rect[2], rect[3])
            )
            annot.set_colors(stroke=color)
            annot.update()
            return True
        except Exception as e:
            print(f"添加删除线失败: {e}")
            return False

    @staticmethod
    def add_text_annotation(page, text: str,
                            pos: tuple) -> bool:
        """在指定位置添加文字便签注释"""
        try:
            page.add_text_annot(
                (pos[0], pos[1]),
                text,
                icon="Note",
            )
            return True
        except Exception as e:
            print(f"添加文字注释失败: {e}")
            return False

    @staticmethod
    def add_free_text(page, text: str, rect: tuple,
                      fontsize: int = 12,
                      color: tuple = (0, 0, 0)) -> bool:
        """在页面上直接添加文字（不是注释，是内容）"""
        try:
            page.insert_text(
                (rect[0], rect[1]),
                text,
                fontsize=fontsize,
                color=color,
            )
            return True
        except Exception as e:
            print(f"添加自由文字失败: {e}")
            return False

    @staticmethod
    def get_annotations(page) -> list[dict]:
        """获取页面上所有注释"""
        annots = []
        for annot in page.annots():
            if annot:
                annots.append({
                    "type": str(annot.type),
                    "info": annot.info,
                    "rect": (annot.rect.x0, annot.rect.y0,
                             annot.rect.x1, annot.rect.y1),
                    "content": annot.info.get("content", ""),
                })
        return annots
