"""文字查找替换——字体匹配终极方案"""

import fitz, os
from core.models import FindResult

_font_cache = {}
_system_fonts = {}


def _init_system_fonts(page):
    pid = id(page)
    if pid in _font_cache:
        return
    from utils.font_utils import get_installed_cn_fonts
    fonts = get_installed_cn_fonts()
    for name, path in fonts.items():
        try:
            page.insert_font(fontname=name, fontfile=path)
            _system_fonts[name] = name
        except:
            pass
    _system_fonts["china-ss"] = "china-ss"
    _font_cache[pid] = dict(_system_fonts)


def _choose_font(detected_name: str) -> str:
    if not _system_fonts:
        return "china-ss"
    key = detected_name.lower().strip()
    if key in {"china-s", "china-ss", "china-ssb", "china-sb"}:
        return key
    for fn in _system_fonts:
        if key in fn.lower() or fn.lower() in key:
            return fn
    priorities = [
        (["yahei", "msyh", "microsoft"], []),
        (["hei"], ["yahei"]),
        (["fang"], []),
        (["song", "sun", "ming"], ["fang"]),
        (["kai"], []),
    ]
    for keywords, excludes in priorities:
        if any(k in key for k in keywords) and not any(e in key for e in excludes):
            for kw_priority in ([keywords[0]] + [k for k in ["song", "sun", "hei"] if k not in keywords]):
                for fn in _system_fonts:
                    if kw_priority in fn.lower():
                        return fn
    for fn in _system_fonts:
        if fn != "china-ss":
            return fn
    return "china-ss"


def _detect_style(page, rect):
    r = {"color": (0, 0, 0), "fontsize": 12, "fontname": "china-ss", "found": False}
    x0, y0, x1, y1 = rect
    try:
        clip = fitz.Rect(max(0, x0-30), max(0, y0-30), x1+30, min(page.rect.height, y1+30))
        best = -1
        for b in page.get_text("dict", clip=clip).get("blocks", []):
            for l in b.get("lines", []):
                for s in l.get("spans", []):
                    if not s["text"].strip(): continue
                    ox, oy = max(x0, s["bbox"][0]), max(y0, s["bbox"][1])
                    ox2, oy2 = min(x1, s["bbox"][2]), min(y1, s["bbox"][3])
                    ov = max(0, ox2-ox)*max(0, oy2-oy)
                    if ov > best:
                        best = ov
                        r["color"] = _int_color_to_rgb(s["color"])
                        r["fontsize"] = s["size"]
                        r["fontname"] = s["font"]
                        r["found"] = True
    except:
        pass
    return r


def _int_color_to_rgb(ci):
    return (((ci >> 16) & 0xFF) / 255.0, ((ci >> 8) & 0xFF) / 255.0, (ci & 0xFF) / 255.0)


class TextOps:
    _next_id = 0
    @classmethod
    def _get_id(cls):
        cls._next_id += 1
        return cls._next_id

    @staticmethod
    def find_text(doc, text, case_sensitive=False):
        results = []
        if not text: return results
        for pn in range(doc.page_count):
            try:
                for r in doc[pn].search_for(text):
                    results.append(FindResult(id=TextOps._get_id(), page_num=pn,
                                              rect=(r.x0, r.y0, r.x1, r.y1), matched_text=text))
            except: continue
        return results

    @staticmethod
    def replace_text(page, rect, new_text, fontname="", fontsize=12):
        x0, y0, x1, y1 = rect
        w, h = max(1, x1-x0), max(1, y1-y0)
        _init_system_fonts(page)
        style = _detect_style(page, rect)
        color = style["color"]
        pts = style["fontsize"] if (style["found"] and style["fontsize"] > 0) else max(6, h)
        detected = style["fontname"]
        use_font = _choose_font(detected)
        page.draw_rect(fitz.Rect(x0-1, y0-3, x1+1, y1+1), fill=(1, 1, 1), width=0)
        tw = fitz.get_text_length(new_text, fontname="china-ss", fontsize=pts)
        cx = x0 + (w - tw) / 2
        by = (y0 + y1) / 2 + pts * 0.35
        page.insert_text((cx, by), new_text, fontsize=pts, fontname=use_font, color=color)
        return True

    @staticmethod
    def replace_all(doc, results, new_text, fontname="", fontsize=12):
        c = 0
        for r in results:
            if r.replaced: continue
            if TextOps.replace_text(doc[r.page_num], r.rect, new_text, fontname, fontsize):
                r.replaced = True; c += 1
        return c
