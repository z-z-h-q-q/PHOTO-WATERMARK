"""
水印引擎模块，负责文字水印绘制。
依赖：PIL.Image, PIL.ImageDraw, PIL.ImageFont
"""
from PIL import ImageDraw, ImageFont

class WatermarkEngine:
    def add_text_watermark(self, img, text):
        """在图片右下角添加白色文字水印，返回新图片"""
        if img is None:
            return None
        img = img.copy()
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 36)
        except:
            font = ImageFont.load_default()
        text_size = draw.textbbox((0, 0), text, font=font)
        text_width = text_size[2] - text_size[0]
        text_height = text_size[3] - text_size[1]
        x = img.width - text_width - 20
        y = img.height - text_height - 20
        draw.text((x, y), text, fill="white", font=font)
        return img
