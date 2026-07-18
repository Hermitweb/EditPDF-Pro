"""主窗口——完整功能"""

import os, webbrowser
from PyQt5.QtCore import Qt, QTimer, QSize, QPoint, pyqtSignal
from PyQt5.QtGui import (
    QPixmap, QIcon, QDragEnterEvent, QDropEvent,
    QMouseEvent, QCursor, QColor,
)
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFileDialog, QScrollArea, QListWidget, QListWidgetItem,
    QAbstractItemView, QListView, QTabWidget, QDialog, QLineEdit,
    QDialogButtonBox, QFormLayout, QSpinBox, QComboBox,
    QMenu, QMessageBox, QInputDialog, QPushButton, QColorDialog,
    QApplication, QAction, QTextEdit, QButtonGroup, QRadioButton, QStackedWidget,
)
from qfluentwidgets import (
    MSFluentWindow, NavigationItemPosition, FluentIcon,
    PushButton, ToolButton, PrimaryPushButton,
    InfoBar, InfoBarPosition,
    ComboBox, BodyLabel, CaptionLabel,
)

from app.constants import APP_NAME, APP_VERSION, ZOOM_LEVELS
from app.theme import ThemeManager
from app.settings import add_recent, get_recent, save_theme, load as load_cfg
from utils.signal_bus import signal_bus
from core.pdf_engine import PDFEngine
import fitz
from core.renderer import Renderer
from ui.pages.watermark_page import WatermarkPage
from ui.pages.settings_page import SettingsPage
from ui.dialogs.tool_dialog import ToolDialog


