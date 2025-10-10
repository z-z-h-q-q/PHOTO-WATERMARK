"""
图片导出模块，负责保存图片到本地。
依赖：PIL.Image
"""
class Exporter:
    def save_image(self, img, path):
        """保存PIL图片到指定路径"""
        try:
            img.save(path)
            return True
        except Exception as e:
            print(f"保存图片失败: {e}")
            return False
