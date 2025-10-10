"""
图片水印处理模块，负责添加图片水印。
依赖：PIL.Image
"""
from PIL import Image

class ImageWatermark:
    def add_image_watermark(self, base_image, watermark_image, position='bottom-right', opacity=0.5):
        """
        添加图片水印
        :param base_image: PIL.Image 基础图片
        :param watermark_image: PIL.Image 水印图片
        :param position: 水印位置 ('top-left', 'top-right', 'bottom-left', 'bottom-right', 'center')
        :param opacity: 水印透明度 (0-1)
        :return: PIL.Image
        """
        if None in (base_image, watermark_image):
            return None

        # 转换图片模式确保兼容性
        if base_image.mode != 'RGBA':
            base_image = base_image.convert('RGBA')
        if watermark_image.mode != 'RGBA':
            watermark_image = watermark_image.convert('RGBA')

        # 调整水印大小（默认为基础图片的1/4）
        max_size = (base_image.width // 4, base_image.height // 4)
        watermark_image.thumbnail(max_size, Image.Resampling.LANCZOS)

        # 计算位置
        position_map = {
            'top-left': (0, 0),
            'top-right': (base_image.width - watermark_image.width, 0),
            'bottom-left': (0, base_image.height - watermark_image.height),
            'bottom-right': (base_image.width - watermark_image.width, 
                           base_image.height - watermark_image.height),
            'center': ((base_image.width - watermark_image.width) // 2,
                      (base_image.height - watermark_image.height) // 2)
        }
        x, y = position_map.get(position, position_map['bottom-right'])

        # 创建新图层
        transparent = Image.new('RGBA', base_image.size, (0, 0, 0, 0))
        transparent.paste(watermark_image, (x, y))

        # 调整透明度
        mask = transparent.split()[3].point(lambda x: x * opacity)
        transparent.putalpha(mask)

        # 合并图层
        return Image.alpha_composite(base_image, transparent)