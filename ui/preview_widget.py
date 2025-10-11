from PyQt6.QtWidgets import QLabel, QSizePolicy
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor, QFont
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PIL import Image, ImageDraw, ImageFont


class PreviewWidget(QLabel):
    watermark_moved = pyqtSignal(tuple)  # 拖拽结束发射 (x, y)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(300, 200)
        self.setStyleSheet("color: gray; font-size: 14px;")
        self.setAcceptDrops(True)

        # 图片和水印
        self.image = None
        self.hint_text = "将图片拖拽到此处或点击导入按钮加载图片"

        self.current_settings = {}
        self.watermark_text = ""
        self.font_family = "Arial"
        self.font_size = 36
        self.bold = False
        self.italic = False
        self.color = QColor(255, 255, 255, 180)

        self.watermark_pos = None  # 原图坐标
        self.dragging = False
        self.drag_offset = (0, 0)
        self.min_margin = 10
        self.bottom_offset = 0

        # 可选调试框
        self.show_watermark_box = False

        # 修正左侧文件列表变小的问题
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

    # ------------------- 兼容 update_preview -------------------
    def update_preview(self):
        if self.current_settings:
            self.watermark_text = self.current_settings.get("text", "")
            self.font_family = self.current_settings.get("font_family", "Arial")
            self.font_size = self.current_settings.get("font_size", 36)
            self.bold = self.current_settings.get("bold", False)
            self.italic = self.current_settings.get("italic", False)
            color = self.current_settings.get("color", (255, 255, 255, 180))
            self.color = QColor(*color)
        else:
            self.watermark_text = ""

        if self.image and self.watermark_text and self.watermark_pos is None:
            self.set_watermark_position_preset("center")

        self.update()

    # ------------------- 拖拽导入 -------------------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        paths = [u.toLocalFile() for u in urls if u.toLocalFile().lower().endswith(
            ('.png', '.jpg', '.jpeg', '.bmp', '.tiff'))]
        if paths:
            top_window = self.window()
            if hasattr(top_window, "add_images"):
                top_window.add_images(paths)

    # ------------------- 设置图片 -------------------
    def set_image(self, pil_img):
        self.image = pil_img
        self.watermark_pos = None
        self.update_preview()

    # ------------------- 水印拖拽 -------------------
    def mousePressEvent(self, event):
        if self.is_over_watermark(event.pos()):
            self.dragging = True
            wx, wy = self.watermark_pos or (0, 0)
            scaled_w, scaled_h, x_offset, y_offset = self._get_scaled_geometry()
            ratio_w = scaled_w / self.image.width
            ratio_h = scaled_h / self.image.height
            self.drag_offset = (event.x() - (x_offset + wx * ratio_w),
                                event.y() - (y_offset + wy * ratio_h))

    def mouseMoveEvent(self, event):
        if self.dragging and self.image:
            scaled_w, scaled_h, x_offset, y_offset = self._get_scaled_geometry()
            ratio_w = self.image.width / scaled_w
            ratio_h = self.image.height / scaled_h

            new_x = (event.x() - x_offset - self.drag_offset[0]) * ratio_w
            new_y = (event.y() - y_offset - self.drag_offset[1]) * ratio_h

            wm_w, wm_h = self.get_watermark_size()
            new_x = max(self.min_margin, min(new_x, self.image.width - wm_w - self.min_margin))
            new_y = max(self.min_margin, min(new_y, self.image.height - wm_h - self.min_margin))

            self.watermark_pos = (new_x, new_y)
            self.update()

    def mouseReleaseEvent(self, event):
        if self.dragging:
            self.dragging = False
            if self.watermark_pos:
                self.watermark_moved.emit(self.watermark_pos)

    def is_over_watermark(self, pos: QPoint):
        if not self.image or not self.watermark_text or not self.watermark_pos:
            return False

        scaled_w, scaled_h, x_offset, y_offset = self._get_scaled_geometry()
        ratio_w = scaled_w / self.image.width
        ratio_h = scaled_h / self.image.height

        wx = x_offset + self.watermark_pos[0] * ratio_w
        wy = y_offset + self.watermark_pos[1] * ratio_h
        wm_w, wm_h = self.get_watermark_size()
        wm_w *= ratio_w
        wm_h *= ratio_h

        x, y = pos.x(), pos.y()
        return wx <= x <= wx + wm_w and wy <= y <= wy + wm_h

    # ------------------- 水印尺寸 -------------------
    def get_watermark_size(self):
        if not self.watermark_text or not self.image:
            return 0, 0
        try:
            font = ImageFont.truetype(self.font_family, self.font_size)
        except:
            font = ImageFont.load_default()
        dummy = Image.new("RGB", (10, 10))
        draw = ImageDraw.Draw(dummy)
        try:
            bbox = draw.textbbox((0, 0), self.watermark_text, font=font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            w, h = draw.textsize(self.watermark_text, font=font)
        return w, h

    # ------------------- 水印位置预设 -------------------
    def set_watermark_position_preset(self, position_name):
        if not self.image or not self.watermark_text:
            return
        img_w, img_h = self.image.width, self.image.height
        wm_w, wm_h = self.get_watermark_size()
        positions = {
            "top-left": (self.min_margin, self.min_margin),
            "top-right": (img_w - wm_w - self.min_margin, self.min_margin),
            "bottom-left": (self.min_margin, img_h - wm_h - self.min_margin - self.bottom_offset),
            "bottom-right": (img_w - wm_w - self.min_margin,
                             img_h - wm_h - self.min_margin - self.bottom_offset),
            "center": ((img_w - wm_w)//2, (img_h - wm_h)//2),
        }
        x, y = positions.get(position_name, positions["center"])
        x = max(self.min_margin, min(x, img_w - wm_w - self.min_margin))
        y = max(self.min_margin, min(y, img_h - wm_h - self.min_margin))
        self.watermark_pos = (x, y)
        self.update()

    # ------------------- 绘制 -------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if self.image:
            qimg = self._pil2qimage(self.image)
            pixmap = QPixmap.fromImage(qimg)
            scaled_w, scaled_h, x_offset, y_offset = self._get_scaled_geometry()
            scaled_pixmap = pixmap.scaled(
                int(scaled_w), int(scaled_h),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            painter.drawPixmap(int(x_offset), int(y_offset), scaled_pixmap)

            if self.watermark_text and self.watermark_pos:
                ratio_w = scaled_w / self.image.width
                ratio_h = scaled_h / self.image.height
                wm_x = x_offset + self.watermark_pos[0] * ratio_w
                wm_y = y_offset + self.watermark_pos[1] * ratio_h

                font = QFont(self.font_family, max(int(self.font_size * ratio_h), 1))
                font.setBold(self.bold)
                font.setItalic(self.italic)
                painter.setFont(font)
                painter.setPen(self.color)
                painter.drawText(int(wm_x), int(wm_y + font.pointSize()), self.watermark_text)

                if self.show_watermark_box:
                    wm_w, wm_h = self.get_watermark_size()
                    wm_w *= ratio_w
                    wm_h *= ratio_h
                    painter.setPen(QColor(255, 0, 0, 180))
                    painter.drawRect(int(wm_x), int(wm_y), int(wm_w), int(wm_h))
        else:
            painter.setPen(Qt.GlobalColor.gray)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.hint_text)

    # ------------------- PIL -> QImage -------------------
    def _pil2qimage(self, im):
        if im.mode == "RGB":
            r, g, b = im.split()
            im = Image.merge("RGB", (b, g, r))
            data = im.tobytes("raw", "RGB")
            return QImage(data, im.width, im.height, QImage.Format.Format_RGB888)
        elif im.mode == "RGBA":
            data = im.tobytes("raw", "RGBA")
            return QImage(data, im.width, im.height, QImage.Format.Format_RGBA8888)
        else:
            im = im.convert("RGBA")
            data = im.tobytes("raw", "RGBA")
            return QImage(data, im.width, im.height, QImage.Format.Format_RGBA8888)

    # ------------------- 缩放计算 -------------------
    def _get_scaled_geometry(self):
        if not self.image:
            return 0, 0, 0, 0
        img_w, img_h = self.image.width, self.image.height
        widget_w, widget_h = self.width(), self.height()
        ratio = min(widget_w / img_w, widget_h / img_h)
        scaled_w = img_w * ratio
        scaled_h = img_h * ratio
        x_offset = (widget_w - scaled_w) / 2
        y_offset = (widget_h - scaled_h) / 2
        return scaled_w, scaled_h, x_offset, y_offset
