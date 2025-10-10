"""
预览控件模块，负责显示图片和水印预览。
依赖：PIL.Image, PyQt5
"""
from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from PIL import Image

class PreviewWidget(QLabel):
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(300, 200)

    def set_image(self, pil_img):
        """显示PIL图片为缩略图"""
        if pil_img is None:
            self.clear()
            return
        qimg = self.pil2qimage(pil_img)
        pixmap = QPixmap.fromImage(qimg)
        scaled = pixmap.scaled(self.width(), self.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(scaled)

    def pil2qimage(self, im):
        """PIL.Image 转 QImage"""
        if im.mode == "RGB":
            r, g, b = im.split()
            im = Image.merge("RGB", (b, g, r))
            data = im.tobytes("raw", "RGB")
            qimg = QImage(data, im.width, im.height, QImage.Format_RGB888)
        elif im.mode == "RGBA":
            data = im.tobytes("raw", "RGBA")
            qimg = QImage(data, im.width, im.height, QImage.Format_RGBA8888)
        else:
            im = im.convert("RGBA")
            data = im.tobytes("raw", "RGBA")
            qimg = QImage(data, im.width, im.height, QImage.Format_RGBA8888)
        return qimg
