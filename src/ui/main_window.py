"""主窗口——完整功能"""

from PyQt5.QtCore import Qt, QTimer, QSize, QPoint
from PyQt5.QtGui import (
    QPixmap, QIcon, QDragEnterEvent, QDropEvent,
    QMouseEvent, QCursor, QColor,
)
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFileDialog, QScrollArea, QListWidget, QListWidgetItem,
    QAbstractItemView, QTabWidget, QDialog, QLineEdit,
    QDialogButtonBox, QFormLayout, QSpinBox, QComboBox,
    QMessageBox, QInputDialog, QPushButton, QColorDialog,
    QApplication,
)
from qfluentwidgets import (
    MSFluentWindow, NavigationItemPosition, FluentIcon,
    PushButton, ToolButton, PrimaryPushButton,
    SearchLineEdit, InfoBar, InfoBarPosition,
    ComboBox, BodyLabel, CaptionLabel,
)

from app.constants import APP_NAME, APP_VERSION, ZOOM_LEVELS
from app.theme import ThemeManager
from app.settings import add_recent, get_recent, save_theme, load as load_cfg
from utils.signal_bus import signal_bus
from core.pdf_engine import PDFEngine
from core.renderer import Renderer
from ui.pages.page_manage_page import PageManagePage
from ui.pages.watermark_page import WatermarkPage
from ui.pages.settings_page import SettingsPage
from ui.dialogs.tool_dialog import ToolDialog


