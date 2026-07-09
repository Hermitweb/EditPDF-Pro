"""水印工具页面"""

import os
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog
from qfluentwidgets import (
    PrimaryPushButton, PushButton, CardWidget,
    BodyLabel, TitleLabel, CaptionLabel,
    FluentIcon, InfoBar, LineEdit,
    ComboBox, DoubleSpinBox,
)
from core.models import WatermarkConfig


class WatermarkPage(QWidget):
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
        title = TitleLabel("水印工具")
        layout.addWidget(title)

        tc = CardWidget(self)
        tl = QVBoxLayout(tc); tl.setSpacing(12)
        tl.addWidget(BodyLabel("文字水印"))
        r1 = QHBoxLayout()
        r1.addWidget(BodyLabel("文字:"))
        self.text_input = LineEdit()
        self.text_input.setPlaceholderText("例如: 仅供查阅")
        self.text_input.setText("仅供查阅"); self.text_input.setFixedWidth(200)
        r1.addWidget(self.text_input); r1.addSpacing(20)
        r1.addWidget(BodyLabel("字体大小:"))
        self.font_size = ComboBox()
        self.font_size.addItems(["12","18","24","36","48","72"])
        self.font_size.setCurrentText("24"); self.font_size.setFixedWidth(80)
        r1.addWidget(self.font_size); r1.addSpacing(20)
        r1.addWidget(BodyLabel("透明度:"))
        self.opacity = DoubleSpinBox()
        self.opacity.setRange(0.05, 1.0); self.opacity.setSingleStep(0.05)
        self.opacity.setValue(0.3); self.opacity.setFixedWidth(80)
        r1.addWidget(self.opacity); r1.addStretch()
        tl.addLayout(r1)

        r2 = QHBoxLayout()
        r2.addWidget(BodyLabel("旋转角度:"))
        self.rotation = ComboBox()
        self.rotation.addItems(["0","15","30","45","60","90"])
        self.rotation.setCurrentText("45"); self.rotation.setFixedWidth(80)
        r2.addWidget(self.rotation); r2.addSpacing(20)
        r2.addWidget(BodyLabel("位置:"))
        self.position = ComboBox()
        self.position.addItems(["居中","平铺","左上","右上","左下","右下"])
        self.position.setCurrentText("平铺"); self.position.setFixedWidth(120)
        r2.addWidget(self.position); r2.addSpacing(20)
        at = PrimaryPushButton(FluentIcon.COMPLETED, "应用文字水印")
        at.clicked.connect(self._on_text_watermark)
        r2.addWidget(at); r2.addStretch()
        tl.addLayout(r2)
        layout.addWidget(tc)

        ic = CardWidget(self)
        il = QHBoxLayout(ic)
        il.addWidget(BodyLabel("图片水印"))
        self.ip = CaptionLabel("未选择图片")
        self.ip.setStyleSheet("color:#888;")
        il.addWidget(self.ip, 1)
        si = PushButton(FluentIcon.PHOTO, "选择图片")
        si.clicked.connect(self._on_select_image)
        il.addWidget(si)
        ai = PrimaryPushButton(FluentIcon.SAVE, "应用图片水印")
        ai.clicked.connect(self._on_image_watermark)
        il.addWidget(ai)
        layout.addWidget(ic)
        layout.addStretch()
        self._sel = ""

    def _make_config(self):
        pm = {"居中":"center","平铺":"tile","左上":"top-left",
              "右上":"top-right","左下":"bottom-left","右下":"bottom-right"}
        return WatermarkConfig(
            text=self.text_input.text().strip(),
            font_size=int(self.font_size.currentText()),
            opacity=self.opacity.value(),
            rotation=int(self.rotation.currentText()),
            position=pm.get(self.position.currentText(),"center"),
            pages="all", image_path=self._sel)

    def _on_text_watermark(self):
        if not self._eng.is_open: return
        if not self.text_input.text().strip(): return
        c = self._eng.add_text_watermark(self._make_config())
        InfoBar.success(title="",content=f"文字水印已应用到 {c} 页",
                        orient=Qt.Horizontal,isClosable=True,
                        duration=3000,parent=self)
        self.main._render()

    def _on_select_image(self):
        p,_ = QFileDialog.getOpenFileName(self,"选择水印图片","",
                                          "图片文件 (*.png *.jpg *.jpeg *.bmp)")
        if p:
            self._sel = p
            self.ip.setText("✅ "+os.path.basename(p))
            self.ip.setStyleSheet("color:#4CAF50;")

    def _on_image_watermark(self):
        if not self._eng.is_open: return
        if not self._sel: return
        c = self._eng.add_image_watermark(self._make_config())
        InfoBar.success(title="",content=f"图片水印已应用到 {c} 页",
                        orient=Qt.Horizontal,isClosable=True,
                        duration=3000,parent=self)
        self.main._render()
