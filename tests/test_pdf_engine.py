"""PDF引擎集成测试——创建测试PDF并验证各项功能"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import fitz
from core.pdf_engine import PDFEngine


def create_test_pdf(path: str):
    """创建包含中文的测试PDF"""
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


def test_pdf_engine():
    tmp_dir = tempfile.mkdtemp()
    test_pdf = os.path.join(tmp_dir, "test_contract.pdf")
    create_test_pdf(test_pdf)

    engine = PDFEngine()
    passed = 0; total = 0

    # 1. 打开
    total += 1
    assert engine.open(test_pdf), "打开失败"
    assert engine.page_count == 2, f"页数: {engine.page_count} != 2"
    passed += 1; print(f"[{passed}/{total}] ✅ 打开: {engine.page_count}页")

    # 2. 查找
    total += 1
    results = engine.find_text("张三")
    assert len(results) >= 1, f"应找到至少1处'张三', 实际: {len(results)}"
    passed += 1; print(f"[{passed}/{total}] ✅ 查找'张三': {len(results)}处")

    total += 1
    results2 = engine.find_text("100,000")
    assert len(results2) == 1
    passed += 1; print(f"[{passed}/{total}] ✅ 查找'100,000': {len(results2)}处")

    total += 1
    results3 = engine.find_text("不存在的文字")
    assert len(results3) == 0
    passed += 1; print(f"[{passed}/{total}] ✅ 查无结果: 0处")

    # 3. 替换
    total += 1
    if results:
        r = results[0]
        ok = engine.replace_text(r.page_num, r.rect, "王五")
        assert ok, "替换失败"
        after = engine.find_text("张三")
        print(f"[{passed+1}/{total}] ✅ 替换'张三'→'王五', 剩余'张三': {len(after)}处")
        passed += 1

    # 4. 渲染
    total += 1
    img = engine.render_page(engine.current_page, 72)
    assert img is not None
    passed += 1; print(f"[{passed}/{total}] ✅ 渲染: {img.width()}x{img.height()}")

    total += 1
    thumb = engine.render_thumbnail(0)
    assert thumb is not None
    passed += 1; print(f"[{passed}/{total}] ✅ 缩略图渲染")

    # 5. 导航
    total += 1
    engine.go_to_page(1)
    assert engine.current_page == 1
    engine.go_to_page(0)
    assert engine.current_page == 0
    passed += 1; print(f"[{passed}/{total}] ✅ 页面导航")

    # 6. 保存
    total += 1
    out = os.path.join(tmp_dir, "output.pdf")
    assert engine.save(out), "保存失败"
    assert os.path.exists(out)
    passed += 1; print(f"[{passed}/{total}] ✅ 保存: {os.path.getsize(out)//1024}KB")

    # 7. 关闭
    total += 1
    engine.close()
    assert not engine.is_open
    passed += 1; print(f"[{passed}/{total}] ✅ 关闭")

    print(f"\n{'='*40}")
    print(f"🎉 {passed}/{total} 全部通过！")
    print(f"{'='*40}")

    import shutil; shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_pdf_engine()
