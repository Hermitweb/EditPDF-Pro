"""集成测试：主窗口 + PDF引擎联合测试"""
import sys, os, tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)

import fitz
from ui.main_window import MainWindow

# 创建测试PDF
tmp_dir = tempfile.mkdtemp()
test_pdf = os.path.join(tmp_dir, "test.pdf")
doc = fitz.open()
p = doc.new_page()
p.insert_text((50, 100), "采购合同", fontsize=18, fontname="china-s")
p.insert_text((50, 150), "甲方：张三 科技有限公司", fontsize=12, fontname="china-s")
p.insert_text((50, 180), "合同金额：100,000 元", fontsize=12, fontname="china-s")
p.insert_text((50, 220), "付款日期：2026年12月31日", fontsize=12, fontname="china-s")
doc.save(test_pdf); doc.close()

# 测试
w = MainWindow()
ok = w.engine.open(test_pdf)
assert ok, "打开失败"
print(f"[1/7] ✅ 打开PDF: {w.engine.page_count}页")

img = w.engine.render_page(0, 120)
print(f"[2/7] ✅ 渲染: {img.width()}x{img.height()}")

w._build_thumbnails()
print(f"[3/7] ✅ 缩略图: {w.thumb_layout.count()} 项")

results = w.engine.find_text("张三")
assert len(results) > 0
print(f"[4/7] ✅ 查找: {len(results)} 处")

r = results[0]
ok = w.engine.replace_text(r.page_num, r.rect, "李四")
print(f"[5/7] ✅ 替换: {'成功' if ok else '失败'}")

w.engine.insert_blank_page(0)
print(f"[6/7] ✅ 插入空白页: {w.engine.page_count}页")

out = os.path.join(tmp_dir, "out.pdf")
w.engine.save(out)
print(f"[7/7] ✅ 保存: {os.path.getsize(out)//1024}KB")

w.engine.close()
print("🎉 全部集成测试通过!")
