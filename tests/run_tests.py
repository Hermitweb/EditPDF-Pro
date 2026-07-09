"""PDF引擎快速测试（含PyQt5 QApplication初始化）"""

import os, sys, tempfile

# 必须在导入QObject前创建QApplication
from PyQt5.QtWidgets import QApplication
_qapp = QApplication(sys.argv)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import fitz
from core.pdf_engine import PDFEngine


def create_test_pdf(path: str):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 100), "采购合同", fontsize=18, fontname="china-s")
    page.insert_text((50, 150), "甲方：张三 科技有限公司", fontsize=12, fontname="china-s")
    page.insert_text((50, 180), "乙方：李四 贸易有限公司", fontsize=12, fontname="china-s")
    page.insert_text((50, 220), "合同金额：100,000 元人民币", fontsize=12, fontname="china-s")
    page.insert_text((50, 260), "付款日期：2026年12月31日前付清全款。", fontsize=12, fontname="china-s")
    page.insert_text((50, 300), "本合同一式两份，甲乙双方各执一份。", fontsize=12, fontname="china-s")
    page2 = doc.new_page()
    page2.insert_text((50, 100), "合同条款（续）", fontsize=18, fontname="china-s")
    page2.insert_text((50, 150), "甲方代表：张三", fontsize=12, fontname="china-s")
    page2.insert_text((50, 180), "乙方代表：李四", fontsize=12, fontname="china-s")
    doc.save(path, clean=True)
    doc.close()
    print(f"✅ 测试PDF已创建: {path}")


def main():
    tmp_dir = tempfile.mkdtemp()
    test_pdf = os.path.join(tmp_dir, "test_contract.pdf")
    create_test_pdf(test_pdf)

    engine = PDFEngine()

    # 1. 打开
    assert engine.open(test_pdf), "❌ 打开失败"
    assert engine.page_count == 2
    assert engine.is_open
    print(f"✅ 打开成功: {engine.page_count} 页")

    # 2. 文档信息
    info = engine.get_document_info()
    assert info.page_count == 2
    print(f"✅ 文档信息: {info.filename}, {info.file_size_str}")

    # 3. 查找
    r1 = engine.find_text("张三")
    assert len(r1) > 0
    print(f"✅ 查找'张三': {len(r1)} 处")

    r2 = engine.find_text("100,000")
    assert len(r2) > 0
    print(f"✅ 查找'100,000': {len(r2)} 处")

    r3 = engine.find_text("不存在的文字")
    assert len(r3) == 0
    print(f"✅ 查找不存在文字: 0处")

    # 4. 替换
    if r1:
        ok = engine.replace_text(r1[0].page_num, r1[0].rect, "李四")
        assert ok
        print(f"✅ 替换'张三'→'李四' 成功")

    # 5. 渲染
    img = engine.render_current_page(72)
    assert img is not None
    print(f"✅ 渲染当前页: {img.width}x{img.height}")

    thumb = engine.render_thumbnail(0)
    assert thumb is not None
    print(f"✅ 缩略图渲染成功")

    # 6. 导航
    engine.next_page(); assert engine.current_page == 1
    engine.prev_page(); assert engine.current_page == 0
    print(f"✅ 页面导航正常")

    # 7. 保存
    out = os.path.join(tmp_dir, "output.pdf")
    assert engine.save(out)
    assert os.path.exists(out)
    print(f"✅ 保存成功: {out}")

    # 8. 页面操作
    engine.open(test_pdf)
    blank_idx = engine.insert_blank_page(0)
    assert blank_idx == 1
    print(f"✅ 插入空白页成功")

    del_count = engine.delete_pages([0])
    assert del_count == 1
    print(f"✅ 删除页面成功")

    rotate_count = engine.rotate_pages([0], 90)
    assert rotate_count == 1
    print(f"✅ 旋转页面成功")

    # 9. 关闭
    engine.close()
    assert not engine.is_open
    print(f"✅ 关闭成功")

    print(f"\n{'='*40}")
    print(f"🎉 全部核心测试通过！")
    print(f"{'='*40}")

    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
