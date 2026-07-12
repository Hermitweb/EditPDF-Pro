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

w = MainWindow()
eng = w._eng  # Use property, not direct attribute
assert eng is not None, "引擎不存在"

ok = eng.open(test_pdf)
assert ok, "打开失败"
print(f"[1/7] ✅ 打开PDF: {eng.page_count}页")

img = eng.render_page(0, 120)
assert img is not None
print(f"[2/7] ✅ 渲染: {img.width()}x{img.height()}")

w._thumbs()
tc = w._tab
assert tc is not None
print(f"[3/7] ✅ 缩略图: {tc.thumb_list.count()}项")

results = eng.find_text("张三")
assert len(results) > 0
print(f"[4/7] ✅ 查找: {len(results)}处")

r = results[0]
ok = eng.replace_text(r.page_num, r.rect, "李四")
assert ok
print(f"[5/7] ✅ 替换成功")

eng.insert_blank_page(0)
print(f"[6/7] ✅ 插入空白页: {eng.page_count}页")

out = os.path.join(tmp_dir, "out.pdf")
eng.save(out)
print(f"[7/7] ✅ 保存: {os.path.getsize(out)//1024}KB")

eng.close()
print("🎉 全部集成测试通过!")
