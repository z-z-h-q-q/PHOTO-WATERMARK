"""
预览控件模块，负责显示图片和水印预览。
依赖：PIL.Image, PyQt6
"""
from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QPixmap, QImage, QPainter
from PyQt6.QtCore import Qt
from PIL import Image


class PreviewWidget(QLabel):
    """增强版预览控件：支持parent参数 + 无图片提示 + PIL兼容"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(300, 200)
        self.image = None
        self.hint_text = "将图片拖拽到此处或点击导入按钮加载图片"
        self.setStyleSheet("color: gray; font-size: 14px;")

    def set_image(self, pil_img):
        """显示PIL图片为缩略图"""
        self.image = pil_img
        self.update()

    def pil2qimage(self, im):
        """PIL.Image 转 QImage"""
        if im.mode == "RGB":
            r, g, b = im.split()
            im = Image.merge("RGB", (b, g, r))
            data = im.tobytes("raw", "RGB")
            qimg = QImage(data, im.width, im.height, QImage.Format.Format_RGB888)
        elif im.mode == "RGBA":
            data = im.tobytes("raw", "RGBA")
            qimg = QImage(data, im.width, im.height, QImage.Format.Format_RGBA8888)
        else:
            im = im.convert("RGBA")
            data = im.tobytes("raw", "RGBA")
            qimg = QImage(data, im.width, im.height, QImage.Format.Format_RGBA8888)
        return qimg

    def paintEvent(self, event):
        """自定义绘制逻辑：无图时显示提示，有图时显示图像"""
        painter = QPainter(self)
        if self.image:
            qimg = self.pil2qimage(self.image)
            pixmap = QPixmap.fromImage(qimg)
            scaled = pixmap.scaled(
                self.width(), self.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        else:
            painter.setPen(Qt.GlobalColor.gray)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.hint_text)
