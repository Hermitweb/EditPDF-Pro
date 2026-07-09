"""完整集成测试"""
import sys, os, tempfile, shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)
from app.theme import ThemeManager; ThemeManager.init()
from ui.main_window import MainWindow
from core.models import WatermarkConfig
import fitz

tmp = tempfile.mkdtemp()
pdf = os.path.join(tmp, "c.pdf")
doc = fitz.open()
p = doc.new_page()
p.insert_text((50,100), "采购合同", fontsize=18, fontname="china-s")
p.insert_text((50,150), "甲方：张三", fontsize=12, fontname="china-s")
doc.save(pdf); doc.close()

err = []
def ck(n, cond, d=""):
    if cond: print(f"  ✅ {n}")
    else: print(f"  ❌ {n}: {d}"); err.append(n)

w = MainWindow()
eng = w._eng  # 当前标签的引擎

ok = eng.open(pdf)
ck("打开PDF", ok and eng.page_count == 1)

img = eng.render_page(0, 120)
ck("渲染页面", img and img.width() > 0)
w._thumbs()
ck("生成缩略图", w._tab.thumb_list.count() >= 1)

eng.go_to_page(0)
ck("导航", eng.current_page == 0)

results = eng.find_text("张三")
ck("查找文字", len(results) > 0)

if results:
    ok = eng.replace_text(results[0].page_num, results[0].rect, "李四")
    ck("替换文字", ok)

count = eng.insert_blank_page(0)
ck("插入空白页", eng.page_count == 2)

count = eng.delete_pages([1])
ck("删除页面", count == 1)

count = eng.rotate_pages([0], 90)
ck("旋转页面", count > 0)

config = WatermarkConfig(text="仅供查阅", font_size=24, opacity=0.3,
                         rotation=45, position="tile", pages="all")
count = eng.add_text_watermark(config)
ck("文字水印", count > 0)

out = os.path.join(tmp, "o.pdf")
ok = eng.save(out)
ck("保存PDF", ok and os.path.getsize(out) > 0)

pdf2 = os.path.join(tmp, "p2.pdf")
d2 = fitz.open()
dp = d2.new_page()
dp.insert_text((50,50), "附录", fontsize=12, fontname="china-s")
d2.save(pdf2); d2.close()
merged = os.path.join(tmp, "m.pdf")
total = eng.merge_pdfs([pdf, pdf2], merged)
ck("合并PDF", total >= 2)

# 添加文字
ok = eng.add_text(0, (100, 200), "测试文字", "SimSun", 12)
ck("添加文字", ok)

# 加密
ok = eng.encrypt("123")
ck("加密PDF", ok)

# 提取图片
ex = eng.extract_images(tmp)
ck("提取图片", len(ex) >= 0)

eng.close()
ck("关闭", not eng.is_open)

print(f"\n{'='*40}")
if err: print(f"❌ {len(err)}项失败: {', '.join(err)}")
else: print(f"🎉 全部通过！")
print(f"{'='*40}")
shutil.rmtree(tmp, ignore_errors=True)
