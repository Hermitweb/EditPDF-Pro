"""PDF引擎集成测试——CI 兼容（无 GUI）"""

import os, sys, tempfile, shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest

from PyQt5.QtWidgets import QApplication
_app = QApplication.instance()
if not _app:
    _app = QApplication(["--platform", "offscreen"])

import fitz
from core.pdf_engine import PDFEngine


@pytest.fixture
def test_pdf():
    tmp_dir = tempfile.mkdtemp()
    path = os.path.join(tmp_dir, "test.pdf")
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 100), "采购合同", fontsize=18, fontname="china-s")
    page.insert_text((50, 150), "甲方：张三 科技有限公司", fontsize=12, fontname="china-s")
    page.insert_text((50, 220), "合同金额：100,000 元", fontsize=12, fontname="china-s")
    doc.save(path); doc.close()
    yield path
    shutil.rmtree(tmp_dir, ignore_errors=True)


def test_open_pdf(test_pdf):
    engine = PDFEngine()
    assert engine.open(test_pdf), "打开失败"
    assert engine.page_count == 1
    engine.close()


def test_find_text(test_pdf):
    engine = PDFEngine()
    engine.open(test_pdf)
    r = engine.find_text("张三")
    assert len(r) >= 1
    r2 = engine.find_text("不存在")
    assert len(r2) == 0
    engine.close()


def test_find_numbers(test_pdf):
    engine = PDFEngine()
    engine.open(test_pdf)
    r = engine.find_text("100,000")
    assert len(r) == 1
    engine.close()


def test_replace_text(test_pdf):
    engine = PDFEngine()
    engine.open(test_pdf)
    results = engine.find_text("张三")
    assert results
    r = results[0]
    ok = engine.replace_text(r.page_num, r.rect, "王五")
    assert ok
    after = engine.find_text("王五")
    assert len(after) >= 1
    engine.close()


def test_render_page(test_pdf):
    engine = PDFEngine()
    engine.open(test_pdf)
    img = engine.render_page(0, 72)
    assert img is not None
    assert img.width() > 0
    engine.close()


def test_render_thumbnail(test_pdf):
    engine = PDFEngine()
    engine.open(test_pdf)
    thumb = engine.render_thumbnail(0)
    assert thumb is not None
    engine.close()


def test_navigation(test_pdf):
    engine = PDFEngine()
    engine.open(test_pdf)
    engine.go_to_page(0)
    engine.next_page()
    engine.prev_page()
    assert engine.current_page == 0
    engine.close()


def test_save(test_pdf):
    engine = PDFEngine()
    engine.open(test_pdf)
    tmp = tempfile.mkdtemp()
    out = os.path.join(tmp, "out.pdf")
    assert engine.save(out)
    assert os.path.exists(out)
    assert os.path.getsize(out) > 0
    engine.close()
    shutil.rmtree(tmp, ignore_errors=True)
