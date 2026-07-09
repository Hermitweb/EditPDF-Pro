"""PDF引擎——全部功能"""

import os, tempfile
import fitz
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from core.models import WatermarkConfig
from core.text_ops import TextOps
from core.page_ops import PageOps
from core.watermark_ops import WatermarkOps
from core.annotation_ops import AnnotationOps
from core.renderer import Renderer
from app.constants import PREVIEW_DPI, THUMBNAIL_DPI


class PDFEngine(QObject):
    document_loaded = pyqtSignal(str, int)
    page_changed = pyqtSignal(int, int)
    operation_completed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    find_completed = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._doc = None; self._filepath = ""; self._cur = 0
        self._modified = False; self._undo = []
        self._to = TextOps(); self._po = PageOps()
        self._wo = WatermarkOps(); self._ao = AnnotationOps()
        self._re = Renderer()

    def _snap(self):
        if not self._doc: return
        try:
            t = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False); t.close()
            self._doc.save(t.name, incremental=False, clean=True, garbage=4)
            self._undo.append(t.name)
            if len(self._undo) > 20:
                try: os.unlink(self._undo.pop(0))
                except: pass
        except: pass

    def undo(self):
        if not self._undo: return False
        s = self._undo.pop()
        try:
            nd = fitz.open(s); op, cp = self._filepath, self._cur
            if self._doc: self._doc.close()
            self._doc = nd; self._modified = True
            self._filepath = op; self._cur = min(cp, self._doc.page_count-1)
            self.document_loaded.emit(self._filepath, self._doc.page_count)
            self.page_changed.emit(self._cur, self._doc.page_count)
            self.operation_completed.emit("已撤销"); return True
        except: return False

    def open(self, fp):
        try:
            self._clean()
            if not os.path.exists(fp): return False
            self._doc = fitz.open(fp); self._filepath = fp
            self._cur = 0; self._modified = False; self._undo = []
            self.document_loaded.emit(fp, self._doc.page_count)
            self.page_changed.emit(0, self._doc.page_count); return True
        except: return False

    def save(self, op=None):
        p = op or self._filepath
        if not p: return False
        try:
            self._doc.save(p, incremental=False, clean=True, garbage=4, deflate=True)
            self._filepath = p; self._modified = False
            self.operation_completed.emit(f"已保存: {os.path.basename(p)}"); return True
        except: return False

    def close(self): self._clean()
    def _clean(self):
        if self._doc: self._doc.close(); self._doc = None
        self._filepath = ""; self._cur = 0; self._modified = False
        for s in self._undo:
            try: os.unlink(s)
            except: pass
        self._undo = []

    @property
    def is_open(self): return self._doc is not None
    @property
    def page_count(self): return self._doc.page_count if self._doc else 0
    @property
    def current_page(self): return self._cur
    @property
    def filepath(self): return self._filepath
    @property
    def modified(self): return self._modified

    def go_to_page(self, pn):
        if not self._doc: return
        self._cur = max(0, min(pn, self._doc.page_count-1))
        self.page_changed.emit(self._cur, self._doc.page_count)
    def next_page(self): self.go_to_page(self._cur+1)
    def prev_page(self): self.go_to_page(self._cur-1)
    def render_page(self, pn, dpi=PREVIEW_DPI):
        if not self._doc or pn<0 or pn>=self._doc.page_count: return None
        return self._re.render_page(self._doc[pn], dpi)
    def render_thumbnail(self, pn):
        if not self._doc or pn<0 or pn>=self._doc.page_count: return None
        return self._re.render_thumbnail(self._doc[pn])

    def find_text(self, text, cs=False):
        if not self._doc or not text: return []
        r = self._to.find_text(self._doc, text, cs)
        self.find_completed.emit(r); return r
    def replace_text(self, pn, rect, nt):
        if not self._doc: return False
        self._snap(); ok = self._to.replace_text(self._doc[pn], rect, nt)
        if ok: self._modified = True; return ok
    def replace_all(self, rs, nt):
        if not self._doc: return 0
        self._snap(); c = self._to.replace_all(self._doc, rs, nt)
        if c>0: self._modified = True; return c

    def add_text(self, pn, pos, text, fn="SimSun", fs=12, c=(0,0,0)):
        if not self._doc: return False
        self._snap()
        try:
            self._doc[pn].insert_text(pos, text, fontsize=fs, fontname=fn, color=c)
            self._modified = True; return True
        except:
            try:
                self._doc[pn].insert_text(pos, text, fontsize=fs, fontname="china-ss", color=c)
                self._modified = True; return True
            except: return False

    def merge_pdfs(self, fps, out): return self._po.merge_pdfs(fps, out)
    def split_pdf(self, d, r):
        return self._po.split_pdf(self._doc, d, r) if self._doc else []
    def insert_pdf(self, path, after=-1):
        if not self._doc: return 0
        self._snap()
        if after<0: after=self._cur
        p=self._po.insert_pdf(self._doc, path, after)
        if p>0: self._modified=True; self.document_loaded.emit(self._filepath, self._doc.page_count)
        return p
    def insert_blank_page(self, after=-1, size="A4"):
        if not self._doc: return 0
        self._snap()
        if after<0: after=self._cur
        from app.constants import PAGE_SIZES
        w,h=PAGE_SIZES.get(size,(210,297)); wp,hp=w*72/25.4, h*72/25.4
        r=self._po.insert_blank_page(self._doc, after, wp, hp)
        self._modified=True; self.document_loaded.emit(self._filepath, self._doc.page_count); return r
    def delete_pages(self, pns):
        if not self._doc: return 0
        self._snap(); c=self._po.delete_pages(self._doc, pns)
        if c>0:
            self._modified=True
            if self._cur>=self._doc.page_count: self._cur=self._doc.page_count-1
            self.document_loaded.emit(self._filepath, self._doc.page_count)
            self.page_changed.emit(self._cur, self._doc.page_count)
        return c
    def rotate_pages(self, pns, a=90):
        if not self._doc: return 0
        self._snap(); c=self._po.rotate_pages(self._doc, pns, a)
        if c>0: self._modified=True; return c
    def reorder_pages(self, no):
        if not self._doc: return False
        self._snap(); ok=self._po.reorder_pages(self._doc, no)
        if ok: self._modified=True; self.document_loaded.emit(self._filepath, self._doc.page_count)
        return ok
    def add_text_watermark(self, cfg, cb=None):
        if not self._doc: return 0
        self._snap(); c=self._wo.add_text_watermark(self._doc, cfg, cb)
        if c>0: self._modified=True; return c
    def add_image_watermark(self, cfg, cb=None):
        if not self._doc: return 0
        self._snap(); c=self._wo.add_image_watermark(self._doc, cfg, cb)
        if c>0: self._modified=True; return c
    def add_highlight(self, pn, rect):
        if not self._doc: return False
        self._snap(); ok=self._ao.add_highlight(self._doc[pn], rect)
        if ok: self._modified=True; return ok
    def is_encrypted(self): return self._doc.is_encrypted if self._doc else False
    def authenticate(self, pwd): return self._doc.authenticate(pwd) if self._doc else False
    def encrypt(self, pwd):
        if not self._doc: return False
        self._snap()
        try:
            t="__tmp_enc.pdf"
            self._doc.save(t, encryption=4, user_pw=pwd, owner_pw=pwd, clean=True, garbage=4)
            self._doc=fitz.open(t); self._modified=True
            self.operation_completed.emit("已加密"); return True
        except: return False
    def decrypt(self, pwd):
        if not self._doc: return False
        ok=self._doc.authenticate(pwd)
        if ok: self._snap(); self._modified=True; self.operation_completed.emit("已解密")
        return ok
    def extract_images(self, out_dir):
        if not self._doc: return []
        ex=[]
        try:
            for pn in range(self._doc.page_count):
                for ii in self._doc[pn].get_images():
                    xref=ii[0]; base=self._doc.extract_image(xref)
                    if base:
                        fp=os.path.join(out_dir, f"page{pn+1}_img{xref}.{base['ext']}")
                        with open(fp,"wb") as f: f.write(base["image"])
                        ex.append(fp)
            self.operation_completed.emit(f"提取 {len(ex)} 张图片")
        except: pass
        return ex