class AddTextDialog(QDialog):
    def __init__(self, pos_pdf, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加文字"); self.setModal(True)
        self._color = (0, 0, 0)
        self._pos = pos_pdf  # (pdf_x, pdf_y)
        l = QFormLayout(self)

        l.addRow(BodyLabel(f"位置: ({pos_pdf[0]:.0f}, {pos_pdf[1]:.0f})"))

        self.ti = QLineEdit()
        self.ti.setPlaceholderText("输入文字...")
        l.addRow("文字:", self.ti)

        self.fc = QComboBox()
        self.fc.addItems(["SimSun", "SimHei", "KaiTi", "FangSong", "YaHei", "china-ss"])
        l.addRow("字体:", self.fc)

        self.ss = QSpinBox(); self.ss.setRange(6, 200); self.ss.setValue(12)
        l.addRow("大小:", self.ss)

        self.cb = QPushButton("选择颜色")
        self.cb.setStyleSheet("background:#ccc; min-height:24px;")
        self.cb.clicked.connect(self._pick_color)
        l.addRow("颜色:", self.cb)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        l.addRow(bb)

    def _pick_color(self):
        c = QColorDialog.getColor(QColor(0, 0, 0), self)
        if c.isValid():
            self._color = (c.redF(), c.greenF(), c.blueF())
            self.cb.setStyleSheet(
                f"background:rgb({c.red()},{c.green()},{c.blue()}); "
                f"color:{'white' if c.lightness()<128 else 'black'};"
                f"min-height:24px;")

    def get_cfg(self):
        return {"pos": self._pos, "text": self.ti.text().strip(),
                "fontname": self.fc.currentText(), "fontsize": self.ss.value(),
                "color": self._color}


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
        self.thumb_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.thumb_list.setSpacing(2); self.thumb_list.setIconSize(QSize(160, 120))
        self.thumb_list.itemClicked.connect(self._tc)
        content = QWidget()
        cl = QHBoxLayout(content); cl.setContentsMargins(0,0,0,0); cl.setSpacing(0)
        cl.addWidget(self.thumb_list); cl.addWidget(self.preview_scroll, 1)
        l = QVBoxLayout(self); l.setContentsMargins(0,0,0,0); l.setSpacing(0)
        l.addWidget(content, 1)

    def _tc(self, item):
        p = item.data(Qt.UserRole)
        if p is not None: self.engine.go_to_page(p)


class MainWindow(MSFluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(1280, 800); self.setMinimumSize(900, 600)
        self.setAcceptDrops(True)
        self._tabs = []; self._cur = -1; self._act = -1; self._zoom = 100
        self._add_text_mode = False  # 添加文字模式
        self._setup_nav()
        self._setup_ui()
        self._new_tab()
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
        n.addItem("p", FluentIcon.LAYOUT, "页面管理", onClick=self._show_page_dlg, position=NavigationItemPosition.TOP)
        n.addItem("t", FluentIcon.FONT, "添加文字", onClick=self._on_add_text_mode, position=NavigationItemPosition.TOP)
        n.addItem("w", FluentIcon.PENCIL_INK, "水印工具", onClick=self._show_wm_dlg, position=NavigationItemPosition.TOP)
        n.addItem("img", FluentIcon.PHOTO, "提取图片", onClick=self._on_extract_img, position=NavigationItemPosition.TOP)
        n.addItem("lock", FluentIcon.REMOVE, "加解密", onClick=self._on_encrypt, position=NavigationItemPosition.TOP)
        n.addItem("s", FluentIcon.SETTING, "设置", onClick=self._show_set_dlg, position=NavigationItemPosition.BOTTOM)

    def _setup_ui(self):
        self.central_widget = QWidget(); self.central_widget.setObjectName("centralArea")
        self.cl = QVBoxLayout(self.central_widget); self.cl.setContentsMargins(0,0,0,0); self.cl.setSpacing(0)
        self.tab_bar = QTabWidget(); self.tab_bar.setTabsClosable(True); self.tab_bar.setMovable(True)
        self.tab_bar.tabCloseRequested.connect(self._close_tab)
        self.tab_bar.currentChanged.connect(self._on_switch)
        self._setup_find()
        self._setup_bar()
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
        self.fl = CaptionLabel("未打开文件"); self.fl.setStyleSheet("color:#888;")
        l.addWidget(BodyLabel("缩放:")); l.addWidget(self.zc); l.addSpacing(12)
        l.addWidget(self.bp); l.addWidget(self.pl); l.addWidget(self.bn); l.addSpacing(12)
        l.addStretch(); l.addWidget(self.fl)

    def _setup_find(self):
        self.find_panel = QWidget(); self.find_panel.setVisible(False)
        p = QHBoxLayout(self.find_panel); p.setContentsMargins(8,4,8,4)
        self.fi = SearchLineEdit(); self.fi.setPlaceholderText("查找..."); self.fi.setFixedWidth(200)
        self.ri = QLineEdit(); self.ri.setPlaceholderText("替换为..."); self.ri.setFixedWidth(160)
        self.rl = BodyLabel(""); self.rl.setFixedWidth(100)
        self.bpm = PushButton(FluentIcon.CARE_UP_SOLID, "上一个")
        self.bnm = PushButton(FluentIcon.CARE_DOWN_SOLID, "下一个")
        self.brp = PrimaryPushButton(FluentIcon.SEARCH, "替换")
        self.bra = PushButton(FluentIcon.COMPLETED, "全部替换")
        self.bcf = ToolButton(FluentIcon.CLOSE)
        p.addWidget(QLabel("🔍")); p.addWidget(self.fi); p.addWidget(self.ri)
        p.addWidget(self.rl); p.addWidget(self.bpm); p.addWidget(self.bnm)
        p.addWidget(self.brp); p.addWidget(self.bra); p.addStretch(); p.addWidget(self.bcf)
        self.fi.searchSignal.connect(self._on_search)
        self.bpm.clicked.connect(self._on_fp)
        self.bnm.clicked.connect(self._on_fn)
        self.brp.clicked.connect(self._on_rp)
        self.bra.clicked.connect(self._on_ra)
        self.bcf.clicked.connect(lambda: self.find_panel.setVisible(False))

    # ── 添加文字模式 ──

    def _on_add_text_mode(self):
        """进入添加文字模式——鼠标点击预览定位"""
        if not self._eng or not self._eng.is_open:
            self._show_error("请先打开PDF"); return
        self._add_text_mode = True
        QApplication.setOverrideCursor(QCursor(Qt.CrossCursor))
        self._show_info("点击PDF预览中要添加文字的位置")
        # 绑定点击事件到当前预览
        tc = self._tab
        if tc:
            tc.preview_label.mousePressEvent = self._on_preview_click

    def _on_preview_click(self, event: QMouseEvent):
        """预览点击——捕获PDF坐标"""
        if not self._add_text_mode or not self._eng:
            return
        self._add_text_mode = False
        QApplication.restoreOverrideCursor()
        # 恢复预览的默认mousePressEvent
        tc = self._tab
        if tc:
            tc.preview_label.mousePressEvent = lambda e: None

        # 将点击坐标转为PDF坐标
        # 预览渲染DPI=120, PDF默认72DPI, 还有缩放因子
        scale = self._zoom / 100.0 * (120.0 / 72.0)
        pdf_x = event.pos().x() / scale
        pdf_y = event.pos().y() / scale

        dlg = AddTextDialog((pdf_x, pdf_y), self)
        if dlg.exec():
            c = dlg.get_cfg()
            if not c["text"]: return
            e = self._eng
            ok = e.add_text(e.current_page, c["pos"], c["text"],
                            c["fontname"], c["fontsize"], c["color"])
            if ok:
                self._show_info(f"已添加: {c['text']}")
                self._thumbs(); self._render()

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
        if fp: eng.open(fp)
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
        if not e: self.fl.setText("无文件"); return
        n = e.filepath.split("\\")[-1] if e.filepath else "新文档"
        m = " ●" if e.modified else ""
        self.fl.setText(f"📄 {n}{m}")
        self.tab_bar.setTabText(self._cur, f"{n}{m}")
        if e.is_open:
            self.pl.setText(f"第 {e.current_page+1}/{e.page_count} 页")
            self._render(); self._thumbs()
        else: self.pl.setText("第 0/0 页")

    def _show_page_dlg(self):
        if not self._eng or not self._eng.is_open: self._show_error("请先打开PDF"); return
        ToolDialog("页面管理", PageManagePage(self), self).exec_(); self._thumbs()
    def _show_wm_dlg(self):
        if not self._eng or not self._eng.is_open: self._show_error("请先打开PDF"); return
        ToolDialog("水印工具", WatermarkPage(self), self).exec_(); self._render()
    def _show_set_dlg(self):
        ToolDialog("设置", SettingsPage(self), self).exec_()

    def _on_extract_img(self):
        if not self._eng or not self._eng.is_open: self._show_error("请先打开PDF"); return
        d = QFileDialog.getExistingDirectory(self, "选择保存目录")
        if d: self._show_info(f"提取 {len(self._eng.extract_images(d))} 张图片")

    def _on_encrypt(self):
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
        path, _ = QFileDialog.getOpenFileName(self, "打开PDF", "", "PDF文件 (*.pdf)")
        if path:
            self._new_tab(path); add_recent(path)
            self.find_panel.setVisible(True); self.fi.setFocus(); self.fi.clear()

    def save_current(self):
        e = self._eng
        if not e or not e.is_open: return
        if e.filepath and not e.modified: return
        if e.filepath: e.save(); self._update_ui()
        else: self.save_as()

    def save_as(self):
        e = self._eng
        if not e or not e.is_open: return
        p, _ = QFileDialog.getSaveFileName(self, "另存为", "", "PDF文件 (*.pdf)")
        if p: e.save(p); self._update_ui()

    def undo_current(self):
        if self._eng: self._eng.undo(); self._update_ui()

    def _on_search(self, text):
        if self._eng and text: self._eng.find_text(text)
    def _on_fp(self):
        e = self._eng
        if e and e.is_open and e.current_page > 0: e.go_to_page(e.current_page-1)
    def _on_fn(self):
        e = self._eng
        if e and e.is_open and e.current_page < e.page_count-1: e.go_to_page(e.current_page+1)
    def _on_rp(self):
        if self._eng and self._eng.is_open: self._show_info("在结果列表中选择目标后替换")
    def _on_ra(self):
        if self._eng and self._eng.is_open: self._show_info("全部替换")

    def _on_loaded(self, fp, pc): self._update_ui()
    def _on_pc(self, pn, t):
        if self._eng and self._eng.current_page == pn:
            self.pl.setText(f"第 {pn+1}/{t} 页"); self._render()
    def _on_fc(self, results):
        self.rl.setText(f"共找到 {len(results)} 处" if results else "未找到匹配")

    def _render(self):
        e, t = self._eng, self._tab
        if not e or not e.is_open or not t: return
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
        if t.thumb_list.count() > 0: t.thumb_list.setCurrentRow(0)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls(): e.acceptProposedAction()
    def dropEvent(self, e):
        for url in e.mimeData().urls():
            p = url.toLocalFile()
            if p.lower().endswith(".pdf"): self._new_tab(p); add_recent(p); break

    def show_find_panel(self): self.find_panel.setVisible(True); self.fi.setFocus()
    def _on_zoom(self, t):
        try: self._zoom = int(t.replace("%","")); self._render()
        except: pass
    def toggle_theme(self):
        from qfluentwidgets import setTheme, Theme
        t = "dark" if not hasattr(self,'_th') or not self._th else "light"
        if t == "dark": setTheme(Theme.DARK)
        else: setTheme(Theme.LIGHT)
        self._th = (t == "dark"); save_theme(t); signal_bus.theme_changed.emit(t)

    def _show_info(self, msg):
        InfoBar.success(title="", content=msg, orient=Qt.Horizontal,
                        isClosable=True, position=InfoBarPosition.TOP_LEFT, duration=2000, parent=self)
    def _show_error(self, msg):
        InfoBar.error(title="", content=msg, orient=Qt.Horizontal,
                      isClosable=True, position=InfoBarPosition.TOP_LEFT, duration=3000, parent=self)

    def keyPressEvent(self, event):
        k, m = event.key(), event.modifiers()
        if k == Qt.Key_Escape:
            self.find_panel.setVisible(False)
            if self._add_text_mode:
                self._add_text_mode = False
                QApplication.restoreOverrideCursor()
        elif m == Qt.ControlModifier and k == Qt.Key_O: self.open_file_dialog()
        elif m == Qt.ControlModifier and k == Qt.Key_S:
            if m == Qt.ShiftModifier: self.save_as()
            else: self.save_current()
        elif m == Qt.ControlModifier and k == Qt.Key_Z: self.undo_current()
        elif m == Qt.ControlModifier and k == Qt.Key_F: self.show_find_panel()
        elif m == Qt.ControlModifier and k == Qt.Key_Plus: self._zoom_in()
        elif m == Qt.ControlModifier and k == Qt.Key_Minus: self._zoom_out()
        elif m == Qt.ControlModifier and k == Qt.Key_0: self._zoom=100; self.zc.setCurrentText("100%")
        elif k == Qt.Key_PageUp:
            if self._eng: self._eng.prev_page()
        elif k == Qt.Key_PageDown:
            if self._eng: self._eng.next_page()
        super().keyPressEvent(event)

    def _zoom_in(self):
        for z in ZOOM_LEVELS:
            if z > self._zoom: self._zoom=z; self.zc.setCurrentText(f"{z}%"); return
    def _zoom_out(self):
        for z in reversed(ZOOM_LEVELS):
            if z < self._zoom: self._zoom=z; self.zc.setCurrentText(f"{z}%"); return
