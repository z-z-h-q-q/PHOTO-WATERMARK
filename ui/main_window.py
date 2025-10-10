"""
主窗口模块，负责UI布局、用户交互和信号处理。
增强功能：
1. 支持多文件或文件夹导入；
2. 自动扫描文件夹内图片；
3. 缩略图支持追加显示；
4. 拖拽导入提示；
5. 点击缩略图切换预览。
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QFileDialog, QLabel, QMessageBox, QComboBox, QTabWidget, QListWidget,
    QListWidgetItem, QSplitter
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QIcon, QPainter, QColor

import os

# === 引入核心模块 ===
from ui.preview_widget import PreviewWidget
from ui.template_dialog import TemplateDialog
from core.image_loader import ImageLoader
from core.watermark_engine import WatermarkEngine
from core.image_watermark import ImageWatermark
from core.template_manager import TemplateManager
from core.exporter import Exporter


class HintPreviewWidget(PreviewWidget):
    """带文字提示的预览组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hint_text = "拖拽图片到此处或点击『导入图片』按钮"
        self.image = None

    def set_image(self, image):
        self.image = image
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.image:
            super().paintEvent(event)
        else:
            painter.setPen(QColor("#888"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.hint_text)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图片水印工具")
        self.setMinimumSize(900, 600)

        # 控制器模块
        self.image_loader = ImageLoader()
        self.watermark_engine = WatermarkEngine()
        self.image_watermark = ImageWatermark()
        self.template_manager = TemplateManager()
        self.exporter = Exporter()

        # === 主体布局 ===
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)

        # === 文字水印选项卡 ===
        text_tab = QWidget()
        text_layout = QVBoxLayout(text_tab)

        # 左右分割布局
        splitter = QSplitter(Qt.Orientation.Horizontal)
        text_layout.addWidget(splitter)

        # 左侧缩略图列表
        self.thumbnail_list = QListWidget()
        self.thumbnail_list.setIconSize(QSize(100, 100))
        self.thumbnail_list.itemClicked.connect(self.on_thumbnail_clicked)
        splitter.addWidget(self.thumbnail_list)

        # 右侧预览区
        self.preview = HintPreviewWidget()
        self.preview.setAcceptDrops(True)
        self.preview.dragEnterEvent = self.dragEnterEvent
        self.preview.dropEvent = self.dropEvent
        splitter.addWidget(self.preview)
        splitter.setStretchFactor(1, 1)

        # 模板选择区
        template_layout = QHBoxLayout()
        template_layout.addWidget(QLabel("选择模板:"))
        self.template_combo = QComboBox()
        self.update_template_list()
        template_layout.addWidget(self.template_combo)
        text_layout.addLayout(template_layout)

        # 模板管理按钮
        btn_layout = QHBoxLayout()
        for text, handler in [
            ("新建模板", self.create_template),
            ("编辑模板", self.edit_template),
            ("删除模板", self.delete_template)
        ]:
            btn = QPushButton(text)
            btn.clicked.connect(handler)
            btn_layout.addWidget(btn)
        text_layout.addLayout(btn_layout)

        # 文字输入与按钮
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("请输入水印文字")
        text_layout.addWidget(self.text_input)

        btn_import = QPushButton("导入图片")
        btn_import.clicked.connect(self.import_image)
        btn_export = QPushButton("导出图片")
        btn_export.clicked.connect(self.export_image)

        op_layout = QHBoxLayout()
        op_layout.addWidget(btn_import)
        op_layout.addWidget(btn_export)
        text_layout.addLayout(op_layout)

        tab_widget.addTab(text_tab, "文字水印")

        # === 图片水印选项卡 ===
        image_tab = QWidget()
        image_layout = QVBoxLayout(image_tab)

        self.watermark_preview = PreviewWidget()
        image_layout.addWidget(self.watermark_preview)

        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("不透明度:"))
        self.opacity_input = QLineEdit("0.5")
        opacity_layout.addWidget(self.opacity_input)

        self.position_combo = QComboBox()
        self.position_combo.addItems(['右下角', '右上角', '左下角', '左上角', '居中'])
        opacity_layout.addWidget(self.position_combo)
        image_layout.addLayout(opacity_layout)

        btn_import_wm = QPushButton("导入水印图片")
        btn_import_wm.clicked.connect(self.import_watermark_image)
        btn_apply_wm = QPushButton("应用水印")
        btn_apply_wm.clicked.connect(self.apply_image_watermark)

        img_btns = QHBoxLayout()
        img_btns.addWidget(btn_import_wm)
        img_btns.addWidget(btn_apply_wm)
        image_layout.addLayout(img_btns)

        tab_widget.addTab(image_tab, "图片水印")

        # 状态栏
        self.status_label = QLabel("就绪")
        layout.addWidget(self.status_label)

        # 状态
        self.current_image_path = None
        self.watermark_image_path = None

    # -------------------- 拖拽支持 -------------------- #
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        valid_files = [
            f for f in files
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff'))
        ]
        if not valid_files:
            self.status_label.setText("未检测到有效图片文件")
            return
        self._add_images(valid_files)
        self.status_label.setText(f"拖入 {len(valid_files)} 张图片")

    # -------------------- 导入功能增强 -------------------- #
    def import_image(self):
        """支持多文件与文件夹导入"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择图片", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff);;All Files (*)"
        )

        if not files:
            folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
            if folder:
                for root, _, fnames in os.walk(folder):
                    for f in fnames:
                        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                            files.append(os.path.join(root, f))

        if not files:
            return

        self._add_images(files)
        self.status_label.setText(f"已加载 {len(files)} 张图片，共 {self.thumbnail_list.count()} 张")

    def _add_images(self, files):
        """内部方法：追加图片到缩略图列表"""
        for path in files:
            if not os.path.exists(path):
                continue
            # 防止重复
            if any(self.thumbnail_list.item(i).data(Qt.ItemDataRole.UserRole) == path
                   for i in range(self.thumbnail_list.count())):
                continue
            img = self.image_loader.load_image(path)
            if img is None:
                continue

            item = QListWidgetItem(os.path.basename(path))
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    100, 100, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                item.setIcon(QIcon(pixmap))
            item.setData(Qt.ItemDataRole.UserRole, path)
            self.thumbnail_list.addItem(item)

        # 初次导入默认显示第一张
        if self.current_image_path is None and self.thumbnail_list.count() > 0:
            first = self.thumbnail_list.item(0)
            self.on_thumbnail_clicked(first)

    # -------------------- 缩略图交互 -------------------- #
    def on_thumbnail_clicked(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        img = self.image_loader.load_image(path)
        if img:
            self.current_image_path = path
            self.preview.set_image(img)
            self.status_label.setText(f"预览：{os.path.basename(path)}")

    # -------------------- 模板逻辑 -------------------- #
    def update_template_list(self):
        self.template_combo.clear()
        self.template_combo.addItem("不使用模板")
        templates = self.template_manager.list_templates()
        self.template_combo.addItems(templates)

    def create_template(self):
        dialog = TemplateDialog(self)
        if dialog.exec():
            data = dialog.get_template_data()
            if self.template_manager.save_template(data['name'], data):
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

    # -------------------- 图片水印逻辑 -------------------- #
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
            QMessageBox.warning(self, "错误", "不透明度必须在 0~1 之间")
            return

        position_map = {
            '右下角': 'bottom-right',
            '右上角': 'top-right',
            '左下角': 'bottom-left',
            '左上角': 'top-left',
            '居中': 'center'
        }
        pos = position_map[self.position_combo.currentText()]
        base_img = self.image_loader.load_image(self.current_image_path)
        watermark_img = self.image_loader.load_image(self.watermark_image_path)
        result = self.image_watermark.add_image_watermark(base_img, watermark_img, pos, opacity)

        if result:
            save_path, _ = QFileDialog.getSaveFileName(
                self, "保存图片", "", "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg)"
            )
            if save_path and self.exporter.save_image(result, save_path):
                self.status_label.setText(f"已导出：{save_path}")
        else:
            QMessageBox.warning(self, "错误", "添加水印失败")

    # -------------------- 文字水印导出 -------------------- #
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
                self, "保存图片", "", "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg)"
            )
            if save_path and self.exporter.save_image(watermarked, save_path):
                self.status_label.setText(f"已导出：{save_path}")
        else:
            QMessageBox.warning(self, "错误", "添加水印失败")