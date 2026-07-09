"""PDF页面渲染引擎——将PDF页面渲染为Qt图像"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from app.constants import PREVIEW_DPI, THUMBNAIL_DPI


class Renderer:
    """将PyMuPDF页面渲染为QImage/QPixmap"""

    @staticmethod
    def render_page(page, dpi: int = PREVIEW_DPI) -> QImage:
        mat = page.get_pixmap(dpi=dpi)
        return QImage(
            mat.samples_ptr, mat.width, mat.height, mat.stride,
            QImage.Format_RGB888,
        ).copy()

    @staticmethod
    def render_pixmap(page, dpi: int = PREVIEW_DPI) -> QPixmap:
        return QPixmap.fromImage(Renderer.render_page(page, dpi))

    @staticmethod
    def render_thumbnail(page, dpi: int = THUMBNAIL_DPI) -> QPixmap:
        return Renderer.render_pixmap(page, dpi)

    @staticmethod
    def render_page_with_highlights(
        page,
        rects: list[tuple[float, float, float, float]],
        active_idx: int = -1,
        dpi: int = PREVIEW_DPI,
    ) -> QImage:
        """渲染页面，普通匹配黄色高亮，选中匹配橙色高亮"""
        from PyQt5.QtGui import QPainter, QColor, QPen

        img = Renderer.render_page(page, dpi)
        if not rects:
            return img

        scale = dpi / 72.0
        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing)

        for i, rect in enumerate(rects):
            x = int(rect[0] * scale)
            y = int(rect[1] * scale)
            w = int((rect[2] - rect[0]) * scale)
            h = int((rect[3] - rect[1]) * scale)

            if i == active_idx:
                # 选中的匹配：橙色高亮 + 红色粗边框
                painter.fillRect(x, y, w, h, QColor(255, 140, 0, 140))
                painter.setPen(QPen(QColor(255, 0, 0), 3))
            else:
                # 普通匹配：黄色半透明 + 红色细边框
                painter.fillRect(x, y, w, h, QColor(255, 235, 59, 80))
                painter.setPen(QPen(QColor(255, 0, 0), 1))
            painter.drawRect(x, y, w, h)

        painter.end()
        return img
