"""页面管理页面——合并/拆分/旋转/插入/删除"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFileDialog,
)
from qfluentwidgets import (
    PrimaryPushButton, PushButton, CardWidget,
    BodyLabel, TitleLabel, CaptionLabel,
    FluentIcon, InfoBar, MessageBox,
    LineEdit,
)


class PageManagePage(QWidget):
    """页面管理页面"""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main = main_window
        self._setup_ui()

    @property
    def _eng(self):
        return self.main._eng

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)

        title = TitleLabel("页面管理")
        layout.addWidget(title)

        # ── 合并PDF ──
        merge_card = CardWidget(self)
        merge_layout = QHBoxLayout(merge_card)
        merge_layout.addWidget(BodyLabel("合并PDF"))
        merge_layout.addWidget(CaptionLabel("将多个PDF合并为一个文件"), 1)
        merge_btn = PrimaryPushButton(FluentIcon.ADD_TO, "选择文件并合并")
        merge_btn.clicked.connect(self._on_merge)
        merge_layout.addWidget(merge_btn)
        layout.addWidget(merge_card)

        # ── 拆分PDF ──
        split_card = CardWidget(self)
        split_layout = QHBoxLayout(split_card)
        split_layout.addWidget(BodyLabel("拆分PDF"))

        self.split_range = LineEdit()
        self.split_range.setPlaceholderText("例如: 1-3, 5, 7-9")
        self.split_range.setFixedWidth(200)
        split_layout.addWidget(self.split_range)
        split_layout.addWidget(CaptionLabel("输入页面范围，逗号分隔", self), 1)
        split_btn = PrimaryPushButton(FluentIcon.CUT, "拆分提取")
        split_btn.clicked.connect(self._on_split)
        split_layout.addWidget(split_btn)
        layout.addWidget(split_card)

        # ── 插入/删除页面 ──
        page_card = CardWidget(self)
        page_layout = QHBoxLayout(page_card)
        page_layout.addWidget(BodyLabel("插入"))
        insert_blank_btn = PushButton("空白页(A4)", self)
        insert_blank_btn.clicked.connect(self._on_insert_blank)
        page_layout.addWidget(insert_blank_btn)
        insert_file_btn = PushButton("从文件插入", self)
        insert_file_btn.clicked.connect(self._on_insert_file)
        page_layout.addWidget(insert_file_btn)
        page_layout.addSpacing(20)
        page_layout.addWidget(BodyLabel("删除"))
        delete_btn = PushButton(FluentIcon.DELETE, "删除当前页")
        delete_btn.clicked.connect(self._on_delete)
        page_layout.addWidget(delete_btn)
        page_layout.addStretch()
        layout.addWidget(page_card)

        # ── 旋转页面 ──
        rotate_card = CardWidget(self)
        rotate_layout = QHBoxLayout(rotate_card)
        rotate_layout.addWidget(BodyLabel("旋转当前页"))
        r90 = PushButton("90°")
        r90.clicked.connect(lambda: self._on_rotate(90))
        r180 = PushButton("180°")
        r180.clicked.connect(lambda: self._on_rotate(180))
        r270 = PushButton("270°")
        r270.clicked.connect(lambda: self._on_rotate(270))
        rotate_layout.addWidget(r90)
        rotate_layout.addWidget(r180)
        rotate_layout.addWidget(r270)
        rotate_layout.addStretch()
        layout.addWidget(rotate_card)

        layout.addStretch()

    def _on_merge(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择要合并的PDF", "", "PDF文件 (*.pdf)")
        if len(files) < 2:
            InfoBar.warning(title="", content="请至少选择2个PDF文件",
                            orient=Qt.Horizontal, isClosable=True,
                            duration=3000, parent=self)
            return
        out_path, _ = QFileDialog.getSaveFileName(
            self, "保存合并结果", "合并.pdf", "PDF文件 (*.pdf)")
        if not out_path:
            return
        total = self._eng.merge_pdfs(files, out_path)
        InfoBar.success(title="", content=f"合并完成: {len(files)}个文件 → {total}页",
                        orient=Qt.Horizontal, isClosable=True,
                        duration=4000, parent=self)

    def _on_split(self):
        if not self._eng.is_open:
            InfoBar.warning(title="", content="请先打开一个PDF文件",
                            orient=Qt.Horizontal, isClosable=True,
                            duration=3000, parent=self)
            return
        text = self.split_range.text().strip()
        if not text:
            InfoBar.warning(title="", content="请输入页面范围，例如: 1-3, 5",
                            orient=Qt.Horizontal, isClosable=True,
                            duration=3000, parent=self)
            return
        ranges = self._parse_ranges(text)
        if not ranges:
            return
        import tempfile
        out_dir = tempfile.mkdtemp()
        files = self._eng.split_pdf(out_dir, ranges)
        InfoBar.success(title="", content=f"已拆分: 生成 {len(files)} 个文件",
                        orient=Qt.Horizontal, isClosable=True,
                        duration=4000, parent=self)

    def _parse_ranges(self, text):
        ranges = []
        for part in text.replace("，", ",").split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                try:
                    a, b = part.split("-")
                    start, end = int(a.strip())-1, int(b.strip())-1
                    ranges.append((start, end))
                except:
                    InfoBar.error(title="", content=f"格式错误: {part}",
                                  orient=Qt.Horizontal, isClosable=True,
                                  duration=3000, parent=self)
                    return []
            else:
                try:
                    ranges.append((int(part)-1, int(part)-1))
                except:
                    InfoBar.error(title="", content=f"格式错误: {part}",
                                  orient=Qt.Horizontal, isClosable=True,
                                  duration=3000, parent=self)
                    return []
        return ranges

    def _on_insert_blank(self):
        if not self._eng.is_open: return
        self._eng.insert_blank_page(self._eng.current_page)

    def _on_insert_file(self):
        if not self._eng.is_open: return
        path, _ = QFileDialog.getOpenFileName(self, "选择要插入的PDF", "", "PDF文件 (*.pdf)")
        if path:
            self._eng.insert_pdf(path, self._eng.current_page)

    def _on_delete(self):
        if not self._eng.is_open: return
        page = self._eng.current_page
        box = MessageBox("确认删除", f"确定删除第 {page+1} 页吗？", self)
        if box.exec():
            self._eng.delete_pages([page])

    def _on_rotate(self, angle):
        if not self._eng.is_open: return
        self._eng.rotate_pages([self._eng.current_page], angle)
