# ui/preview_widget.py
from PyQt6.QtWidgets import QLabel, QSizePolicy
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor, QFont, QFontMetrics
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PIL import Image, ImageDraw, ImageFont


class PreviewWidget(QLabel):
    watermark_moved = pyqtSignal(tuple)  # 拖拽结束发射比例坐标 (0~1, 0~1)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(300, 200)
        self.setStyleSheet("color: gray; font-size: 14px;")
        self.setAcceptDrops(True)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        # 图片和水印属性
        self.image = None
        self.hint_text = "将图片拖拽到此处或点击导入按钮加载图片"

        self.current_settings = {}
        self.watermark_text = ""
        self.font_family = "Arial"
        self.font_size = 36
        self.bold = False
        self.italic = False
        self.color = QColor(255, 255, 255, 180)

        self.watermark_pos = None  # 比例坐标 (0~1, 0~1)
        self.dragging = False
        self.drag_offset = (0, 0)
        self.min_margin = 10  # 边距像素

    # ------------------- 设置图片 -------------------
    def set_image(self, pil_img):
        self.image = pil_img
        self.watermark_pos = None
        self.update_preview()

    # ------------------- 更新预览 -------------------
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

        # 默认居中位置
        if self.image and self.watermark_text and self.watermark_pos is None:
            self.set_watermark_position_preset("center")

        self.update()

    # ------------------- 拖拽水印 -------------------
    def mousePressEvent(self, event):
        pos = event.position()  # PyQt6 返回 QPointF
        if self.is_over_watermark(pos):
            self.dragging = True
            # 计算鼠标点击位置与水印左上角的偏移量（在预览控件坐标系中）
            wm_x_px, wm_y_px = self.get_watermark_pixel_pos()
            scaled_w, scaled_h, x_offset, y_offset = self._get_scaled_geometry()
            ratio_w = scaled_w / self.image.width
            ratio_h = scaled_h / self.image.height

            preview_wm_x = x_offset + wm_x_px * ratio_w
            preview_wm_y = y_offset + wm_y_px * ratio_h

            self.drag_offset = (
                pos.x() - preview_wm_x,
                pos.y() - preview_wm_y
            )

    def mouseMoveEvent(self, event):
        if self.dragging and self.image and self.watermark_text:
            pos = event.position()
            scaled_w, scaled_h, x_offset, y_offset = self._get_scaled_geometry()
            ratio_w = scaled_w / self.image.width
            ratio_h = scaled_h / self.image.height

            # 计算新的水印位置（在预览控件坐标系中）
            preview_new_x = pos.x() - self.drag_offset[0]
            preview_new_y = pos.y() - self.drag_offset[1]

            # 转换为原图像素坐标
            new_x = (preview_new_x - x_offset) / ratio_w
            new_y = (preview_new_y - y_offset) / ratio_h

            wm_w, wm_h = self.get_watermark_size()

            # 边界限制 - 确保水印完全在图片内
            new_x = max(0, min(new_x, self.image.width - wm_w))
            new_y = max(0, min(new_y, self.image.height - wm_h))

            # 转换为比例坐标
            if self.image.width - wm_w > 0 and self.image.height - wm_h > 0:
                self.watermark_pos = (
                    new_x / (self.image.width - wm_w),
                    new_y / (self.image.height - wm_h)
                )
            else:
                # 如果水印比图片大，放在左上角
                self.watermark_pos = (0, 0)

            self.update()

    def mouseReleaseEvent(self, event):
        if self.dragging:
            self.dragging = False
            if self.watermark_pos:
                self.watermark_moved.emit(self.watermark_pos)

    def is_over_watermark(self, pos):
        """检查鼠标是否在水印上"""
        # pos 可以是 QPointF 或 QPoint
        if isinstance(pos, QPoint):
            x, y = pos.x(), pos.y()
        else:
            x, y = pos.x(), pos.y()

        if not self.image or not self.watermark_text or not self.watermark_pos:
            return False

        wm_x_px, wm_y_px = self.get_watermark_pixel_pos()
        scaled_w, scaled_h, x_offset, y_offset = self._get_scaled_geometry()
        ratio_w = scaled_w / self.image.width
        ratio_h = scaled_h / self.image.height

        wm_w, wm_h = self.get_watermark_size()
        preview_wm_w = wm_w * ratio_w
        preview_wm_h = wm_h * ratio_h
        preview_wm_x = x_offset + wm_x_px * ratio_w
        preview_wm_y = y_offset + wm_y_px * ratio_h

        return (preview_wm_x <= x <= preview_wm_x + preview_wm_w and 
                preview_wm_y <= y <= preview_wm_y + preview_wm_h)

    # ------------------- 水印尺寸 -------------------
    def get_watermark_size(self):
        """使用Qt计算水印文本的实际尺寸，确保与绘制时一致"""
        if not self.watermark_text or not self.image:
            return 0, 0
        
        # 使用Qt字体计算文本尺寸，确保与绘制时一致
        font = QFont(self.font_family, self.font_size)
        font.setBold(self.bold)
        font.setItalic(self.italic)
        
        font_metrics = QFontMetrics(font)
        text_rect = font_metrics.boundingRect(self.watermark_text)
        
        return text_rect.width(), text_rect.height()

    # ------------------- 九宫格预设 -------------------
    def set_watermark_position_preset(self, position_name: str):
        if not self.image or not self.watermark_text:
            return

        positions_ratio = {
            "top-left": (0, 0),
            "top-right": (1, 0),
            "bottom-left": (0, 1),
            "bottom-right": (1, 1),
            "center": (0.5, 0.5),
        }
        self.watermark_pos = positions_ratio.get(position_name, (0.5, 0.5))
        self.update()

    # ------------------- 坐标转换 -------------------
    def get_watermark_pixel_pos(self):
        """比例坐标 -> 原图像素坐标"""
        if not self.image or not self.watermark_text or not self.watermark_pos:
            return 0, 0
            
        wm_w, wm_h = self.get_watermark_size()
        img_w, img_h = self.image.width, self.image.height

        # 计算可移动范围
        movable_width = max(0, img_w - wm_w)
        movable_height = max(0, img_h - wm_h)
        
        # 将比例坐标转换为像素坐标
        px = self.watermark_pos[0] * movable_width
        py = self.watermark_pos[1] * movable_height

        # 防止越界
        px = max(0, min(px, movable_width))
        py = max(0, min(py, movable_height))
        return px, py

    # ------------------- 绘制 -------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        if not self.image:
            painter.setPen(Qt.GlobalColor.gray)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.hint_text)
            return

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
            wm_x, wm_y = self.get_watermark_pixel_pos()
            ratio_w = scaled_w / self.image.width
            ratio_h = scaled_h / self.image.height

            # 计算在预览控件上的绘制位置
            draw_x = x_offset + wm_x * ratio_w
            draw_y = y_offset + wm_y * ratio_h

            # 创建缩放后的字体
            font = QFont(self.font_family, max(int(self.font_size * ratio_h), 1))
            font.setBold(self.bold)
            font.setItalic(self.italic)
            painter.setFont(font)
            painter.setPen(self.color)

            # 使用Qt绘制文本，确保位置准确
            painter.drawText(int(draw_x), int(draw_y), int(self.image.width * ratio_w), 
                           int(self.image.height * ratio_h), 
                           Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, 
                           self.watermark_text)

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

    # ------------------- QLabel 缩放计算 -------------------
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