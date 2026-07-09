"""验证字体匹配"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from PyQt5.QtWidgets import QApplication; app=QApplication(sys.argv)
import fitz
from core.text_ops import _init_system_fonts, _choose_font, _system_fonts
doc = fitz.open(); p = doc.new_page(); _init_system_fonts(p)

print("可用字体:", list(_system_fonts.keys()))
print()
tests = [
    ("SimSun","SimSun"), ("Song","SimSun"), ("宋体","SimSun"), ("STSong","SimSun"),
    ("SimHei","SimHei"), ("Heiti","SimHei"), ("黑体","SimHei"), ("Bold","SimHei"),
    ("KaiTi","KaiTi"), ("楷体","KaiTi"), ("FZXingKai","KaiTi"),
    ("FangSong","FangSong"), ("仿宋","FangSong"),
    ("YaHei","YaHei"), ("微软雅黑","YaHei"), ("Microsoft YaHei","YaHei"),
    ("MingLiU","SimSun"), ("Gothic","SimHei"),
    ("china-ss","china-ss"), ("UnknownFont","SimSun"),
]
for name, expect in tests:
    result = _choose_font(name)
    status = "✅" if result == expect else "❌"
    print(f"  {status} [{name:18}] -> {result:8} (期望: {expect})")
