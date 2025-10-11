from PIL import Image, ImageDraw, ImageFont
import os


class WatermarkEngine:
    """
    水印引擎：
    - 支持文字水印
    - 支持字体、字号、粗体/斜体
    - 支持 RGBA 透明度
    - 支持中英文混排
    - 斜体效果自然
    - 水印居中
    - 兼容 Pillow 8/9+
    """

    def __init__(self):
        self.font_paths = self._init_font_paths()

    def _init_font_paths(self):
        """初始化常见字体映射表"""
        base_paths = [
            "C:/Windows/Fonts",
            "/usr/share/fonts",
            "/System/Library/Fonts",
        ]
        font_map = {}

        def find_font(name, filename):
            for base in base_paths:
                path = os.path.join(base, filename)
                if os.path.exists(path):
                    font_map[name] = path
                    return

        # 英文字体
        find_font("Arial", "arial.ttf")
        find_font("Arial Bold", "arialbd.ttf")
        find_font("Arial Italic", "ariali.ttf")
        find_font("Arial Bold Italic", "arialbi.ttf")

        find_font("Times New Roman", "times.ttf")
        find_font("Times New Roman Bold", "timesbd.ttf")
        find_font("Times New Roman Italic", "timesi.ttf")
        find_font("Times New Roman Bold Italic", "timesbi.ttf")

        find_font("Courier New", "cour.ttf")
        find_font("Courier New Bold", "courbd.ttf")
        find_font("Courier New Italic", "couri.ttf")
        find_font("Courier New Bold Italic", "courbi.ttf")

        # 中文字体
        find_font("SimHei", "simhei.ttf")
        find_font("SimSun", "simsun.ttc")

        return font_map

    def _get_font(self, font_family: str, font_size: int, bold: bool, italic: bool, text: str = ""):
        """
        获取字体：
        - 中文使用 SimHei/SimSun
        - 英文使用用户选择字体
        """
        has_chinese = any('\u4e00' <= c <= '\u9fff' for c in text)

        # 构建字体 key
        key = font_family
        if bold and italic:
            key += " Bold Italic"
        elif bold:
            key += " Bold"
        elif italic:
            key += " Italic"

        # 尝试用户选择字体
        path = self.font_paths.get(key)
        if path and os.path.exists(path):
            try:
                font = ImageFont.truetype(path, font_size)
                if has_chinese and font_family not in ["SimHei", "SimSun"]:
                    # 中文回退
                    for cf in ["SimHei", "SimSun"]:
                        cf_path = self.font_paths.get(cf)
                        if cf_path and os.path.exists(cf_path):
                            return ImageFont.truetype(cf_path, font_size)
                return font
            except:
                pass

        # 回退普通字体
        path = self.font_paths.get(font_family)
        if path and os.path.exists(path):
            try:
                return ImageFont.truetype(path, font_size)
            except:
                pass

        # 中文兜底
        for cf in ["SimHei", "SimSun"]:
            path = self.font_paths.get(cf)
            if path and os.path.exists(path):
                try:
                    return ImageFont.truetype(path, font_size)
                except:
                    continue

        return ImageFont.load_default()

    def add_text_watermark(self, img: Image.Image, text: str, settings: dict = None, custom_pos: tuple = None) -> Image.Image:
        """添加文字水印"""
        if img is None or not text:
            return img

        img = img.copy()
        if settings is None:
            settings = {}

        font_family = settings.get("font_family", "SimHei")
        font_size = settings.get("font_size", 36)
        bold = settings.get("bold", False)
        italic = settings.get("italic", False)
        color = settings.get("color", (255, 255, 255, 255))
        opacity = settings.get("opacity", 1.0)

        if len(color) == 3:
            color = (*color, int(255 * opacity))
        elif len(color) == 4:
            color = (color[0], color[1], color[2], int(color[3] * opacity))
        else:
            color = (255, 255, 255, int(255 * opacity))

        if img.mode != "RGBA":
            img = img.convert("RGBA")

        # 新建透明图层
        text_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(text_layer)

        # ---------- 中英文混排绘制 ----------
        x_offset, y_offset = 0, 0
        max_h = 0
        char_sizes = []

        # 先计算总宽度和最大高度
        for char in text:
            char_font = self._get_font(font_family, font_size, bold, italic, text=char)
            try:
                bbox = draw.textbbox((0, 0), char, font=char_font)
                w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            except AttributeError:
                try:
                    w, h = char_font.getsize(char)
                except AttributeError:
                    w, h = font_size, font_size
            char_sizes.append((char, char_font, w, h))
            x_offset += w
            max_h = max(max_h, h)

        # ---------- 创建单独文字图层 ----------
        single_layer = Image.new("RGBA", (x_offset + 20, max_h + 20), (0, 0, 0, 0))
        draw_single = ImageDraw.Draw(single_layer)

        # 绘制每个字符
        x_cursor = 10
        for char, char_font, w, h in char_sizes:
            offsets = [(0, 0)]
            if bold:
                offsets += [(1, 0), (0, 1), (1, 1)]
            for dx, dy in offsets:
                draw_single.text((x_cursor + dx, 10 + dy), char, font=char_font, fill=color)
            x_cursor += w

        # 斜体仿射
        if italic:
            shear = 0.25
            new_w = int(single_layer.width + max_h * shear)
            single_layer = single_layer.transform(
                (new_w, single_layer.height),
                Image.AFFINE,
                (1, shear, 0, 0, 1, 0),
                resample=Image.BICUBIC
            )

        # ---------- 水印位置 ----------
        if custom_pos and isinstance(custom_pos, tuple):
            final_x, final_y = custom_pos
        else:
            final_x = (img.width - single_layer.width) // 2
            final_y = (img.height - single_layer.height) // 2

        text_layer.paste(single_layer, (final_x, final_y), single_layer)
        combined = Image.alpha_composite(img, text_layer)
        return combined
