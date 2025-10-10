"""
主窗口模块，负责UI布局、用户交互和信号处理。
依赖：ui.preview_widget, core.image_loader, core.watermark_engine, core.exporter
"""
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QLineEdit, QFileDialog, QLabel, QMessageBox
from ui.preview_widget import PreviewWidget
from core.image_loader import ImageLoader
from core.watermark_engine import WatermarkEngine
from core.exporter import Exporter

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图片水印工具 MVP")
        self.setMinimumSize(600, 400)

        # 控制器/核心模块
        self.image_loader = ImageLoader()
        self.watermark_engine = WatermarkEngine()
        self.exporter = Exporter()

        # UI 组件
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)


        self.preview = PreviewWidget()
        self.preview.setAcceptDrops(True)
        self.preview.dragEnterEvent = self.dragEnterEvent
        self.preview.dropEvent = self.dropEvent
        layout.addWidget(self.preview)

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("请输入水印文字")
        layout.addWidget(self.text_input)

        btn_import = QPushButton("导入图片")
        btn_import.clicked.connect(self.import_image)
        layout.addWidget(btn_import)

        btn_export = QPushButton("导出图片")
        btn_export.clicked.connect(self.export_image)
        layout.addWidget(btn_export)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        # 当前图片路径
        self.current_image_path = None

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for f in files:
            if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                img = self.image_loader.load_image(f)
                if img is not None:
                    self.current_image_path = f
                    self.preview.set_image(img)
                    self.status_label.setText(f"已加载：{f}")

    def import_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择图片", "", "Images (*.png *.jpg *.jpeg)")
        if not path:
            return
        img = self.image_loader.load_image(path)
        if img is None:
            QMessageBox.warning(self, "错误", "无法加载图片")
            return
        self.current_image_path = path
        self.preview.set_image(img)
        self.status_label.setText(f"已加载：{path}")

    def export_image(self):
        if not self.current_image_path:
            QMessageBox.warning(self, "错误", "请先导入图片")
            return
        text = self.text_input.text()
        if not text:
            QMessageBox.warning(self, "错误", "请输入水印文字")
            return
        img = self.image_loader.load_image(self.current_image_path)
        watermarked = self.watermark_engine.add_text_watermark(img, text)
        save_path, _ = QFileDialog.getSaveFileName(self, "保存图片", "", "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg)")
        if not save_path:
            return
        ok = self.exporter.save_image(watermarked, save_path)
        if ok:
            self.status_label.setText(f"已导出：{save_path}")
        else:
            QMessageBox.warning(self, "错误", "保存失败")
