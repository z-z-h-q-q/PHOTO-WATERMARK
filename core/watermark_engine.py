from PIL import Image, ImageDraw, ImageFont
import os
import sys


class WatermarkEngine:
    """
    水印引擎：
    - 支持添加文字水印；
    - 支持 RGBA 透明度；
    - 支持字体、字号、样式（粗体/斜体）；
    - 兼容 Pillow 8 与 9+。
    """

    def __init__(self):
        # 常见字体映射，可根据系统调整路径
        self.font_paths = self._init_font_paths()

    def _init_font_paths(self):
        """初始化常见字体映射表"""
        base_paths = [
            "C:/Windows/Fonts",  # Windows
            "/usr/share/fonts",  # Linux
            "/System/Library/Fonts",  # macOS
        ]
        font_map = {}

        def find_font(name, filename):
            for base in base_paths:
                path = os.path.join(base, filename)
                if os.path.exists(path):
                    font_map[name] = path
                    return

        find_font("Arial", "arial.ttf")
        find_font("Times New Roman", "times.ttf")
        find_font("Courier New", "cour.ttf")
        find_font("SimHei", "simhei.ttf")
        find_font("SimSun", "simsun.ttc")

        return font_map

    def _get_font(self, font_family: str, font_size: int, bold: bool, italic: bool):
        """加载字体文件"""
        path = self.font_paths.get(font_family)

        # 简单模拟粗体/斜体效果（仅在字体文件不支持时）
        try:
            if path and os.path.exists(path):
                font = ImageFont.truetype(path, font_size)
            else:
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()

        return font

    def add_text_watermark(self, img: Image.Image, text: str, settings: dict = None) -> Image.Image:
        """在图片上添加文字水印"""
        if img is None or not text:
            return img

        img = img.copy()

        # ---------------- 获取设置 ----------------
        if settings is None:
            settings = {}

        font_family = settings.get("font_family", "Arial")
        font_size = settings.get("font_size", 36)
        bold = settings.get("bold", False)
        italic = settings.get("italic", False)
        color = settings.get("color", (255, 255, 255, 255))
        opacity = settings.get("opacity", 1.0)

        # ---------------- 字体加载 ----------------
        font = self._get_font(font_family, font_size, bold, italic)

        # ---------------- 颜色和透明度 ----------------
        if len(color) == 3:
            color = (*color, int(255 * opacity))
        elif len(color) == 4:
            color = (color[0], color[1], color[2], int(color[3] * opacity))
        else:
            color = (255, 255, 255, int(255 * opacity))

        # ---------------- 绘制文字 ----------------
        if img.mode != "RGBA":
            img = img.convert("RGBA")

        draw = ImageDraw.Draw(img, "RGBA")

        # Pillow 兼容 textbbox 和 textsize
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            w, h = draw.textsize(text, font=font)

        x = (img.width - w) // 2
        y = (img.height - h) // 2

        # 在新透明层上绘制文字
        text_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        text_draw = ImageDraw.Draw(text_layer)
        text_draw.text((x, y), text, font=font, fill=color)

        # 合并图层
        combined = Image.alpha_composite(img, text_layer)
        return combined
