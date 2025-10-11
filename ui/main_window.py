from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QFileDialog, QLabel,
    QMessageBox, QComboBox, QProgressBar, QSplitter,
    QListWidget, QListWidgetItem
)
from PyQt6.QtGui import QPixmap, QIcon, QColor
from PyQt6.QtCore import Qt, QSize
from ui.preview_widget import PreviewWidget
from ui.text_watermark_settings import TextWatermarkSettings
from ui.template_dialog import TemplateDialog
from core.image_loader import ImageLoader
from core.watermark_engine import WatermarkEngine
from core.exporter import Exporter
from core.template_manager import TemplateManager
import os


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图片水印工具")
        self.setMinimumSize(900, 600)

        # ---------------- 核心模块 ----------------
        self.image_loader = ImageLoader()
        self.watermark_engine = WatermarkEngine()
        self.template_manager = TemplateManager()
        self.exporter = Exporter()

        # ---------------- 当前状态 ----------------
        self.image_paths = []
        self.current_image_path = None

        # ---------------- 中央控件布局 ----------------
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # 上部：左缩略图 + 右预览
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setFixedHeight(400)
        main_layout.addWidget(splitter)

        # 左侧缩略图列表
        self.thumbnail_list = QListWidget()
        self.thumbnail_list.setIconSize(QSize(100, 100))
        self.thumbnail_list.itemClicked.connect(self.on_thumbnail_clicked)
        splitter.addWidget(self.thumbnail_list)

        # 右侧预览
        self.preview = PreviewWidget()
        splitter.addWidget(self.preview)
        splitter.setStretchFactor(1, 1)

        # 下部：水印设置、模板、导出
        bottom_layout = QVBoxLayout()
        main_layout.addLayout(bottom_layout)

        # 文字水印设置面板
        self.text_settings = TextWatermarkSettings()
        self.text_settings.settings_changed.connect(lambda s: self.update_text_preview(s))
        bottom_layout.addWidget(self.text_settings)

        # 模板区
        template_layout = QHBoxLayout()
        template_layout.addWidget(QLabel("选择模板:"))
        self.template_combo = QComboBox()
        self.update_template_list()
        template_layout.addWidget(self.template_combo)

        btn_new_template = QPushButton("新建模板")
        btn_new_template.clicked.connect(self.create_template)
        btn_edit_template = QPushButton("编辑模板")
        btn_edit_template.clicked.connect(self.edit_template)
        btn_delete_template = QPushButton("删除模板")
        btn_delete_template.clicked.connect(self.delete_template)

        template_layout.addWidget(btn_new_template)
        template_layout.addWidget(btn_edit_template)
        template_layout.addWidget(btn_delete_template)
        bottom_layout.addLayout(template_layout)

        # 导出区
        export_layout = QHBoxLayout()
        export_layout.addWidget(QLabel("前缀:"))
        self.prefix_input = QLineEdit("wm_")
        export_layout.addWidget(self.prefix_input)
        export_layout.addWidget(QLabel("后缀:"))
        self.suffix_input = QLineEdit("_watermarked")
        export_layout.addWidget(self.suffix_input)
        export_layout.addWidget(QLabel("输出格式:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "JPEG"])
        export_layout.addWidget(self.format_combo)

        btn_import_files = QPushButton("导入图片")
        btn_import_files.clicked.connect(self.import_images)
        btn_import_folder = QPushButton("导入文件夹")
        btn_import_folder.clicked.connect(self.import_folder)
        self.btn_export = QPushButton("导出所有图片")
        self.btn_export.clicked.connect(self.export_all_images)

        export_layout.addWidget(btn_import_files)
        export_layout.addWidget(btn_import_folder)
        export_layout.addWidget(self.btn_export)
        bottom_layout.addLayout(export_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        bottom_layout.addWidget(self.progress_bar)

        # 状态栏
        self.status_label = QLabel("")
        main_layout.addWidget(self.status_label)

    # ---------------- 工具函数 ----------------
    def qcolor_to_rgba(self, color, opacity=1.0):
        """统一转换为 RGBA"""
        if isinstance(color, QColor):
            return (color.red(), color.green(), color.blue(), int(255 * opacity))
        elif isinstance(color, tuple):
            if len(color) == 3:
                return (color[0], color[1], color[2], int(255 * opacity))
            elif len(color) == 4:
                return (color[0], color[1], color[2], int(255 * opacity))
        return (255, 255, 255, int(255 * opacity))

    # ---------------- 图片导入 ----------------
    def import_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择图片", "", "Images (*.png *.jpg *.jpeg *.bmp *.tiff)"
        )
        if files:
            self.add_images(files)

    def import_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if not folder:
            return
        files = []
        for root, _, filenames in os.walk(folder):
            for f in filenames:
                if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff")):
                    files.append(os.path.join(root, f))
        if files:
            self.add_images(files)

    def add_images(self, files):
        for path in files:
            if path in self.image_paths or not os.path.exists(path):
                continue
            self.image_paths.append(path)
            item = QListWidgetItem(os.path.basename(path))
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    100,
                    100,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                item.setIcon(QIcon(pixmap))
            item.setData(Qt.ItemDataRole.UserRole, path)
            self.thumbnail_list.addItem(item)

        if self.image_paths and not self.current_image_path:
            self.current_image_path = self.image_paths[0]
            self.update_text_preview(self.text_settings.get_settings())
        self.status_label.setText(f"已加载 {len(self.image_paths)} 张图片")

    # ---------------- 缩略图点击 ----------------
    def on_thumbnail_clicked(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.current_image_path = path
            # 自动刷新水印预览
            self.update_text_preview(self.text_settings.get_settings())
            self.status_label.setText(f"预览：{os.path.basename(path)}")


    # ---------------- 实时水印预览 ----------------
    def update_text_preview(self, settings):
        if not self.current_image_path:
            return
        img = self.image_loader.load_image(self.current_image_path)
        if not img:
            return

        # 从 UI 获取文字
        text = settings.get("text", "")
        if not text:
            self.preview.set_image(img)
            return

        # 转换颜色为 RGBA
        settings["color"] = self.qcolor_to_rgba(settings.get("color"), settings.get("opacity", 1.0))

        watermarked = self.watermark_engine.add_text_watermark(img, text, settings=settings)
        if watermarked:
            self.preview.set_image(watermarked)

    # ---------------- 生成预览按钮 ----------------
    def generate_preview(self):
        """点击生成预览按钮时刷新当前图片水印效果"""
        self.update_text_preview(self.text_settings.get_settings())

    # ---------------- 模板管理 ----------------
    def update_template_list(self):
        self.template_combo.clear()
        self.template_combo.addItem("不使用模板")
        templates = self.template_manager.list_templates()
        self.template_combo.addItems(templates)

    def create_template(self):
        dialog = TemplateDialog(self)
        if dialog.exec():
            data = dialog.get_template_data()
            if self.template_manager.save_template(data["name"], data):
                self.update_template_list()
                self.status_label.setText(f"已创建模板：{data['name']}")
            else:
                QMessageBox.warning(self, "错误", "保存模板失败")

    def edit_template(self):
        name = self.template_combo.currentText()
        if name == "不使用模板":
            return
        data = self.template_manager.get_template(name)
        if data:
            dialog = TemplateDialog(self, data)
            if dialog.exec():
                new_data = dialog.get_template_data()
                if self.template_manager.save_template(name, new_data):
                    self.update_template_list()
                    self.status_label.setText(f"已更新模板：{name}")
                else:
                    QMessageBox.warning(self, "错误", "更新模板失败")

    def delete_template(self):
        name = self.template_combo.currentText()
        if name == "不使用模板":
            return
        if QMessageBox.question(self, "确认", f"确定要删除模板 {name} 吗？") == QMessageBox.StandardButton.Yes:
            if self.template_manager.delete_template(name):
                self.update_template_list()
                self.status_label.setText(f"已删除模板：{name}")
            else:
                QMessageBox.warning(self, "错误", "删除模板失败")

    # ---------------- 批量导出 ----------------
    def export_all_images(self):
        if not self.image_paths:
            QMessageBox.warning(self, "错误", "请先导入图片")
            return

        folder = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if not folder:
            return

        # 防止覆盖源目录
        orig_folders = set(os.path.dirname(p) for p in self.image_paths)
        if folder in orig_folders:
            QMessageBox.warning(self, "错误", "输出文件夹不能与原图片所在文件夹相同")
            return

        prefix = self.prefix_input.text()
        suffix = self.suffix_input.text()
        settings = self.text_settings.get_settings()
        settings["color"] = self.qcolor_to_rgba(settings.get("color"), settings.get("opacity", 1.0))
        text = settings.get("text", "")
        if not text:
            QMessageBox.warning(self, "错误", "请先设置水印文字")
            return

        fmt = self.format_combo.currentText()
        self.progress_bar.setMaximum(len(self.image_paths))
        self.progress_bar.setValue(0)

        for i, path in enumerate(self.image_paths, start=1):
            img = self.image_loader.load_image(path)
            if img is None:
                continue
            watermarked = self.watermark_engine.add_text_watermark(img, text, settings=settings)
            name = os.path.splitext(os.path.basename(path))[0]
            ext = ".png" if fmt == "PNG" else ".jpg"
            if ext == ".jpg" and watermarked.mode == "RGBA":
                watermarked = watermarked.convert("RGB")
            new_name = f"{prefix}{name}{suffix}{ext}"
            save_path = os.path.join(folder, new_name)
            if not self.exporter.save_image(watermarked, save_path):
                QMessageBox.warning(self, "错误", f"保存图片失败: {save_path}")
            self.progress_bar.setValue(i)

        QMessageBox.information(self, "完成", f"已导出 {len(self.image_paths)} 张图片")
        self.progress_bar.setValue(0)