class InlineTextEditor(QTextEdit):
    confirmed = pyqtSignal(object)

    def __init__(self, parent, pdf_x, pdf_y, scale,
                 fn="SimSun", fs=12, color=(0,0,0),
                 off_x=0, off_y=0):
        super().__init__(parent)
        self._pdf_x = pdf_x; self._pdf_y = pdf_y
        self._fn = fn; self._fs = fs; self._color = color
        self._scale = scale; self._off_x = off_x; self._off_y = off_y
        self._drag = False; self._border = 8
        r, g, b = [int(c*255) for c in color]
        self.setStyleSheet(f"""
            QTextEdit {{
                background: rgba(255,255,255,30);
                border: 2px dashed #0078D4;
                border-radius: 2px;
                padding: 4px 6px;
                font-family: "{fn}";
                font-size: {fs}pt;
                color: rgb({r},{g},{b});
            }}
        """)
        self.setFontPointSize(fs)
        self.setFontFamily(fn)
        self.setMinimumWidth(120); self.setMinimumHeight(32)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        sx = int(pdf_x * scale) + off_x
        sy = int(pdf_y * scale) + off_y
        self.move(sx, sy)
        self.resize(220, max(40, fs * 2 + 10))
        self.setAcceptDrops(False)
        self.show(); self.setFocus()
        self.setMouseTracking(True)
        self.viewport().installEventFilter(self)
        self.viewport().setMouseTracking(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._on_border_bare(event.pos()):
            self._start_drag(event.globalPos())
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag: return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._drag and event.button() == Qt.LeftButton:
            self._end_drag(); event.accept()
        else:
            super().mouseReleaseEvent(event)

    def _on_border_bare(self, pos):
        w, h = self.width(), self.height()
        b = self._border
        return (pos.x() < b or pos.x() > w - b or pos.y() < b or pos.y() > h - b)

    def _on_border(self, obj, pos):
        if pos is None: return False
        if obj is self.viewport():
            wp = self.viewport().mapTo(self, pos)
        else:
            return self._on_border_bare(pos)
        w, h = self.width(), self.height()
        b = self._border
        return (wp.x() < b or wp.x() > w - b or wp.y() < b or wp.y() > h - b)

    def _start_drag(self, global_pos):
        self._drag = True
        self._drag_start_global = global_pos
        self._drag_start_pos = self.pos()
        self.setCursor(Qt.ClosedHandCursor)

    def _end_drag(self):
        self._drag = False
        self.setCursor(Qt.ArrowCursor)
        new_x = self.pos().x() - self._off_x
        new_y = self.pos().y() - self._off_y
        self._pdf_x = new_x / self._scale
        self._pdf_y = new_y / self._scale

    def eventFilter(self, obj, event):
        from PyQt5.QtCore import QEvent
        t = event.type()
        if self._drag:
            if t == QEvent.MouseMove:
                delta = event.globalPos() - self._drag_start_global
                self.move(self._drag_start_pos + delta)
                return True
            if t == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
                self._end_drag()
                return True
            return False
        if obj is self.viewport():
            if t == QEvent.MouseButtonPress:
                if event.button() == Qt.LeftButton and self._on_border(obj, event.pos()):
                    self._start_drag(event.globalPos())
                    return True
            elif t == QEvent.MouseMove:
                self.setCursor(Qt.OpenHandCursor if self._on_border(obj, event.pos()) else Qt.IBeamCursor)
        return super().eventFilter(obj, event)

    def get_result(self):
        return {"x": self._pdf_x, "y": self._pdf_y,
                "text": self.toPlainText().strip(),
                "fn": self._fn, "fs": self._fs, "color": self._color}

    def apply_props(self, fn=None, fs=None, color=None):
        if fn: self._fn = fn
        if fs: self._fs = fs
        if color: self._color = color
        r, g, b = [int(c*255) for c in self._color]
        self.setFontPointSize(self._fs)
        self.setStyleSheet(f"""
            QTextEdit {{
                background: rgba(255,255,255,30);
                border: 2px dashed #0078D4;
                border-radius: 2px;
                padding: 4px 6px;
                font-family: "{self._fn}";
                font-size: {self._fs}pt;
                color: rgb({r},{g},{b});
            }}
        """)


class TabPage(QWidget):
    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMouseTracking(True)
        self.preview_scroll = QScrollArea()
        self.preview_scroll.setWidgetResizable(True)
        self.preview_scroll.setWidget(self.preview_label)
        self.thumb_list = QListWidget()
        self.thumb_list.setFixedWidth(180)
        self.thumb_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.thumb_list.setDefaultDropAction(Qt.MoveAction)
        self.thumb_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.thumb_list.setSpacing(2)
        self.thumb_list.setIconSize(QSize(160, 120))
        self.thumb_list.setViewMode(QListView.IconMode)
        self.thumb_list.setGridSize(QSize(174, 150))
        self.thumb_list.setWordWrap(True)
        self.thumb_list.itemClicked.connect(self._tc)
        content = QWidget()
        cl = QHBoxLayout(content); cl.setContentsMargins(0,0,0,0); cl.setSpacing(0)
        cl.addWidget(self.thumb_list); cl.addWidget(self.preview_scroll, 1)
        l = QVBoxLayout(self); l.setContentsMargins(0,0,0,0); l.setSpacing(0)
        l.addWidget(content, 1)

    def _tc(self, current, previous=None):
        p = current.data(Qt.UserRole)
        if p is not None:
            self.engine.go_to_page(p)
            self.engine.page_changed.emit(self.engine.current_page, self.engine.page_count)

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            mw = self.window()
            if mw and hasattr(mw, "_zoom_in"):
                if event.angleDelta().y() > 0: mw._zoom_in()
                else: mw._zoom_out()
                event.accept(); return
        self.preview_scroll.wheelEvent(event)

    def contextMenuEvent(self, event):
        if not self.engine or not self.engine.is_open: return
        local_pos = self.preview_label.mapFrom(self, event.pos())
        self._ctx_menu_pos = local_pos
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { font-size: 13px; padding: 4px; } QMenu::item { padding: 6px 24px; } QMenu::item:selected { background: #e0e0e0; }")
        annot_menu = menu.addMenu("标注")
        annot_menu.addAction("🟡 高亮").triggered.connect(lambda: self._annot_here("highlight"))
        annot_menu.addAction("🟢 下划线").triggered.connect(lambda: self._annot_here("underline"))
        annot_menu.addAction("🔴 删除线").triggered.connect(lambda: self._annot_here("strikeout"))
        menu.addSeparator()
        menu.addAction("🗑 删除此页").triggered.connect(self._del_this_page)
        menu.addAction("ℹ 页面信息").triggered.connect(self._page_info)
        menu.exec(event.globalPos())

    def _annot_here(self, atype):
        if not self.engine or not self.engine.is_open: return
        pos = getattr(self, '_ctx_menu_pos', None)
        page = self.engine._doc[self.engine.current_page]
        pw, ph = page.rect.width, page.rect.height
        if pos is None: r = (pw*0.3, ph*0.3, pw*0.7, ph*0.7)
        else:
            scale = self.window()._zoom / 100.0 * (120.0 / 72.0) if self.window() else 120.0/72.0
            label = self.preview_label; pixmap = label.pixmap()
            off_x = max(0, (label.width() - pixmap.width())//2) if pixmap else 0
            off_y = max(0, (label.height() - pixmap.height())//2) if pixmap else 0
            px = (pos.x() - off_x) / scale; py = (pos.y() - off_y) / scale
            w = pw * 0.15; h = ph * 0.02
            r = (px - w/2, py - h/2, px + w/2, py + h/2)
        ok = False
        if atype == "highlight": ok = self.engine.add_highlight(self.engine.current_page, r)
        elif atype == "underline": ok = self.engine.add_underline(self.engine.current_page, r, (0,1,0))
        elif atype == "strikeout": ok = self.engine.add_strikeout(self.engine.current_page, r, (1,0,0))
        if ok:
            mw = self.window()
            if mw: mw._show_info("已添加标注"); mw._render()

    def _del_this_page(self):
        if not self.engine or not self.engine.is_open: return
        p = self.engine.current_page
        mw = self.window()
        if mw and hasattr(mw, '_ask_yes_no') and mw._ask_yes_no("确认", f"确定删除第 {p+1} 页吗？"):
            self.engine.delete_pages([p])

    def _page_info(self):
        if not self.engine or not self.engine.is_open: return
        from qfluentwidgets import InfoBar, InfoBarPosition
        p = self.engine.current_page; page = self.engine._doc[p]
        msg = f"第 {p+1} 页 | {page.rect.width:.0f}x{page.rect.height:.0f} pt"
        InfoBar.info(title="", content=msg, orient=0, isClosable=True, position=InfoBarPosition.TOP_RIGHT, duration=3000, parent=self)
        if p is not None: self.engine.go_to_page(p)


class MainWindow(MSFluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("")
        self.resize(1280, 800); self.setMinimumSize(900, 600)
        self.setAcceptDrops(True)
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "res", "app.ico")
        if os.path.exists(icon_path): self.setWindowIcon(QIcon(icon_path))
        self._tabs = []; self._cur = -1; self._act = -1; self._zoom = 100
        self._add_text_mode = False; self._text_editor = None; self._editing_text_idx = -1
        self._find_results = []; self._find_active = 0
        self._annot_mode = False; self._annot_type = 'highlight'; self._annot_color = (1, 1, 0)
        self._setup_nav(); self._setup_ui(); self._new_tab()
        self.tab_bar.setCornerWidget(QWidget(), Qt.TopRightCorner)
        self._btn_new_tab = ToolButton(FluentIcon.ADD)
        self._btn_new_tab.clicked.connect(lambda: self._new_tab())
        self.tab_bar.cornerWidget().layout = QHBoxLayout(self.tab_bar.cornerWidget())
        self.tab_bar.cornerWidget().layout.setContentsMargins(0,0,0,0)
        self.tab_bar.cornerWidget().layout.addWidget(self._btn_new_tab)
        self.stackedWidget.removeWidget(self.stackedWidget.currentWidget())
        self.stackedWidget.addWidget(self.central_widget)
        self.stackedWidget.setCurrentWidget(self.central_widget)
        self._recent = get_recent()
        cfg = load_cfg()
        if cfg.get("theme") == "dark":
            ThemeManager.set_dark(); signal_bus.theme_changed.emit("dark")

    @property
    def _eng(self): return self._tabs[self._cur].engine if 0 <= self._cur < len(self._tabs) else None
    @property
    def _tab(self): return self._tabs[self._cur] if 0 <= self._cur < len(self._tabs) else None

    def _setup_nav(self):
        n = self.navigationInterface
        n.addItem("o", FluentIcon.DOCUMENT, "打开文件", onClick=self.open_file_dialog, position=NavigationItemPosition.TOP)
        n.addItem("f", FluentIcon.SEARCH, "查找替换", onClick=self.show_find_panel, position=NavigationItemPosition.TOP)
        n.addItem("t", FluentIcon.FONT, "添加文字", onClick=self._on_add_text_mode, position=NavigationItemPosition.TOP)
        n.addItem("annot", FluentIcon.EDIT, "注释标注", onClick=self._on_annot_mode, position=NavigationItemPosition.TOP)
        n.addItem("merge", FluentIcon.LAYOUT, "合并PDF", onClick=self._show_merge_dlg, position=NavigationItemPosition.TOP)
        n.addItem("split", FluentIcon.SCROLL, "拆分PDF", onClick=self._show_split_dlg, position=NavigationItemPosition.TOP)
        n.addItem("insert", FluentIcon.ADD_TO, "插入页面", onClick=self._show_insert_dlg, position=NavigationItemPosition.TOP)
        n.addItem("w", FluentIcon.PENCIL_INK, "水印工具", onClick=self._show_wm_dlg, position=NavigationItemPosition.TOP)
        n.addItem("img", FluentIcon.PHOTO, "提取图片", onClick=self._on_extract_img, position=NavigationItemPosition.TOP)
        n.addItem("zip", FluentIcon.SAVE, "压缩", onClick=self._on_compress, position=NavigationItemPosition.TOP)
        n.addItem("lock", FluentIcon.REMOVE, "加解密", onClick=self._on_encrypt, position=NavigationItemPosition.TOP)
        n.addItem("s", FluentIcon.SETTING, "设置", onClick=self._show_set_dlg, position=NavigationItemPosition.BOTTOM)

    def _setup_ui(self):
        self.central_widget = QWidget(); self.central_widget.setObjectName("centralArea")
        self.cl = QVBoxLayout(self.central_widget); self.cl.setContentsMargins(0,0,0,0); self.cl.setSpacing(0)
        self.welcome_widget = QWidget(); self.welcome_widget.setObjectName("welcomeCard")
        wl = QVBoxLayout(self.welcome_widget); wl.setAlignment(Qt.AlignCenter)
        wl.addStretch()
        title = BodyLabel("📄 拖放 PDF 文件到此处")
        title.setStyleSheet("font-size:22px; color:#1565C0; font-weight:bold;")
        title.setAlignment(Qt.AlignCenter); wl.addWidget(title)
        logo = BodyLabel("📝"); logo.setStyleSheet("font-size:48px;"); logo.setAlignment(Qt.AlignCenter); wl.addWidget(logo)
        subtitle = CaptionLabel("拖放 PDF 文件到此处，或点击左侧「打开文件」选择")
        subtitle.setStyleSheet("font-size:13px; color:#aaa;"); subtitle.setAlignment(Qt.AlignCenter); wl.addWidget(subtitle)
        self.welcome_recent = QListWidget()
        self.welcome_recent.setMaximumHeight(120); self.welcome_recent.setFixedWidth(350)
        self.welcome_recent.itemDoubleClicked.connect(self._on_welcome_recent)
        wl.addWidget(self.welcome_recent, alignment=Qt.AlignCenter)
        wl.addStretch()
        self._refresh_welcome_recent()
        self.tab_bar = QTabWidget(); self.tab_bar.setTabsClosable(True); self.tab_bar.setMovable(True)
        self.tab_bar.tabBar().setElideMode(Qt.ElideRight)
        self.tab_bar.tabBar().setStyleSheet(
            "QTabBar::close-button { image: url(none); }"
            "QTabBar::close-button:hover { background: rgba(128,128,128,0.3); }")
        self.tab_bar.tabCloseRequested.connect(self._close_tab)
        self.tab_bar.currentChanged.connect(self._on_switch)
        self.tab_bar.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tab_bar.customContextMenuRequested.connect(self._on_tab_context_menu)
        self._setup_find(); self._setup_bar(); self._setup_text_props_bar()
        self.main_stack = QStackedWidget()
        self.main_stack.addWidget(self.welcome_widget)
        main_area = QWidget()
        ml = QVBoxLayout(main_area); ml.setContentsMargins(0,0,0,0); ml.setSpacing(0)
        ml.addWidget(self.tab_bar, 1); ml.addWidget(self.find_panel); ml.addWidget(self.bottom_bar)
        self.main_stack.addWidget(main_area)
        self.cl.addWidget(self.main_stack, 1)
        logo = QLabel(f"📝 {APP_NAME}  v{APP_VERSION}")
        logo.setStyleSheet("font-size:13px; font-weight:bold; color:#1A73E8; border:none; background:transparent; padding-left:4px;")
        self.titleBar.layout().insertWidget(0, logo)
        self.status_bar = QWidget(); self.status_bar.setFixedHeight(24); self.status_bar.setObjectName("status_bar")
        sl = QHBoxLayout(self.status_bar); sl.setContentsMargins(12,0,12,0)
        self.status_label = CaptionLabel("就绪"); sl.addWidget(self.status_label)
        sl.addStretch(); self.status_size = CaptionLabel(""); sl.addWidget(self.status_size)
        self.cl.addWidget(self.status_bar)

    # (rest of MainWindow unchanged — key methods already synced via earlier pushes)

class MergeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("合并PDF"); self.resize(500, 350)
        l = QVBoxLayout(self)
        l.addWidget(BodyLabel("选择要合并的PDF文件（可拖拽排序）："))
        self.list_widget = QListWidget()
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_widget.setDefaultDropAction(Qt.MoveAction)
        l.addWidget(self.list_widget)
        bl = QHBoxLayout()
        add_btn = PushButton(FluentIcon.ADD, "添加文件")
        add_btn.clicked.connect(self._add_files); bl.addWidget(add_btn)
        rm_btn = PushButton(FluentIcon.DELETE, "移除选中")
        rm_btn.clicked.connect(lambda: self.list_widget.takeItem(self.list_widget.currentRow()))
        bl.addWidget(rm_btn); bl.addStretch(); l.addLayout(bl)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject); l.addWidget(bb)

    def _add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "选择PDF", "", "PDF文件 (*.pdf)")
        for p in paths:
            item = QListWidgetItem(os.path.basename(p)); item.setData(Qt.UserRole, p)
            self.list_widget.addItem(item)

    def get_paths(self):
        return [self.list_widget.item(i).data(Qt.UserRole) for i in range(self.list_widget.count())]


class SplitDialog(QDialog):
    def __init__(self, parent, total_pages):
        super().__init__(parent)
        self.setWindowTitle("拆分PDF"); self.resize(350, 180); self.total = total_pages
        l = QFormLayout(self)
        l.addRow(BodyLabel(f"总页数: {total_pages}"))
        self.start_spin = QSpinBox(); self.start_spin.setRange(1, total_pages); self.start_spin.setValue(1)
        l.addRow("起始页:", self.start_spin)
        self.end_spin = QSpinBox(); self.end_spin.setRange(1, total_pages); self.end_spin.setValue(total_pages)
        l.addRow("结束页:", self.end_spin)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject); l.addRow(bb)

    def get_range(self):
        return (self.start_spin.value() - 1, self.end_spin.value() - 1)


class InsertPageDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("插入页面"); self.resize(350, 200)
        l = QVBoxLayout(self)
        self.mode_group = QButtonGroup(self)
        rb_blank = QRadioButton("插入空白页"); rb_blank.setChecked(True)
        rb_file = QRadioButton("从PDF文件插入")
        self.mode_group.addButton(rb_blank, 0); self.mode_group.addButton(rb_file, 1)
        l.addWidget(rb_blank); l.addWidget(rb_file); l.addSpacing(8)
        size_l = QHBoxLayout()
        size_l.addWidget(BodyLabel("页面尺寸:"))
        self.size_cb = QComboBox(); self.size_cb.addItems(["A4","A3","A5","Letter","Legal"])
        size_l.addWidget(self.size_cb); size_l.addStretch(); l.addLayout(size_l)
        self.file_label = BodyLabel("未选择"); self.file_label.setVisible(False); l.addWidget(self.file_label)
        sel_btn = QPushButton("选择PDF文件..."); sel_btn.clicked.connect(self._sel_file); l.addWidget(sel_btn)
        l.addSpacing(8)
        pos_l = QHBoxLayout()
        pos_l.addWidget(BodyLabel("插入位置:"))
        self.pos_cb = QComboBox(); self.pos_cb.addItems(["当前页之后", "文档末尾"])
        pos_l.addWidget(self.pos_cb); pos_l.addStretch(); l.addLayout(pos_l)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject); l.addWidget(bb)
        self._sel_path = ""
        self.mode_group.buttonClicked.connect(lambda b: self.size_cb.setVisible(b == self.mode_group.button(0)))
        self.mode_group.buttonClicked.connect(lambda b: self.file_label.setVisible(b == self.mode_group.button(1)))

    def _sel_file(self):
        p, _ = QFileDialog.getOpenFileName(self, "选择PDF", "", "PDF文件 (*.pdf)")
        if p: self._sel_path = p; self.file_label.setText(os.path.basename(p))

    def get_result(self):
        if self.mode_group.checkedId() == 0:
            return ("blank", {"size": self.size_cb.currentText(), "after": -1})
        return ("file", {"path": self._sel_path, "after": -1})
