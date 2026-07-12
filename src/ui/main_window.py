"""主窗口——完整功能"""

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
    QApplication, QAction, QTextEdit,
)
from qfluentwidgets import (
    MSFluentWindow, NavigationItemPosition, FluentIcon,
    PushButton, ToolButton, PrimaryPushButton,
    InfoBar, InfoBarPosition,
    ComboBox, BodyLabel,
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
    """PS风格内联文字编辑器——覆盖在预览上方，所见即所得"""
    confirmed = pyqtSignal(object)  # dict: {x, y, text, fn, fs, color}

    def __init__(self, parent, pdf_x, pdf_y, scale,
                 fn="SimSun", fs=12, color=(0,0,0),
                 off_x=0, off_y=0):
        super().__init__(parent)
        self._pdf_x = pdf_x; self._pdf_y = pdf_y
        self._fn = fn; self._fs = fs; self._color = color
        self._scale = scale; self._off_x = off_x; self._off_y = off_y
        self._drag = False; self._border = 8  # 边框拖动敏感区

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
        # 定位
        sx = int(pdf_x * scale) + off_x
        sy = int(pdf_y * scale) - int(fs * scale) + off_y
        self.move(sx, sy)
        self.resize(220, max(40, fs * 2 + 10))
        self.setAcceptDrops(False)
        self.show(); self.setFocus()
        self.setMouseTracking(True)
        # 在 viewport + 编辑器自身安装事件过滤器
        self.viewport().installEventFilter(self)
        self.viewport().setMouseTracking(True)
        self.installEventFilter(self)

    def _on_border(self, obj, pos):
        """检查鼠标是否在边框可拖动区域"""
        if pos is None: return False
        if obj is self.viewport():
            wp = self.viewport().mapTo(self, pos)  # viewport坐标 → widget坐标
        else:
            wp = pos  # 已是 widget 坐标（来自 self 的事件）
        w, h = self.width(), self.height()
        b = self._border
        return (wp.x() < b or wp.x() > w - b or
                wp.y() < b or wp.y() > h - b)

    def _start_drag(self, global_pos):
        self._drag = True
        self._drag_start_global = global_pos
        self._drag_start_pos = self.pos()
        self.grabMouse()
        self.setCursor(Qt.ClosedHandCursor)

    def _end_drag(self):
        self._drag = False
        self.releaseMouse()
        self.setCursor(Qt.ArrowCursor)
        new_x = self.pos().x() - self._off_x
        new_y = self.pos().y() + int(self._fs * self._scale) - self._off_y
        self._pdf_x = new_x / self._scale
        self._pdf_y = new_y / self._scale

    def eventFilter(self, obj, event):
        """处理 viewport/self 鼠标事件 + 拖动"""
        from PyQt5.QtCore import QEvent
        t = event.type()
        # 拖动中：来自 grabMouse 的全局鼠标事件
        if self._drag:
            if t == QEvent.MouseMove:
                delta = event.globalPos() - self._drag_start_global
                self.move(self._drag_start_pos + delta)
                return True
            if t == QEvent.MouseButtonRelease:
                if event.button() == Qt.LeftButton:
                    self._end_drag()
                return True
            return False
        # 非拖动：边框检测 + 光标提示（监听 viewport 和 self）
        if obj is self.viewport() or obj is self:
            if t == QEvent.MouseButtonPress:
                if event.button() == Qt.LeftButton and self._on_border(obj, event.pos()):
                    self._start_drag(event.globalPos())
                    return True
            elif t == QEvent.MouseMove:
                if self._on_border(obj, event.pos()):
                    self.setCursor(Qt.OpenHandCursor)
                else:
                    self.setCursor(Qt.IBeamCursor)
        return super().eventFilter(obj, event)

    def get_result(self):
        """确认时返回文字属性"""
        return {"x": self._pdf_x, "y": self._pdf_y,
                "text": self.toPlainText().strip(),
                "fn": self._fn, "fs": self._fs, "color": self._color}

    def apply_props(self, fn=None, fs=None, color=None):
        """应用属性变更"""
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
                if event.angleDelta().y() > 0:
                    mw._zoom_in()
                else:
                    mw._zoom_out()
                event.accept()
                return
        self.preview_scroll.wheelEvent(event)

    def contextMenuEvent(self, event):
        """右键菜单"""
        if not self.engine or not self.engine.is_open:
            return
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { font-size: 13px; padding: 4px; } QMenu::item { padding: 6px 24px; } QMenu::item:selected { background: #e0e0e0; }")

        # 标注子菜单
        annot_menu = menu.addMenu("标注")
        a_hl = annot_menu.addAction("高亮")
        a_hl.triggered.connect(lambda: self._annot_here("highlight"))

        a_ul = annot_menu.addAction("下划线")
        a_ul.triggered.connect(lambda: self._annot_here("underline"))

        a_so = annot_menu.addAction("删除线")
        a_so.triggered.connect(lambda: self._annot_here("strikeout"))

        # 其他操作
        menu.addSeparator()
        a_del = menu.addAction("删除此页")
        a_del.triggered.connect(self._del_this_page)

        a_prop = menu.addAction("页面信息")
        a_prop.triggered.connect(self._page_info)

        menu.exec(event.globalPos())

    def _annot_here(self, atype):
        """在右键点击位置添加标注"""
        if not self.engine or not self.engine.is_open:
            return
        # Use current page center area
        page = self.engine._doc[self.engine.current_page]
        w, h = page.rect.width, page.rect.height
        r = (w*0.3, h*0.3, w*0.7, h*0.7)
        ok = False
        if atype == "highlight":
            ok = self.engine.add_highlight(self.engine.current_page, r)
        elif atype == "underline":
            ok = self.engine.add_underline(self.engine.current_page, r, (0,1,0))
        elif atype == "strikeout":
            ok = self.engine.add_strikeout(self.engine.current_page, r, (1,0,0))
        if ok:
            self.parent()._show_info(f"已添加{['高亮','下划线','删除线'][['highlight','underline','strikeout'].index(atype)]}")

    def _del_this_page(self):
        if not self.engine or not self.engine.is_open:
            return
        from qfluentwidgets import MessageBox
        p = self.engine.current_page
        box = MessageBox("确认", f"确定删除第 {p+1} 页吗？", self)
        if box.exec():
            self.engine.delete_pages([p])

    def _page_info(self):
        if not self.engine or not self.engine.is_open:
            return
        from qfluentwidgets import InfoBar, InfoBarPosition
        p = self.engine.current_page
        page = self.engine._doc[p]
        msg = f"第 {p+1} 页 | {page.rect.width:.0f}x{page.rect.height:.0f} pt"
        InfoBar.info(title="", content=msg, orient=0, isClosable=True, position=InfoBarPosition.TOP_RIGHT, duration=3000, parent=self)
        if p is not None: self.engine.go_to_page(p)


class MainWindow(MSFluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(1280, 800); self.setMinimumSize(900, 600)
        self.setAcceptDrops(True)
        self._tabs = []; self._cur = -1; self._act = -1; self._zoom = 100
        self._add_text_mode = False  # 添加文字模式
        self._text_editor = None  # 内联文字编辑器实例
        self._editing_text_idx = -1  # 正在编辑的已有文字索引
        self._find_results = []  # 当前搜索结果
        self._find_active = 0  # 当前高亮的搜索结果索引
        self._annot_mode = False
        self._annot_type = 'highlight'
        self._annot_color = (1, 1, 0)
        self._setup_nav()
        self._setup_ui()
        self._new_tab()
        # Add new tab button
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
    def _eng(self):
        return self._tabs[self._cur].engine if 0 <= self._cur < len(self._tabs) else None

    @property
    def _tab(self):
        return self._tabs[self._cur] if 0 <= self._cur < len(self._tabs) else None

    def _setup_nav(self):
        n = self.navigationInterface
        n.addItem("o", FluentIcon.DOCUMENT, "打开文件", onClick=self.open_file_dialog, position=NavigationItemPosition.TOP)
        n.addItem("f", FluentIcon.SEARCH, "查找替换", onClick=self.show_find_panel, position=NavigationItemPosition.TOP)
        n.addItem("t", FluentIcon.FONT, "添加文字", onClick=self._on_add_text_mode, position=NavigationItemPosition.TOP)
        n.addItem("w", FluentIcon.PENCIL_INK, "水印工具", onClick=self._show_wm_dlg, position=NavigationItemPosition.TOP)
        n.addItem("img", FluentIcon.PHOTO, "提取图片", onClick=self._on_extract_img, position=NavigationItemPosition.TOP)
        n.addItem("batch", FluentIcon.ALBUM, "批量处理", onClick=self._on_batch, position=NavigationItemPosition.TOP)
        n.addItem("zip", FluentIcon.SAVE, "压缩", onClick=self._on_compress, position=NavigationItemPosition.TOP)
        n.addItem("lock", FluentIcon.REMOVE, "加解密", onClick=self._on_encrypt, position=NavigationItemPosition.TOP)
        n.addItem("s", FluentIcon.SETTING, "设置", onClick=self._show_set_dlg, position=NavigationItemPosition.BOTTOM)
        n.addItem("annot", FluentIcon.EDIT, "注释标注", onClick=self._on_annot_mode, position=NavigationItemPosition.TOP)

    def _setup_ui(self):
        self.central_widget = QWidget(); self.central_widget.setObjectName("centralArea")
        self.cl = QVBoxLayout(self.central_widget); self.cl.setContentsMargins(0,0,0,0); self.cl.setSpacing(0)
        self.tab_bar = QTabWidget(); self.tab_bar.setTabsClosable(True); self.tab_bar.setMovable(True)
        self.tab_bar.tabBar().setElideMode(Qt.ElideRight)
        self.tab_bar.tabCloseRequested.connect(self._close_tab)
        self.tab_bar.currentChanged.connect(self._on_switch)
        self._setup_find()
        self._setup_bar()
        self._setup_text_props_bar()
        self.cl.addWidget(self.tab_bar, 1); self.cl.addWidget(self.find_panel); self.cl.addWidget(self.bottom_bar)

    def _setup_bar(self):
        self.bottom_bar = QWidget(); self.bottom_bar.setFixedHeight(44)
        l = QHBoxLayout(self.bottom_bar); l.setContentsMargins(12,2,12,2)
        self.zc = ComboBox(); self.zc.addItems([f"{z}%" for z in ZOOM_LEVELS])
        self.zc.setCurrentText("100%"); self.zc.setFixedWidth(80)
        self.zc.currentTextChanged.connect(self._on_zoom)
        self.pl = BodyLabel("第 0/0 页")
        self.bp = ToolButton(FluentIcon.PAGE_LEFT); self.bp.setFixedSize(28,28)
        self.bp.clicked.connect(lambda: self._eng and self._eng.prev_page())
        self.bn = ToolButton(FluentIcon.PAGE_RIGHT); self.bn.setFixedSize(28,28)
        self.bn.clicked.connect(lambda: self._eng and self._eng.next_page())
        
        self.br_ccw = PushButton(chr(0x21ba)); self.br_ccw.setFixedSize(36,28)
        self.br_ccw.setToolTip("逆时针旋转90°")
        self.br_ccw.clicked.connect(lambda: self._on_rotate_sel(270))
        self.br_cw = PushButton(chr(0x21bb)); self.br_cw.setFixedSize(36,28)
        self.br_cw.setToolTip("顺时针旋转90°")
        self.br_cw.clicked.connect(lambda: self._on_rotate_sel(90))
        l.addWidget(BodyLabel("缩放:")); l.addWidget(self.zc); l.addSpacing(12)
        l.addWidget(self.bp); l.addWidget(self.pl); l.addWidget(self.bn); l.addSpacing(12)
        l.addWidget(self.br_ccw); l.addWidget(self.br_cw); l.addSpacing(12)
        l.addStretch()
        # 保存按钮组：主按钮 + 下拉箭头
        save_container = QWidget()
        sl = QHBoxLayout(save_container); sl.setContentsMargins(0,0,0,0); sl.setSpacing(0)
        self.save_btn = PrimaryPushButton(FluentIcon.SAVE, "保存")
        self.save_btn.clicked.connect(self.save_current)
        sl.addWidget(self.save_btn)
        # 下拉菜单（只有另存为，显示在按钮上方）
        self.save_drop = ToolButton(FluentIcon.CARE_DOWN_SOLID)
        self.save_drop.setFixedSize(24, 32)
        self.save_drop.clicked.connect(self._show_save_menu)
        sl.addWidget(self.save_drop)
        self.save_menu = QMenu()
        self.save_menu.addAction("另存为").triggered.connect(self.save_as)
        l.addWidget(save_container)

    def _setup_find(self):
        self.find_panel = QWidget(); self.find_panel.setVisible(False)
        p = QHBoxLayout(self.find_panel); p.setContentsMargins(8,4,8,4)
        # 查找输入框（普通 QLineEdit，无内置搜索按钮）
        self.fi = QLineEdit(); self.fi.setPlaceholderText("查找..."); self.fi.setFixedWidth(180)
        self.fi.returnPressed.connect(lambda: self._on_search(self.fi.text()))
        p.addWidget(self.fi)
        # 替换图标
        p.addWidget(QLabel("⇄"))
        # 替换输入框
        self.ri = QLineEdit(); self.ri.setPlaceholderText("替换为..."); self.ri.setFixedWidth(160)
        p.addWidget(self.ri)
        # 结果计数
        self.rl = BodyLabel(""); self.rl.setFixedWidth(100)
        p.addWidget(self.rl)
        # 导航按钮
        self.bpm = PushButton(FluentIcon.CARE_UP_SOLID, "上一个")
        self.bnm = PushButton(FluentIcon.CARE_DOWN_SOLID, "下一个")
        p.addWidget(self.bpm); p.addWidget(self.bnm)
        # 查找按钮
        self.bf = PushButton(FluentIcon.SEARCH, "查找")
        self.bf.clicked.connect(lambda: self._on_search(self.fi.text()))
        p.addWidget(self.bf)
        # 替换按钮
        self.brp = PrimaryPushButton(FluentIcon.SEARCH, "替换")
        self.bra = PushButton(FluentIcon.COMPLETED, "全部替换")
        self.bcf = ToolButton(FluentIcon.CLOSE)
        p.addWidget(self.brp); p.addWidget(self.bra)
        p.addStretch(); p.addWidget(self.bcf)
        # 信号
        self.bpm.clicked.connect(self._on_fp)
        self.bnm.clicked.connect(self._on_fn)
        self.brp.clicked.connect(self._on_rp)
        self.bra.clicked.connect(self._on_ra)
        self.bcf.clicked.connect(lambda: self.find_panel.setVisible(False))

    # ── 添加文字模式（PS风格内联编辑）──

    def _on_add_text_mode(self):
        """进入添加文字模式——点击预览定位，弹出内联编辑器"""
        if not self._eng or not self._eng.is_open:
            self._show_error("请先打开PDF"); return
        self._add_text_mode = True
        tc = self._tab
        if tc:
            tc.preview_label.setCursor(Qt.CrossCursor)
            tc.preview_label.mousePressEvent = self._on_text_place
        self._show_info("点击PDF预览中要添加文字的位置")

    def _on_text_place(self, event: QMouseEvent):
        """点击定位——创建内联文字编辑器（支持点击已有文字重新编辑）"""
        if not self._add_text_mode or not self._eng: return
        self._add_text_mode = False
        tc = self._tab
        if not tc: return
        tc.preview_label.setCursor(Qt.ArrowCursor)
        tc.preview_label.mousePressEvent = lambda e: None

        # PDF坐标（用于最终写入）
        scale = self._zoom / 100.0 * (120.0 / 72.0)
        label = tc.preview_label
        pixmap = label.pixmap()
        off_x = max(0, (label.width() - pixmap.width()) // 2) if pixmap else 0
        off_y = max(0, (label.height() - pixmap.height()) // 2) if pixmap else 0
        img_x = event.pos().x() - off_x
        img_y = event.pos().y() - off_y
        pdf_x = max(0, img_x / scale)
        pdf_y = max(0, img_y / scale)

        # 检查是否点击了已有文字 → 重新编辑
        eng = self._eng
        existing = eng.get_added_texts(eng.current_page)
        match_idx = -1
        for i, t in enumerate(existing):
            tw = fitz.get_text_length(t["text"], fontname="china-ss", fontsize=t["fs"])
            if abs(pdf_x - t["x"]) < tw/2 + 15 and abs(pdf_y - t["y"]) < t["fs"] + 10:
                match_idx = i; break

        self._show_text_props()

        if match_idx >= 0:
            # 编辑已有文字——用已有文字位置定位，不用点击位置
            t = existing[match_idx]
            global_idx = eng._added_texts.index(t)
            self._editing_text_idx = global_idx
            editor = InlineTextEditor(
                tc.preview_label, t["x"], t["y"], scale,
                fn=t["fn"], fs=t["fs"], color=t["c"],
                off_x=off_x, off_y=off_y)
            editor.setPlainText(t["text"])
            self.tp_font.setCurrentText(t["fn"])
            self.tp_size.setValue(int(t["fs"]))
            self._tp_color = t["c"]
            r, g, b = [int(c*255) for c in t["c"]]
            self.tp_color_btn.setStyleSheet(
                f"background:rgb({r},{g},{b}); color:{'white' if (r+g+b)/3<128 else 'black'}; "
                f"border:1px solid #888; font-size:16px;")
        else:
            self._editing_text_idx = -1
            editor = InlineTextEditor(
                tc.preview_label, pdf_x, pdf_y, scale,
                off_x=off_x, off_y=off_y)

        self._text_editor = editor
        editor.installEventFilter(self)

    def _show_text_props(self):
        """显示文字属性栏，隐藏普通底部栏"""
        self.bottom_bar.setVisible(False)
        self.text_props_bar.setVisible(True)

    def _hide_text_props(self):
        """恢复普通底部栏"""
        self.text_props_bar.setVisible(False)
        self.bottom_bar.setVisible(True)
        if self._text_editor:
            self._text_editor.deleteLater()
            self._text_editor = None

    def _resume_text_mode(self):
        """编辑完成后回到十字光标状态，等待下一次点击"""
        self._hide_text_props()
        self._add_text_mode = True
        # 延迟一帧确保编辑器销毁后再设置光标
        QTimer.singleShot(0, self._reactivate_text_cursor)

    def _reactivate_text_cursor(self):
        """重新激活文字模式的十字光标和点击事件"""
        if not self._add_text_mode: return
        tc = self._tab
        if tc:
            tc.preview_label.setCursor(Qt.CrossCursor)
            tc.preview_label.setMouseTracking(True)
            tc.preview_label.mousePressEvent = self._on_text_place

    def _exit_text_mode(self):
        """完全退出添加文字模式"""
        self._hide_text_props()
        self._add_text_mode = False
        tc = self._tab
        if tc:
            tc.preview_label.setCursor(Qt.ArrowCursor)
            tc.preview_label.mousePressEvent = lambda e: None

    def _setup_text_props_bar(self):
        """构建文字属性栏"""
        self.text_props_bar = QWidget(); self.text_props_bar.setFixedHeight(44)
        self.text_props_bar.setVisible(False)
        p = QHBoxLayout(self.text_props_bar); p.setContentsMargins(8,4,8,4)

        # 字体
        p.addWidget(BodyLabel("字体:"))
        self.tp_font = ComboBox()
        self.tp_font.addItems(["SimSun","SimHei","KaiTi","FangSong","YaHei"])
        self.tp_font.setCurrentText("SimSun"); self.tp_font.setFixedWidth(80)
        self.tp_font.currentTextChanged.connect(self._on_tp_change)
        p.addWidget(self.tp_font)

        # 大小
        p.addWidget(BodyLabel("大小:"))
        self.tp_size = QSpinBox(); self.tp_size.setRange(6,200); self.tp_size.setValue(12)
        self.tp_size.setFixedWidth(60)
        self.tp_size.valueChanged.connect(self._on_tp_change)
        p.addWidget(self.tp_size)

        # 颜色
        self.tp_color_btn = QPushButton("■")
        self.tp_color_btn.setFixedSize(28,28)
        self.tp_color_btn.setStyleSheet("background:#000; color:#fff; border:1px solid #888; font-size:16px;")
        self.tp_color_btn.clicked.connect(self._on_tp_color)
        p.addWidget(self.tp_color_btn)
        self._tp_color = (0,0,0)

        # 加粗/斜体/下划线/删除线
        self.tp_bold = ToolButton()
        self.tp_bold.setText("B"); self.tp_bold.setFixedSize(28,28)
        self.tp_bold.setCheckable(True)
        self.tp_bold.setStyleSheet("QToolButton{font-weight:bold;font-size:14px;} QToolButton:checked{background:#0078D4;color:#fff;}")
        self.tp_bold.toggled.connect(self._on_tp_change)
        p.addWidget(self.tp_bold)

        self.tp_italic = ToolButton()
        self.tp_italic.setText("I"); self.tp_italic.setFixedSize(28,28)
        self.tp_italic.setCheckable(True)
        self.tp_italic.setStyleSheet("QToolButton{font-style:italic;font-size:14px;} QToolButton:checked{background:#0078D4;color:#fff;}")
        self.tp_italic.toggled.connect(self._on_tp_change)
        p.addWidget(self.tp_italic)

        self.tp_underline = ToolButton()
        self.tp_underline.setText("U"); self.tp_underline.setFixedSize(28,28)
        self.tp_underline.setCheckable(True)
        self.tp_underline.setStyleSheet("QToolButton{text-decoration:underline;font-size:14px;} QToolButton:checked{background:#0078D4;color:#fff;}")
        self.tp_underline.toggled.connect(self._on_tp_change)
        p.addWidget(self.tp_underline)

        self.tp_strike = ToolButton()
        self.tp_strike.setText("S"); self.tp_strike.setFixedSize(28,28)
        self.tp_strike.setCheckable(True)
        self.tp_strike.setStyleSheet("QToolButton{text-decoration:line-through;font-size:14px;} QToolButton:checked{background:#0078D4;color:#fff;}")
        self.tp_strike.toggled.connect(self._on_tp_change)
        p.addWidget(self.tp_strike)

        p.addSpacing(16)

        # 间距/行高
        p.addWidget(BodyLabel("间距:"))
        self.tp_spacing = QSpinBox(); self.tp_spacing.setRange(0,50); self.tp_spacing.setValue(0)
        self.tp_spacing.setFixedWidth(50); self.tp_spacing.setSuffix("%")
        self.tp_spacing.valueChanged.connect(self._on_tp_change)
        p.addWidget(self.tp_spacing)

        p.addWidget(BodyLabel("行高:"))
        self.tp_lh = QSpinBox(); self.tp_lh.setRange(100,300); self.tp_lh.setValue(120)
        self.tp_lh.setFixedWidth(60); self.tp_lh.setSuffix("%"); self.tp_lh.setSingleStep(10)
        self.tp_lh.valueChanged.connect(self._on_tp_change)
        p.addWidget(self.tp_lh)

        p.addStretch()

        # 确认/取消
        self.tp_ok = PrimaryPushButton("✓ 确认")
        self.tp_ok.clicked.connect(self._confirm_text)
        p.addWidget(self.tp_ok)
        self.tp_cancel = PushButton("✗ 取消")
        self.tp_cancel.clicked.connect(self._cancel_text)
        p.addWidget(self.tp_cancel)

        # 加入布局
        self.cl.addWidget(self.text_props_bar)

    def _on_tp_change(self):
        """属性栏变化 → 实时更新编辑器样式"""
        if not self._text_editor: return
        e = self._text_editor
        e._fn = self.tp_font.currentText()
        e._fs = self.tp_size.value()
        r, g, b = [int(c*255) for c in self._tp_color]
        bold = self.tp_bold.isChecked()
        italic = self.tp_italic.isChecked()
        underline = self.tp_underline.isChecked()
        strike = self.tp_strike.isChecked()
        spacing = self.tp_spacing.value()
        lh = self.tp_lh.value()

        # 同步 Qt 内部字体状态（与 CSS 双重保障）
        e.setFontFamily(e._fn)
        e.setFontPointSize(e._fs)
        e.setTextColor(QColor(r, g, b))

        e.setStyleSheet(f"""
            QTextEdit {{
                background: rgba(255,255,255,30);
                border: 2px dashed #0078D4;
                border-radius: 2px;
                padding: 4px 6px;
                font-family: "{e._fn}";
                font-size: {e._fs}pt;
                font-weight: {'bold' if bold else 'normal'};
                font-style: {'italic' if italic else 'normal'};
                text-decoration: {'underline' if underline else 'none'};
                color: rgb({r},{g},{b});
                letter-spacing: {spacing}%;
                line-height: {lh}%;
            }}
        """)

    def _on_tp_color(self):
        c = QColorDialog.getColor(QColor(*[int(c*255) for c in self._tp_color]), self)
        if c.isValid():
            self._tp_color = (c.redF(), c.greenF(), c.blueF())
            self.tp_color_btn.setStyleSheet(
                f"background:rgb({c.red()},{c.green()},{c.blue()}); "
                f"color:{'white' if c.lightness()<128 else 'black'}; "
                f"border:1px solid #888; font-size:16px;")
            self._on_tp_change()

    def _confirm_text(self):
        """确认文字——写入PDF（支持新增和覆盖已有文字）"""
        if not self._text_editor or not self._eng: return
        e = self._text_editor; eng = self._eng
        text = e.toPlainText().strip()
        if not text:
            self._resume_text_mode(); return
        pdf_x = e._pdf_x; pdf_y = e._pdf_y
        if self._editing_text_idx >= 0:
            # 用 redaction 精确删除旧文字位置
            old = eng._added_texts[self._editing_text_idx]
            old_pn = old["page"]
            eng._snap()
            page = eng._doc[old_pn]
            tw = fitz.get_text_length(old["text"], fontname="china-ss", fontsize=old["fs"])
            r = fitz.Rect(old["x"], old["y"]-old["fs"]*1.1, old["x"]+tw+2, old["y"]+old["fs"]*0.4)
            page.add_redact_annot(r)
            page.apply_redactions(images=0)
            # redaction 后页面的字体引用被清除，必须重新注册
            import core.text_ops as _to
            _to._font_cache.pop(id(page), None)
            _to._init_system_fonts(page)
            page.insert_text((pdf_x, pdf_y), text,
                             fontsize=e._fs, fontname=e._fn, color=e._color)
            old["text"] = text; old["x"] = pdf_x; old["y"] = pdf_y
            old["fn"] = e._fn; old["fs"] = e._fs; old["color"] = e._color
            eng._modified = True
            self._show_info(f"已修改: {text[:20]}")
        else:
            eng.add_text(eng.current_page, (pdf_x, pdf_y),
                         text, e._fn, e._fs, e._color)
            self._show_info(f"已添加: {text[:20]}")
        self._editing_text_idx = -1
        self._thumbs(); self._render()
        self._resume_text_mode()

    def _cancel_text(self):
        """取消文字编辑——回到十字光标"""
        self._resume_text_mode()
        self._render()

    # 键盘事件处理
    def eventFilter(self, obj, event):
        from PyQt5.QtCore import QEvent
        editor = getattr(self, '_text_editor', None)
        if editor and obj is editor and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Return and event.modifiers() == Qt.NoModifier:
                self._confirm_text(); return True
            if event.key() == Qt.Key_Escape:
                self._resume_text_mode(); self._render(); return True
        return super().eventFilter(obj, event)

    # ── 注释标注模式 ──

    def _on_annot_mode(self):
        """进入注释标注模式"""
        self._exit_text_mode()
        if not self._eng or not self._eng.is_open:
            self._show_error("请先打开PDF"); return
        self._annot_color = (1, 1, 0)
        self._annot_type = "highlight"
        self._annot_mode = True
        QApplication.setOverrideCursor(QCursor(Qt.CrossCursor))
        self._show_info("点击PDF预览中要标注的位置")
        tc = self._tab
        if tc:
            tc.preview_label.mousePressEvent = self._on_annot_click

    def _on_annot_click(self, event):
        if not self._annot_mode or not self._eng: return
        self._annot_mode = False
        QApplication.restoreOverrideCursor()
        tc = self._tab
        if tc:
            tc.preview_label.mousePressEvent = lambda e: None
        scale = self._zoom / 100.0 * (120.0 / 72.0)
        px = event.pos().x() / scale
        py = event.pos().y() / scale
        r = (px - 20, py - 6, px + 20, py + 6)
        e = self._eng
        ok = False
        if self._annot_type == "highlight":
            ok = e.add_highlight(e.current_page, r)
        elif self._annot_type == "underline":
            ok = e.add_underline(e.current_page, r, self._annot_color)
        elif self._annot_type == "strikeout":
            ok = e.add_strikeout(e.current_page, r, self._annot_color)
        if ok: self._show_info("标注已添加"); self._render()

    # ── 标签 ──

    def _new_tab(self, fp=""):
        eng = PDFEngine(self)
        tc = TabPage(eng)
        self._tabs.append(tc)
        idx = self.tab_bar.addTab(tc, "新文档")
        self.tab_bar.setCurrentIndex(idx); self._cur = idx
        eng.document_loaded.connect(self._on_loaded)
        eng.page_changed.connect(self._on_pc)
        eng.operation_completed.connect(self._show_info)
        eng.error_occurred.connect(self._show_error)
        eng.find_completed.connect(self._on_fc)
        if fp: eng.open(fp); eng._doc = eng._doc if eng._doc else fitz.open()
        return tc

    def _close_tab(self, idx):
        if len(self._tabs) <= 1: return
        eng = self._tabs[idx].engine
        if eng.modified:
            r = QMessageBox.question(self, "未保存", "文档已修改，是否关闭？",
                                     QMessageBox.Yes | QMessageBox.No)
            if r != QMessageBox.Yes: return
        eng.close()
        self.tab_bar.removeTab(idx); self._tabs.pop(idx)
        self._cur = max(0, self.tab_bar.currentIndex())

    def _on_switch(self, idx):
        if 0 <= idx < len(self._tabs): self._cur = idx; self._update_ui()

    def _update_ui(self):
        e = self._eng
        if not e: return
        fp = e.filepath
        name = fp.split("\\")[-1] if fp else "新文档"
        mod = " ●" if e.modified else ""
        title = f"{name}{mod}"
        self.tab_bar.setTabText(self._cur, title)
        if fp:
            self.tab_bar.setTabToolTip(self._cur, fp)
        if e.is_open:
            self.pl.setText(f"第 {e.current_page+1}/{e.page_count} 页")
            self._render(); self._thumbs()
        else: self.pl.setText("第 0/0 页")

    def _show_page_dlg(self):
        if not self._eng or not self._eng.is_open: self._show_error("请先打开PDF"); return
    def _show_wm_dlg(self):
        self._exit_text_mode()
        if not self._eng or not self._eng.is_open: self._show_error("请先打开PDF"); return
        ToolDialog("水印工具", WatermarkPage(self), self).exec_(); self._render()
    def _show_set_dlg(self):
        self._exit_text_mode()
        ToolDialog("设置", SettingsPage(self), self).exec_()

    def _on_extract_img(self):
        self._exit_text_mode()
        if not self._eng or not self._eng.is_open: self._show_error("请先打开PDF"); return
        d = QFileDialog.getExistingDirectory(self, "选择保存目录")
        if d: self._show_info(f"提取 {len(self._eng.extract_images(d))} 张图片")

    def _on_encrypt(self):
        self._exit_text_mode()
        if not self._eng or not self._eng.is_open: self._show_error("请先打开PDF"); return
        e = self._eng
        if e.is_encrypted():
            pwd, ok = QInputDialog.getText(self, "解密", "输入密码:", echo=QLineEdit.Password)
            if ok and pwd:
                if e.decrypt(pwd): self._show_info("已解密"); self._update_ui()
                else: self._show_error("密码错误")
        else:
            pwd, ok = QInputDialog.getText(self, "加密", "设置密码:", echo=QLineEdit.Password)
            if ok and pwd:
                if e.encrypt(pwd): self._show_info("已加密"); self._update_ui()
                else: self._show_error("加密失败")

    def open_file_dialog(self):
        self._exit_text_mode()
        path, _ = QFileDialog.getOpenFileName(self, "打开PDF", "", "PDF文件 (*.pdf)")
        if path:
            self._new_tab(path); add_recent(path)
            self.find_panel.setVisible(True); self.fi.setFocus(); self.fi.clear()

    def save_new(self):
        e = self._eng
        if not e or not e._doc: return
        p, _ = QFileDialog.getSaveFileName(self, "保存新文档", "", "PDF文件 (*.pdf)")
        if p: e.save(p); self._update_ui(); self._tab and self._tab.thumb_list.clear()

    def _show_save_menu(self):
        """在按钮上方弹出另存为菜单"""
        btn = self.save_drop
        menu_h = self.save_menu.sizeHint().height()
        pos = btn.mapToGlobal(btn.rect().topLeft() - QPoint(0, menu_h))
        self.save_menu.exec(pos)

    def save_current(self):
        e = self._eng
        if not e or not e._doc: return
        if e.filepath and not e.modified: return
        if e.filepath: e.save(); self._update_ui()
        else: self.save_as()

    def save_as(self):
        e = self._eng
        if not e or not e._doc: return
        p, _ = QFileDialog.getSaveFileName(self, "另存为", "", "PDF文件 (*.pdf)")
        if p: e.save(p); self._update_ui()

    def undo_current(self):
        if self._eng: self._eng.undo(); self._update_ui()

    def _on_search(self, text):
        if self._eng and text:
            results = self._eng.find_text(text)
            self._find_results = results
            if results:
                self.rl.setText(f"共找到 {len(results)} 处")
                self._find_active = 0
                self._eng.go_to_page(results[0].page_num)
                self._render()
            else:
                self.rl.setText("未找到匹配")
                self._render()

    def _on_fc(self, results):
        self._find_results = results
        if results:
            self.rl.setText(f"共找到 {len(results)} 处")
            self._find_active = 0
            self._eng.go_to_page(results[0].page_num)
        else:
            self.rl.setText("未找到匹配")
        self._render()

    def _on_fp(self):
        if not self._find_results: return
        self._find_active = max(0, self._find_active - 1)
        r = self._find_results[self._find_active]
        self._eng.go_to_page(r.page_num)
        self._render()

    def _on_fn(self):
        if not self._find_results: return
        self._find_active = min(len(self._find_results) - 1, self._find_active + 1)
        r = self._find_results[self._find_active]
        self._eng.go_to_page(r.page_num)
        self._render()
    def _on_rp(self):
        """替换当前选中的匹配"""
        e = self._eng; results = self._find_results
        if not e or not e.is_open or not results: return
        new_text = self.ri.text().strip()
        if not new_text:
            self._show_error("请输入替换文字"); return
        r = results[self._find_active]
        if e.replace_text(r.page_num, r.rect, new_text):
            r.replaced = True
            # 跳到下一个未替换的匹配
            for i in range(self._find_active + 1, len(results)):
                if not results[i].replaced:
                    self._find_active = i
                    self._eng.go_to_page(results[i].page_num)
                    break
            self._show_info("已替换")
            self._thumbs(); self._render()

    def _on_ra(self):
        """全部替换"""
        e = self._eng; results = self._find_results
        if not e or not e.is_open or not results: return
        new_text = self.ri.text().strip()
        if not new_text:
            self._show_error("请输入替换文字"); return
        count = e.replace_all(results, new_text)
        self._show_info(f"已替换 {count} 处")
        self._render()

    def _on_loaded(self, fp, pc): self._update_ui()
    def _on_pc(self, pn, t):
        if self._eng and self._eng.current_page == pn:
            self.pl.setText(f"第 {pn+1}/{t} 页"); self._render()
    def _on_fc(self, results):
        self.rl.setText(f"共找到 {len(results)} 处" if results else "未找到匹配")

    def _render(self):
        e, t = self._eng, self._tab
        if not e or not e.is_open or not t: return
        # 构建当前页的搜索结果高亮列表
        rects = []
        active_idx = -1
        if hasattr(self, '_find_results') and self._find_results:
            for i, r in enumerate(self._find_results):
                if r.page_num == e.current_page and not r.replaced:
                    rects.append(r.rect)
                    if i == self._find_active:
                        active_idx = len(rects) - 1
        if rects:
            img = Renderer.render_page_with_highlights(
                e._doc[e.current_page], rects, active_idx, 120)
        else:
            img = e.render_page(e.current_page, 120)
        if img is None: return
        s = self._zoom / 100.0
        sc = img.scaled(int(img.width()*s), int(img.height()*s), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        t.preview_label.setPixmap(QPixmap.fromImage(sc)); t.preview_label.resize(sc.size())

    def _thumbs(self):
        e, t = self._eng, self._tab
        if not e or not e.is_open or not t: return
        t.thumb_list.clear()
        for i in range(e.page_count):
            th = e.render_thumbnail(i)
            if th is None: continue
            it = QListWidgetItem(); it.setIcon(QIcon(th)); it.setText(f"第 {i+1} 页")
            it.setData(Qt.UserRole, i); it.setSizeHint(QSize(160,140))
            t.thumb_list.addItem(it)
        

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls(): e.acceptProposedAction()
    def dropEvent(self, e):
        for url in e.mimeData().urls():
            p = url.toLocalFile()
            if p.lower().endswith(".pdf"): self._new_tab(p); add_recent(p); break

    def show_find_panel(self):
        self._exit_text_mode()
        self.find_panel.setVisible(True); self.fi.setFocus()
    def _on_zoom(self, t):
        try: self._zoom = int(t.replace("%","")); self._render()
        except: pass
    def toggle_theme(self):
        from qfluentwidgets import setTheme, Theme
        t = "dark" if not hasattr(self,'_th') or not self._th else "light"
        if t == "dark": setTheme(Theme.DARK)
        else: setTheme(Theme.LIGHT)
        self._th = (t == "dark"); save_theme(t); signal_bus.theme_changed.emit(t)

    def _show_info(self, msg, parent=None):
        if parent is None:
            parent = self._tab if self._tab else self
        InfoBar.success(title="", content=msg, orient=Qt.Horizontal,
                        isClosable=True, position=InfoBarPosition.TOP_RIGHT, duration=2000, parent=parent)
    def _show_error(self, msg):
        InfoBar.error(title="", content=msg, orient=Qt.Horizontal,
                      isClosable=True, position=InfoBarPosition.TOP_RIGHT, duration=3000, parent=self)

    def keyPressEvent(self, event):
        k, m = event.key(), event.modifiers()
        if k == Qt.Key_Escape:
            self.find_panel.setVisible(False)
            if self._add_text_mode and not self._text_editor:
                self._exit_text_mode()
                return
            if self._annot_mode:
                self._annot_mode = False
                QApplication.restoreOverrideCursor()
        elif m == Qt.ControlModifier and k == Qt.Key_O: self.open_file_dialog()
        elif m == (Qt.ControlModifier | Qt.ShiftModifier) and k == Qt.Key_S:
            self.save_as()
        elif m == Qt.ControlModifier and k == Qt.Key_S:
            self.save_current()
        elif m == Qt.ControlModifier and k == Qt.Key_Z: self.undo_current()
        elif m == Qt.ControlModifier and k == Qt.Key_F: self.show_find_panel()
        elif m == Qt.ControlModifier and k == Qt.Key_Plus: self._zoom_in()
        elif m == Qt.ControlModifier and k == Qt.Key_Minus: self._zoom_out()
        elif m == Qt.ControlModifier and k == Qt.Key_0: self._zoom=100; self.zc.setCurrentText("100%")
        elif m == Qt.ControlModifier and k == Qt.Key_C:
            self._on_copy_pages()
        elif m == Qt.ControlModifier and k == Qt.Key_V:
            self._on_paste_pages()
        elif k == Qt.Key_Delete:
            self._on_delete_selected()
        elif k == Qt.Key_PageUp:
            if self._eng: self._eng.prev_page()
        elif k == Qt.Key_PageDown:
            if self._eng: self._eng.next_page()
        super().keyPressEvent(event)

    def _zoom_in(self):
        for z in ZOOM_LEVELS:
            if z > self._zoom: self._zoom=z; self.zc.setCurrentText(f"{z}%"); return
    def _on_batch(self):
        self._exit_text_mode()
        from qfluentwidgets import InfoBar, InfoBarPosition
        files, _ = QFileDialog.getOpenFileNames(self, "选择要批量处理的PDF", "", "PDF文件 (*.pdf)")
        if len(files) < 2:
            self._show_error("请选择至少2个文件"); return
        from core.text_ops import TextOps
        import fitz
        count = 0
        for fp in files:
            try:
                doc = fitz.open(fp)
                for pn in range(doc.page_count):
                    for r in doc[pn].search_for("张三"):
                        TextOps.replace_text(doc[pn], (r.x0,r.y0,r.x1,r.y1), "李四")
                doc.save(fp + ".bak", incremental=False, clean=True, garbage=4)
                doc.close()
                count += 1
            except:
                pass
        InfoBar.success(title="", content=f"批量处理完成: {count}/{len(files)}个文件",
            orient=0, isClosable=True, position=InfoBarPosition.TOP_RIGHT, duration=3000, parent=self)

    def _on_compress(self):
        self._exit_text_mode()
        if not self._eng or not self._eng.is_open:
            self._show_error("请先打开PDF"); return
        from qfluentwidgets import InfoBar, InfoBarPosition
        import os
        out, _ = QFileDialog.getSaveFileName(self, "压缩另存为", "", "PDF文件 (*.pdf)")
        if out:
            if self._eng.compress(out):
                sz = os.path.getsize(out)
                InfoBar.success(title="", content=f"压缩完成: {sz/1024:.0f}KB",
                    orient=0, isClosable=True, position=InfoBarPosition.TOP_RIGHT, duration=3000, parent=self)

    def _on_copy_pages(self):
        e = self._eng
        if not e or not e._doc: return
        tc = self._tab
        if not tc: return
        items = tc.thumb_list.selectedItems()
        if not items:
            self._show_error("请先选择页面"); return
        self._copied_pages = sorted([it.data(Qt.UserRole) for it in items if it.data(Qt.UserRole) is not None])
        self._copied_engine = e
        # 弹窗定位到预览窗口右上角
        preview_parent = tc.preview_scroll if tc else self
        self._show_info(f"已复制 {len(self._copied_pages)} 页", parent=preview_parent)

    def _on_paste_pages(self):
        if not hasattr(self, '_copied_pages') or not self._copied_pages:
            self._show_error('请先复制页面'); return
        e = self._eng
        if not e:
            self._show_error('请打开目标标签页'); return
        if not e._doc:
            e._doc = fitz.open()
        src = self._copied_engine
        if src is e:
            self._show_error('不能粘贴到同一个文档'); return
        pns = self._copied_pages
        for pn in sorted(pns):
            p = src._doc[pn]
            r = e._doc.new_page(-1, width=p.rect.width, height=p.rect.height)
            r.show_pdf_page(r.rect, src._doc, pn)
        e._modified = True
        e._filepath = ''
        e.document_loaded.emit(e._filepath, e._doc.page_count)
        self._thumbs()
        self._show_info('已粘贴 ' + str(len(pns)) + ' 页')

    def _on_delete_selected(self):
        e = self._eng
        if not e or not e._doc: return
        tc = self._tab
        if not tc: return
        items = tc.thumb_list.selectedItems()
        if not items: return
        pages = sorted([it.data(Qt.UserRole) for it in items if it.data(Qt.UserRole) is not None], reverse=True)
        from qfluentwidgets import MessageBox
        box = MessageBox("确认", f"确定删除选中的 {len(pages)} 页吗？", self)
        if box.exec():
            e.delete_pages(pages)

    def _on_rotate_sel(self, angle):
        e = self._eng
        if not e or not e._doc: return
        tc = self._tab
        if not tc: return
        items = tc.thumb_list.selectedItems()
        pages = [it.data(Qt.UserRole) for it in items if it.data(Qt.UserRole) is not None]
        if not pages:
            pages = [e.current_page]
        e.rotate_pages(pages, angle)
        self._thumbs()
        self._render()

    def _zoom_out(self):
        for z in reversed(ZOOM_LEVELS):
            if z < self._zoom: self._zoom=z; self.zc.setCurrentText(f"{z}%"); return
