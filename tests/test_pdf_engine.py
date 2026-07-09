"""PDF引擎集成测试——创建一个测试PDF并验证各项功能"""

import os
import sys
import tempfile

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import fitz
from core.pdf_engine import PDFEngine
from core.text_ops import TextOps


def create_test_pdf(path: str):
    """创建包含中文的测试PDF"""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (50, 100),
        "采购合同",
        fontsize=18,
        fontname="china-s",
    )
    page.insert_text(
        (50, 150),
        "甲方：张三 科技有限公司",
        fontsize=12,
        fontname="china-s",
    )
    page.insert_text(
        (50, 180),
        "乙方：李四 贸易有限公司",
        fontsize=12,
        fontname="china-s",
    )
    page.insert_text(
        (50, 220),
        "合同金额：100,000 元人民币",
        fontsize=12,
        fontname="china-s",
    )
    page.insert_text(
        (50, 260),
        "付款日期：2026年12月31日前付清全款。",
        fontsize=12,
        fontname="china-s",
    )
    page.insert_text(
        (50, 300),
        "本合同一式两份，甲乙双方各执一份。",
        fontsize=12,
        fontname="china-s",
    )

    # 第二页
    page2 = doc.new_page()
    page2.insert_text(
        (50, 100),
        "合同条款（续）",
        fontsize=18,
        fontname="china-s",
    )
    page2.insert_text(
        (50, 150),
        "甲方代表：张三",
        fontsize=12,
        fontname="china-s",
    )
    page2.insert_text(
        (50, 180),
        "乙方代表：李四",
        fontsize=12,
        fontname="china-s",
    )

    doc.save(path, clean=True)
    doc.close()
    print(f"✅ 测试PDF已创建: {path}")


def test_pdf_engine():
    """测试PDF引擎各项功能"""
    # 创建测试文件
    tmp_dir = tempfile.mkdtemp()
    test_pdf = os.path.join(tmp_dir, "test_contract.pdf")
    create_test_pdf(test_pdf)

    engine = PDFEngine()

    # 1. 测试打开
    assert engine.open(test_pdf), "❌ 打开失败"
    assert engine.page_count == 2, f"❌ 页数不对: {engine.page_count}"
    assert engine.is_open, "❌ 应处于打开状态"
    print(f"✅ 打开成功: {engine.page_count} 页")

    # 2. 测试文档信息
    info = engine.get_document_info()
    assert info.page_count == 2
    assert "test_contract" in info.filename
    print(f"✅ 文档信息: {info.filename}, {info.file_size_str}")

    # 3. 测试查找文字
    results = engine.find_text("张三")
    assert len(results) > 0, "❌ 应找到'张三'"
    print(f"✅ 查找'张三': 找到 {len(results)} 处")

    results2 = engine.find_text("100,000")
    assert len(results2) > 0, "❌ 应找到'100,000'"
    print(f"✅ 查找'100,000': 找到 {len(results2)} 处")

    results3 = engine.find_text("不存在的文字")
    assert len(results3) == 0, "❌ 不应找到不存在的文字"
    print(f"✅ 查找不存在的文字: 0处, 正确")

    # 4. 测试替换文字
    if results:
        r = results[0]
        ok = engine.replace_text(r.page_num, r.rect, "李四")
        assert ok, "❌ 替换失败"
        print(f"✅ 替换'张三'→'李四' 成功")

        # 验证替换后查找不到原文字
        after_results = engine.find_text("张三")
        print(f"   替换后查找'张三': {len(after_results)} 处 (已替换的不再计入)")

    # 5. 测试渲染
    img = engine.render_current_page(dpi=72)
    assert img is not None, "❌ 渲染失败"
    print(f"✅ 渲染当前页: {img.width}x{img.height}")

    thumb = engine.render_thumbnail(0)
    assert thumb is not None, "❌ 缩略图渲染失败"
    print(f"✅ 缩略图渲染成功")

    # 6. 测试导航
    engine.next_page()
    assert engine.current_page == 1, f"❌ 下一页失败"
    engine.prev_page()
    assert engine.current_page == 0, f"❌ 上一页失败"
    engine.go_to_page(1)
    assert engine.current_page == 1, f"❌ 跳转失败"
    print(f"✅ 页面导航正常")

    # 7. 测试保存
    output_pdf = os.path.join(tmp_dir, "test_output.pdf")
    ok = engine.save(output_pdf)
    assert ok, "❌ 保存失败"
    assert os.path.exists(output_pdf), "❌ 输出文件不存在"
    print(f"✅ 保存成功: {output_pdf}")

    # 8. 测试关闭
    engine.close()
    assert not engine.is_open, "❌ 关闭后不应处于打开状态"
    print(f"✅ 关闭成功")

    print(f"\n{'='*40}")
    print(f"🎉 全部测试通过！")
    print(f"{'='*40}")

    # 清理
    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_pdf_engine()
