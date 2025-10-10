"""
图片加载与缩略图生成模块。
依赖：PIL.Image
"""
from PIL import Image

class ImageLoader:
    def load_image(self, path):
        """加载图片为PIL.Image对象"""
        try:
            img = Image.open(path)
            return img.convert("RGBA")
        except Exception as e:
            print(f"加载图片失败: {e}")
            return None
