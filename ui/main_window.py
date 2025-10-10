"""
主窗口模块，负责UI布局、用户交互和信号处理。
依赖：ui.preview_widget, ui.template_dialog, core 模块
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLineEdit, QFileDialog, QLabel, 
    QMessageBox, QComboBox, QTabWidget, QListWidget, QListWidgetItem, QSplitter
)
from PyQt6.QtCore import Qt
from PyQt6 import QtCore
from PyQt6.QtGui import QPixmap, QIcon
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
        self.setMinimumSize(800, 600)

        # 控制器/核心模块
        self.image_loader = ImageLoader()
        self.watermark_engine = WatermarkEngine()
        self.image_watermark = ImageWatermark()
        self.template_manager = TemplateManager()
        self.exporter = Exporter()

        # UI 组件
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # 创建选项卡
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)

        # === 文字水印选项卡 ===
        text_tab = QWidget()
        text_layout = QVBoxLayout(text_tab)
        
        # === 新增：左右分割布局（缩略图 + 预览） ===
        splitter = QSplitter(Qt.Orientation.Horizontal)
        text_layout.addWidget(splitter)

        # 左侧缩略图列表
        self.thumbnail_list = QListWidget()
        self.thumbnail_list.setIconSize(QtCore.QSize(100, 100))
        self.thumbnail_list.itemClicked.connect(self.on_thumbnail_clicked)
        splitter.addWidget(self.thumbnail_list)

        # 右侧预览区
        self.preview = PreviewWidget()
        self.preview.setAcceptDrops(True)
        self.preview.dragEnterEvent = self.dragEnterEvent
        self.preview.dropEvent = self.dropEvent
        splitter.addWidget(self.preview)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        # 模板区
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

        # 文字输入
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("请输入水印文字")
        text_layout.addWidget(self.text_input)

        # 文字水印操作按钮
        text_btns = QHBoxLayout()
        btn_import = QPushButton("导入图片")
        btn_import.clicked.connect(self.import_image)
        btn_export = QPushButton("导出图片")
        btn_export.clicked.connect(self.export_image)
        text_btns.addWidget(btn_import)
        text_btns.addWidget(btn_export)
        text_layout.addLayout(text_btns)

        # === 图片水印选项卡 ===
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
        btn_export_watermark = QPushButton("应用水印")
        btn_export_watermark.clicked.connect(self.apply_image_watermark)
        image_btns.addWidget(btn_import_watermark)
        image_btns.addWidget(btn_export_watermark)
        image_layout.addLayout(image_btns)

        # 添加选项卡
        tab_widget.addTab(text_tab, "文字水印")
        tab_widget.addTab(image_tab, "图片水印")

        # 状态栏
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        # 当前状态
        self.current_image_path = None
        self.watermark_image_path = None

    # ========== 拖拽事件 ==========
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    # === 修改版：支持多图拖拽并显示缩略图 ===
    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        valid_files = [
            f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff'))
        ]
        if not valid_files:
            return

        self.thumbnail_list.clear()
        for path in valid_files:
            img = self.image_loader.load_image(path)
            if img is None:
                continue
            item = QListWidgetItem(os.path.basename(path))
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)
                item.setIcon(QIcon(pixmap))
            item.setData(Qt.ItemDataRole.UserRole, path)
            self.thumbnail_list.addItem(item)

        # 默认预览第一张
        first = valid_files[0]
        self.current_image_path = first
        img = self.image_loader.load_image(first)
        self.preview.set_image(img)
        self.status_label.setText(f"已加载 {len(valid_files)} 张图片（拖拽导入）")

    # ========== 导入多图 ==========
    def import_image(self):
        """支持多图和文件夹导入"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择图片", "", 
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff);;All Files (*)")
        
        # 如果未选择文件，则尝试选择文件夹
        if not files:
            folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
            if folder:
                for root, _, filenames in os.walk(folder):
                    for f in filenames:
                        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                            files.append(os.path.join(root, f))

        if not files:
            return

        self.thumbnail_list.clear()

        for path in files:
            if not os.path.exists(path):
                continue
            img = self.image_loader.load_image(path)
            if img is None:
                continue
            item = QListWidgetItem(os.path.basename(path))
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)
                item.setIcon(QIcon(pixmap))
            item.setData(Qt.ItemDataRole.UserRole, path)
            self.thumbnail_list.addItem(item)

        # === 新增：默认加载第一张到预览 ===
        first_img_path = files[0]
        first_img = self.image_loader.load_image(first_img_path)
        if first_img:
            self.current_image_path = first_img_path
            self.preview.set_image(first_img)
            self.status_label.setText(f"已加载 {len(files)} 张图片")

    # ========== 模板管理 ==========
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

    # ========== 水印导入与导出 ==========
    def import_watermark_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择水印图片", "", "Images (*.png *.jpg *.jpeg)"
        )
        if not path:
            return
        img = self.image_loader.load_image(path)
        if img is None:
            QMessageBox.warning(self, "错误", "无法加载图片")
            return
        self.watermark_image_path = path
        self.watermark_preview.set_image(img)
        self.status_label.setText(f"已加载水印图片：{path}")

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
            base_img, watermark_img, position, opacity)

        if result:
            save_path, _ = QFileDialog.getSaveFileName(
                self, "保存图片", "", "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg)")
            if save_path:
                if self.exporter.save_image(result, save_path):
                    self.status_label.setText(f"已导出：{save_path}")
                else:
                    QMessageBox.warning(self, "错误", "保存失败")
        else:
            QMessageBox.warning(self, "错误", "添加水印失败")

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

        if watermarked:
            save_path, _ = QFileDialog.getSaveFileName(
                self, "保存图片", "", "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg)")
            if save_path:
                if self.exporter.save_image(watermarked, save_path):
                    self.status_label.setText(f"已导出：{save_path}")
                else:
                    QMessageBox.warning(self, "错误", "保存失败")
        else:
            QMessageBox.warning(self, "错误", "添加水印失败")

    # ========== 缩略图点击 ==========
    def on_thumbnail_clicked(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        img = self.image_loader.load_image(path)
        if img:
            self.current_image_path = path
            self.preview.set_image(img)
            self.status_label.setText(f"预览：{os.path.basename(path)}")
