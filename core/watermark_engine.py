from PIL import Image, ImageDraw, ImageFont
import os


class WatermarkEngine:
    """
    水印引擎：
    - 支持文字水印
    - 支持字体、字号、粗体/斜体
    - 支持 RGBA 透明度
    - 斜体效果自然，无阴影/重叠
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

        # 常规字体和粗体/斜体
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

        find_font("SimHei", "simhei.ttf")
        find_font("SimSun", "simsun.ttc")

        return font_map

    def _get_font(self, font_family: str, font_size: int, bold: bool, italic: bool):
        """加载字体文件，优先选择粗体/斜体对应文件"""
        key = font_family
        if bold and italic:
            key += " Bold Italic"
        elif bold:
            key += " Bold"
        elif italic:
            key += " Italic"

        path = self.font_paths.get(key)
        if path and os.path.exists(path):
            try:
                return ImageFont.truetype(path, font_size)
            except:
                pass

        # 回退普通字体
        path = self.font_paths.get(font_family)
        if path and os.path.exists(path):
            try:
                return ImageFont.truetype(path, font_size)
            except:
                pass

        return ImageFont.load_default()

    def add_text_watermark(self, img: Image.Image, text: str, settings: dict = None) -> Image.Image:
        """在图片上添加文字水印"""
        if img is None or not text:
            return img

        img = img.copy()

        if settings is None:
            settings = {}

        font_family = settings.get("font_family", "Arial")
        font_size = settings.get("font_size", 36)
        bold = settings.get("bold", False)
        italic = settings.get("italic", False)
        color = settings.get("color", (255, 255, 255, 255))
        opacity = settings.get("opacity", 1.0)

        font = self._get_font(font_family, font_size, bold, italic)

        # 处理颜色和透明度
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

        # ---------- 创建单独文字图层，处理粗体与斜体 ----------
        # 先计算文字尺寸
        dummy_draw = ImageDraw.Draw(img)
        try:
            bbox = dummy_draw.textbbox((0, 0), text, font=font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            w, h = dummy_draw.textsize(text, font=font)

        # 创建文字图层
        single_layer = Image.new("RGBA", (w + 20, h + 20), (0, 0, 0, 0))
        single_draw = ImageDraw.Draw(single_layer)

        # 粗体绘制
        offsets = [(0, 0)]
        if bold:
            offsets += [(1, 0), (0, 1), (1, 1)]
        for dx, dy in offsets:
            single_draw.text((dx + 10, dy + 10), text, font=font, fill=color)  # +10 防止裁剪

        # 斜体仿射
        if italic:
            shear = 0.25  # 斜体倾斜程度，可调
            new_w = int(single_layer.width + h * shear)
            single_layer = single_layer.transform(
                (new_w, single_layer.height),
                Image.AFFINE,
                (1, shear, 0, 0, 1, 0),
                resample=Image.BICUBIC
            )

        # ---------- 将文字图层贴回原图层，保持居中 ----------
        final_x = (img.width - single_layer.width) // 2
        final_y = (img.height - single_layer.height) // 2
        text_layer.paste(single_layer, (final_x, final_y), single_layer)

        # 合并图层
        combined = Image.alpha_composite(img, text_layer)
        return combined
