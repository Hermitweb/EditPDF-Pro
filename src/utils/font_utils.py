"""Windows 字体动态检测 — 从注册表获取已安装字体"""

import os, winreg

CN_FONT_KEYWORDS = [
    "yahei", "msyh", "microsoft yahei", "微软雅黑", "雅黑",
    "simhei", "黑体", "hei",
    "simsun", "宋体", "song", "sung",
    "simkai", "楷体", "kaiti", "kai",
    "simfang", "仿宋", "fangsong", "fang",
    "simli", "隶书", "lishu",
    "simyou", "幼圆", "youyuan",
    "dengxian", "等线",
    "xin", "新宋体",
]


def get_installed_cn_fonts():
    fonts = {}
    fonts_dir = r"C:\Windows\Fonts"
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                             r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts")
        i = 0
        while True:
            try:
                name, value, _ = winreg.EnumValue(key, i)
                name_lower = name.lower()
                is_cn = any(kw in name_lower for kw in CN_FONT_KEYWORDS)
                if not is_cn:
                    i += 1; continue
                fp = value
                if not os.path.isabs(fp):
                    fp = os.path.join(fonts_dir, fp)
                if not os.path.exists(fp):
                    i += 1; continue
                family = name.split(" (")[0].split(" & ")[0].strip()
                if family and family not in fonts:
                    fonts[family] = fp
                i += 1
            except OSError:
                break
        winreg.CloseKey(key)
    except Exception:
        pass
    fallback = {
        "SimSun": os.path.join(fonts_dir, "simsun.ttc"),
        "SimHei": os.path.join(fonts_dir, "simhei.ttf"),
        "KaiTi": os.path.join(fonts_dir, "simkai.ttf"),
        "FangSong": os.path.join(fonts_dir, "simfang.ttf"),
        "Microsoft YaHei": os.path.join(fonts_dir, "msyh.ttc"),
    }
    for name, path in fallback.items():
        if os.path.exists(path) and name not in fonts:
            fonts[name] = path
    return fonts


def get_available_font_names():
    fonts = get_installed_cn_fonts()
    names = sorted(fonts.keys(), key=_font_priority)
    return names


def _font_priority(name):
    n = name.lower()
    if "yahei" in n or "msyh" in n: return 0
    if "hei" in n and "yahei" not in n: return 1
    if "fang" in n: return 2
    if "song" in n or "sun" in n: return 3
    if "kai" in n: return 4
    return 5
