"""
主窗口模块，负责UI布局、用户交互和信号处理。
依赖：ui.preview_widget, ui.template_dialog, core 模块
"""
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLineEdit, QFileDialog, QLabel,
                             QMessageBox, QComboBox, QTabWidget, QListWidget,
                             QListWidgetItem, QSplitter, QProgressBar)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt, QSize
from ui.preview_widget import PreviewWidget
from ui.template_dialog import TemplateDialog
from core.image_loader import ImageLoader
from core.watermark_engine import WatermarkEngine
from core.image_watermark import ImageWatermark
from core.template_manager import TemplateManager
from core.exporter import Exporter
import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图片水印工具")
        self.setMinimumSize(900, 600)

        # 核心模块
        self.image_loader = ImageLoader()
        self.watermark_engine = WatermarkEngine()
        self.image_watermark = ImageWatermark()
        self.template_manager = TemplateManager()
        self.exporter = Exporter()

        # 当前状态
        self.image_paths = []           # 所有导入图片路径
        self.current_image_path = None
        self.watermark_image_path = None

        # 中央控件
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # 选项卡
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)

        # ---------------- 文字水印 ----------------
        text_tab = QWidget()
        text_layout = QVBoxLayout(text_tab)

        # 分割布局：左缩略图 + 右预览
        splitter = QSplitter(Qt.Orientation.Horizontal)
        text_layout.addWidget(splitter)

        # 左缩略图列表
        self.thumbnail_list = QListWidget()
        self.thumbnail_list.setIconSize(QSize(100, 100))
        self.thumbnail_list.itemClicked.connect(self.on_thumbnail_clicked)
        splitter.addWidget(self.thumbnail_list)

        # 右侧预览
        self.preview = PreviewWidget()
        self.preview.setAcceptDrops(True)
        self.preview.dragEnterEvent = self.dragEnterEvent
        self.preview.dropEvent = self.dropEvent
        splitter.addWidget(self.preview)
        splitter.setStretchFactor(1, 1)

        # 模板选择
        template_layout = QHBoxLayout()
        template_layout.addWidget(QLabel("选择模板:"))
        self.template_combo = QComboBox()
        self.update_template_list()
        template_layout.addWidget(self.template_combo)

        template_btns = QHBoxLayout()
        btn_new_template = QPushButton("新建模板")
        btn_new_template.clicked.connect(self.create_template)
        btn_edit_template = QPushButton("编辑模板")
        btn_edit_template.clicked.connect(self.edit_template)
        btn_delete_template = QPushButton("删除模板")
        btn_delete_template.clicked.connect(self.delete_template)
        template_btns.addWidget(btn_new_template)
        template_btns.addWidget(btn_edit_template)
        template_btns.addWidget(btn_delete_template)

        text_layout.addLayout(template_layout)
        text_layout.addLayout(template_btns)

        # 水印文字输入
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("请输入水印文字")
        text_layout.addWidget(self.text_input)

        # 前缀/后缀命名规则
        naming_layout = QHBoxLayout()
        naming_layout.addWidget(QLabel("前缀:"))
        self.prefix_input = QLineEdit("wm_")
        naming_layout.addWidget(self.prefix_input)
        naming_layout.addWidget(QLabel("后缀:"))
        self.suffix_input = QLineEdit("_watermarked")
        naming_layout.addWidget(self.suffix_input)
        naming_layout.addWidget(QLabel("输出格式:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "JPEG"])
        naming_layout.addWidget(self.format_combo)
        text_layout.addLayout(naming_layout)

        # 导入/导出按钮
        text_btns = QHBoxLayout()
        btn_import_files = QPushButton("导入图片")
        btn_import_files.clicked.connect(self.import_images)
        btn_import_folder = QPushButton("导入文件夹")
        btn_import_folder.clicked.connect(self.import_folder)
        self.btn_export = QPushButton("导出所有图片")
        self.btn_export.clicked.connect(self.export_all_images)
        text_btns.addWidget(btn_import_files)
        text_btns.addWidget(btn_import_folder)
        text_btns.addWidget(self.btn_export)
        text_layout.addLayout(text_btns)

        # 批量导出进度条
        self.progress_bar = QProgressBar()
        text_layout.addWidget(self.progress_bar)

        tab_widget.addTab(text_tab, "文字水印")

        # ---------------- 图片水印 ----------------
        image_tab = QWidget()
        image_layout = QVBoxLayout(image_tab)

        self.watermark_preview = PreviewWidget()
        image_layout.addWidget(self.watermark_preview)

        watermark_settings = QHBoxLayout()
        watermark_settings.addWidget(QLabel("不透明度:"))
        self.opacity_input = QLineEdit("0.5")
        watermark_settings.addWidget(self.opacity_input)

        self.position_combo = QComboBox()
        self.position_combo.addItems(['右下角', '右上角', '左下角', '左上角', '居中'])
        watermark_settings.addWidget(self.position_combo)
        image_layout.addLayout(watermark_settings)

        image_btns = QHBoxLayout()
        btn_import_watermark = QPushButton("导入水印图片")
        btn_import_watermark.clicked.connect(self.import_watermark_image)
        btn_apply_watermark = QPushButton("应用水印")
        btn_apply_watermark.clicked.connect(self.apply_image_watermark)
        image_btns.addWidget(btn_import_watermark)
        image_btns.addWidget(btn_apply_watermark)
        image_layout.addLayout(image_btns)

        tab_widget.addTab(image_tab, "图片水印")

        # 状态栏
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

    # ------------------- 拖拽 -------------------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        image_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff'))]
        if not image_files:
            return
        self.add_images(image_files)

    # ------------------- 导入图片 -------------------
    def import_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择图片", "", "Images (*.png *.jpg *.jpeg *.bmp *.tiff)")
        if files:
            self.add_images(files)

    def import_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if not folder:
            return
        files = []
        for root, _, filenames in os.walk(folder):
            for f in filenames:
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                    files.append(os.path.join(root, f))
        if files:
            self.add_images(files)

    def add_images(self, files):
        for path in files:
            if path in self.image_paths:
                continue
            if not os.path.exists(path):
                continue
            self.image_paths.append(path)
            item = QListWidgetItem(os.path.basename(path))
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)
                item.setIcon(QIcon(pixmap))
            item.setData(Qt.ItemDataRole.UserRole, path)
            self.thumbnail_list.addItem(item)

        # 默认预览第一张图片
        if self.image_paths and not self.current_image_path:
            self.current_image_path = self.image_paths[0]
            img = self.image_loader.load_image(self.current_image_path)
            if img:
                self.preview.set_image(img)
        self.status_label.setText(f"已加载 {len(self.image_paths)} 张图片")

    # ------------------- 缩略图点击 -------------------
    def on_thumbnail_clicked(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        img = self.image_loader.load_image(path)
        if img:
            self.current_image_path = path
            self.preview.set_image(img)
            self.status_label.setText(f"预览：{os.path.basename(path)}")

    # ------------------- 模板 -------------------
    def update_template_list(self):
        self.template_combo.clear()
        self.template_combo.addItem("不使用模板")
        templates = self.template_manager.list_templates()
        self.template_combo.addItems(templates)

    def create_template(self):
        dialog = TemplateDialog(self)
        if dialog.exec():
            template_data = dialog.get_template_data()
            if self.template_manager.save_template(template_data['name'], template_data):
                self.update_template_list()
                self.status_label.setText(f"已创建模板：{template_data['name']}")
            else:
                QMessageBox.warning(self, "错误", "保存模板失败")

    def edit_template(self):
        template_name = self.template_combo.currentText()
        if template_name == "不使用模板":
            return
        template_data = self.template_manager.get_template(template_name)
        if template_data:
            dialog = TemplateDialog(self, template_data)
            if dialog.exec():
                new_data = dialog.get_template_data()
                if self.template_manager.save_template(template_name, new_data):
                    self.update_template_list()
                    self.status_label.setText(f"已更新模板：{template_name}")
                else:
                    QMessageBox.warning(self, "错误", "更新模板失败")

    def delete_template(self):
        template_name = self.template_combo.currentText()
        if template_name == "不使用模板":
            return
        if QMessageBox.question(self, "确认", f"确定要删除模板 {template_name} 吗？") == QMessageBox.StandardButton.Yes:
            if self.template_manager.delete_template(template_name):
                self.update_template_list()
                self.status_label.setText(f"已删除模板：{template_name}")
            else:
                QMessageBox.warning(self, "错误", "删除模板失败")

    # ------------------- 图片水印 -------------------
    def import_watermark_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择水印图片", "", "Images (*.png *.jpg *.jpeg *.bmp *.tiff)")
        if not path:
            return
        img = self.image_loader.load_image(path)
        if img:
            self.watermark_image_path = path
            self.watermark_preview.set_image(img)
            self.status_label.setText(f"已加载水印图片：{os.path.basename(path)}")

    def apply_image_watermark(self):
        if not self.current_image_path or not self.watermark_image_path:
            QMessageBox.warning(self, "错误", "请先导入基础图片和水印图片")
            return

        try:
            opacity = float(self.opacity_input.text())
            if not 0 <= opacity <= 1:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "错误", "不透明度必须是0-1之间的数值")
            return

        position_map = {
            '右下角': 'bottom-right',
            '右上角': 'top-right',
            '左下角': 'bottom-left',
            '左上角': 'top-left',
            '居中': 'center'
        }
        position = position_map[self.position_combo.currentText()]

        base_img = self.image_loader.load_image(self.current_image_path)
        watermark_img = self.image_loader.load_image(self.watermark_image_path)
        result = self.image_watermark.add_image_watermark(
            base_img, watermark_img, position, opacity
        )

        if result:
            save_path, _ = QFileDialog.getSaveFileName(
                self, "保存图片", "", "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg)")
            if save_path:
                if result.mode == "RGBA" and save_path.lower().endswith((".jpg", ".jpeg")):
                    result = result.convert("RGB")
                if self.exporter.save_image(result, save_path):
                    self.status_label.setText(f"已导出：{save_path}")
                else:
                    QMessageBox.warning(self, "错误", "保存失败")
        else:
            QMessageBox.warning(self, "错误", "添加水印失败")

    # ------------------- 批量导出文字水印 -------------------
    def export_all_images(self):
        if not self.image_paths:
            QMessageBox.warning(self, "错误", "请先导入图片")
            return

        folder = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if not folder:
            return

        orig_folders = set(os.path.dirname(p) for p in self.image_paths)
        if folder in orig_folders:
            QMessageBox.warning(self, "错误", "输出文件夹不能与原图片所在文件夹相同")
            return

        prefix = self.prefix_input.text()
        suffix = self.suffix_input.text()
        text = self.text_input.text()
        output_format = self.format_combo.currentText()  # PNG 或 JPEG

        self.progress_bar.setMaximum(len(self.image_paths))
        self.progress_bar.setValue(0)

        for i, path in enumerate(self.image_paths, start=1):
            img = self.image_loader.load_image(path)
            if img is None:
                continue

            watermarked = self.watermark_engine.add_text_watermark(img, text)

            name = os.path.splitext(os.path.basename(path))[0]
            ext = ".png" if output_format == "PNG" else ".jpg"
            if ext == ".jpg" and watermarked.mode == "RGBA":
                watermarked = watermarked.convert("RGB")
            new_name = f"{prefix}{name}{suffix}{ext}"
            save_path = os.path.join(folder, new_name)
            if not self.exporter.save_image(watermarked, save_path):
                QMessageBox.warning(self, "错误", f"保存图片失败: {save_path}")

            self.progress_bar.setValue(i)

        QMessageBox.information(self, "完成", f"已导出 {len(self.image_paths)} 张图片")
        self.progress_bar.setValue(0)
