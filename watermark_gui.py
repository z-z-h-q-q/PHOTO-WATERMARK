import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                           QFileDialog, QScrollArea)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QDragEnterEvent, QDropEvent
from PIL import Image, ImageDraw, ImageFont

class ThumbnailLabel(QLabel):
    def __init__(self, main_window, pixmap=None):
        super().__init__()
        self.main_window = main_window
        self.setAcceptDrops(True)
        if pixmap:
            self.setPixmap(pixmap)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(200, 200)
        self.setStyleSheet("border: 2px dashed #aaa")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for f in files:
            if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                self.main_window.add_image(f)

class WatermarkApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.image_paths = []
        self.current_image = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('图片水印工具')
        self.setMinimumSize(800, 600)

        # 主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # 图片预览区
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_layout = QHBoxLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)

        # 拖放区域
        self.drop_label = ThumbnailLabel(self)
        self.drop_label.setText("拖放图片到这里")
        layout.addWidget(self.drop_label)

        # 水印文本输入
        text_layout = QHBoxLayout()
        text_label = QLabel("水印文本：")
        self.text_input = QLineEdit()
        text_layout.addWidget(text_label)
        text_layout.addWidget(self.text_input)
        layout.addLayout(text_layout)

        # 按钮区域
        button_layout = QHBoxLayout()
        select_btn = QPushButton("选择图片")
        select_btn.clicked.connect(self.select_images)
        generate_btn = QPushButton("生成水印")
        generate_btn.clicked.connect(self.generate_watermark)
        button_layout.addWidget(select_btn)
        button_layout.addWidget(generate_btn)
        layout.addLayout(button_layout)

    def add_image(self, path):
        if path not in self.image_paths:
            self.image_paths.append(path)
            pixmap = QPixmap(path)
            label = QLabel()
            scaled_pixmap = pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio)
            label.setPixmap(scaled_pixmap)
            self.scroll_layout.addWidget(label)

    def select_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择图片",
            "",
            "Images (*.png *.jpg *.jpeg)"
        )
        for f in files:
            self.add_image(f)

    def generate_watermark(self):
        if not self.image_paths:
            return

        watermark_text = self.text_input.text()
        if not watermark_text:
            return

        output_dir = QFileDialog.getExistingDirectory(
            self,
            "选择保存目录"
        )
        if not output_dir:
            return

        for img_path in self.image_paths:
            try:
                # 打开图片
                img = Image.open(img_path)
                # 创建绘图对象
                draw = ImageDraw.Draw(img)
                # 使用默认字体
                try:
                    font = ImageFont.truetype("arial.ttf", 36)
                except:
                    font = ImageFont.load_default()

                # 获取文本大小
                text_bbox = draw.textbbox((0, 0), watermark_text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]

                # 计算位置（右下角，留出边距）
                x = img.width - text_width - 20
                y = img.height - text_height - 20

                # 绘制水印
                draw.text((x, y), watermark_text, fill='white', font=font)

                # 保存图片
                output_path = os.path.join(
                    output_dir,
                    'watermark_' + os.path.basename(img_path)
                )
                img.save(output_path)

            except Exception as e:
                print(f"处理图片 {img_path} 时出错: {e}")

def main():
    app = QApplication(sys.argv)
    window = WatermarkApp()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()