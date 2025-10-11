# ui/text_watermark_settings.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox,
    QPushButton, QSlider, QColorDialog, QInputDialog, QMessageBox, QLineEdit
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import pyqtSignal, Qt
from core.template_manager import TemplateManager
from functools import partial


class TextWatermarkSettings(QWidget):
    settings_changed = pyqtSignal(dict)
    position_changed = pyqtSignal(tuple)  # (x, y) 坐标

    def __init__(self, parent=None):
        super().__init__(parent)
        self.color = QColor("white")
        self.watermark_pos = (0.5, 0.5)  # 默认居中
        self.selected_pos_btn = None
        self.current_template_name = None
        self.template_manager = TemplateManager()

        self.init_ui()
        self.emit_settings()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(8)

        # 第一行：字体、字号、样式、颜色、透明度
        line1 = QHBoxLayout()
        line1.setSpacing(5)
        line1.addWidget(QLabel("字体:"))
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Arial", "Times New Roman", "SimHei", "SimSun", "Courier New"])
        line1.addWidget(self.font_combo)

        line1.addWidget(QLabel("字号:"))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(8, 120)
        self.size_spin.setValue(36)
        line1.addWidget(self.size_spin)

        line1.addWidget(QLabel("样式:"))
        self.bold_btn = QPushButton("B")
        self.bold_btn.setCheckable(True)
        self.bold_btn.setStyleSheet("font-weight:bold;width:25px;")
        self.italic_btn = QPushButton("I")
        self.italic_btn.setCheckable(True)
        self.italic_btn.setStyleSheet("font-style:italic;width:25px;")
        line1.addWidget(self.bold_btn)
        line1.addWidget(self.italic_btn)

        line1.addWidget(QLabel("颜色:"))
        self.color_btn = QPushButton()
        self.update_color_btn()
        self.color_btn.clicked.connect(self.select_color)
        line1.addWidget(self.color_btn)

        line1.addWidget(QLabel("透明度:"))
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.setFixedWidth(100)
        line1.addWidget(self.opacity_slider)
        self.opacity_label = QLabel("100%")
        line1.addWidget(self.opacity_label)
        main_layout.addLayout(line1)

        # 第二行：水印文字
        line2 = QHBoxLayout()
        line2.addWidget(QLabel("水印文字:"))
        self.text_input = QLineEdit()
        line2.addWidget(self.text_input)
        main_layout.addLayout(line2)

        # 第三行：九宫格按钮 + 模板选择 + 保存/删除模板
        line3 = QHBoxLayout()
        line3.setSpacing(2)
        line3.addWidget(QLabel("位置:"))

        self.pos_buttons = {}
        positions = [
            ("左上", (0.0, 0.0)),
            ("右上", (1.0, 0.0)),
            ("左下", (0.0, 1.0)),
            ("右下", (1.0, 1.0)),
            ("中", (0.5, 0.5)),
        ]
        for name, coord in positions:
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setFixedSize(40, 25)
            btn.clicked.connect(partial(self.set_position_by_grid, btn, coord))
            line3.addWidget(btn)
            self.pos_buttons[name] = btn

        # 模板下拉
        line3.addWidget(QLabel("模板:"))
        self.template_combo = QComboBox()
        self.update_template_list()
        self.template_combo.currentTextChanged.connect(self.on_template_selected)
        line3.addWidget(self.template_combo)

        # 保存/删除模板
        self.btn_save_template = QPushButton("保存模板")
        self.btn_save_template.clicked.connect(self.save_template)
        line3.addWidget(self.btn_save_template)
        self.btn_delete_template = QPushButton("删除模板")
        self.btn_delete_template.clicked.connect(self.delete_template)
        line3.addWidget(self.btn_delete_template)

        main_layout.addLayout(line3)

        # 信号绑定
        self.font_combo.currentTextChanged.connect(self.emit_settings)
        self.size_spin.valueChanged.connect(self.emit_settings)
        self.bold_btn.toggled.connect(self.emit_settings)
        self.italic_btn.toggled.connect(self.emit_settings)
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        self.text_input.textChanged.connect(self.emit_settings)

    # ---------------- 工具方法 ----------------
    def update_color_btn(self):
        self.color_btn.setStyleSheet(
            f"background-color: {self.color.name()}; border:1px solid gray;"
        )

    def select_color(self):
        color = QColorDialog.getColor(self.color, self)
        if color.isValid():
            self.color = color
            self.update_color_btn()
            self.emit_settings()

    def on_opacity_changed(self, value):
        self.opacity_label.setText(f"{value}%")
        self.emit_settings()

    # ---------------- 九宫格点击 ----------------
    def set_position_by_grid(self, btn, coord):
        # 清除其他按钮状态
        for b in self.pos_buttons.values():
            b.setChecked(False)
            b.setStyleSheet("")

        # 设置当前按钮为选中
        btn.setChecked(True)
        btn.setStyleSheet("background-color: #87CEFA; border: 1px solid #0078D7; color: black;")
        self.selected_pos_btn = btn
        self.watermark_pos = coord
        self.position_changed.emit(coord)
        self.emit_settings()

    def clear_grid_selection(self):
        for btn in self.pos_buttons.values():
            btn.setChecked(False)
            btn.setStyleSheet("")
        self.selected_pos_btn = None

    # ---------------- 拖拽水印 ----------------
    def on_drag_position(self, coord):
        """接收 PreviewWidget 拖拽后位置"""
        self.watermark_pos = coord
        self.clear_grid_selection()  # 清除九宫格按钮选中
        self.position_changed.emit(coord)
        self.emit_settings()

    # ---------------- 设置/获取水印 ----------------
    def get_settings(self):
        return {
            "text": self.text_input.text(),
            "font_family": self.font_combo.currentText(),
            "font_size": self.size_spin.value(),
            "bold": self.bold_btn.isChecked(),
            "italic": self.italic_btn.isChecked(),
            "color": (
                self.color.red(),
                self.color.green(),
                self.color.blue(),
                int(255 * (self.opacity_slider.value() / 100)),
            ),
            "opacity": self.opacity_slider.value() / 100.0,
            "position": self.watermark_pos,  # 保证保存最新拖拽位置
        }

    def emit_settings(self):
        self.settings_changed.emit(self.get_settings())

    # ---------------- 模板相关 ----------------
    def update_template_list(self):
        self.template_combo.blockSignals(True)
        self.template_combo.clear()
        self.template_combo.addItem("不使用模板")
        for name in self.template_manager.list_templates():
            self.template_combo.addItem(name)
        self.template_combo.blockSignals(False)

    def on_template_selected(self, name):
        if name == "不使用模板":
            self.current_template_name = None
            self.clear_settings()
            return
        data = self.template_manager.get_template(name)
        if data:
            self.load_template(data)
            self.current_template_name = name

    def save_template(self):
        settings = self.get_settings()
        if not settings.get("text"):
            QMessageBox.warning(self, "错误", "请先设置水印文字")
            return

        current_name = self.current_template_name or ""
        name, ok = QInputDialog.getText(self, "保存模板", "请输入模板名称:", text=current_name)
        if not ok or not name.strip():
            return
        name = name.strip()

        template_data = {
            "text": settings["text"],
            "font_family": settings["font_family"],
            "font_size": settings["font_size"],
            "bold": settings.get("bold", False),
            "italic": settings.get("italic", False),
            "color": (
                self.color.red(),
                self.color.green(),
                self.color.blue(),
                int(255 * settings["opacity"]),
            ),
            "opacity": settings["opacity"],
            "position": self.watermark_pos,  # 保存拖拽位置
        }
        if self.template_manager.save_template(name, template_data):
            self.update_template_list()
            self.template_combo.setCurrentText(name)
            self.current_template_name = name
        else:
            QMessageBox.warning(self, "错误", "保存模板失败")

    def delete_template(self):
        name = self.template_combo.currentText()
        if name == "不使用模板":
            return
        if QMessageBox.question(self, "确认", f"确定要删除模板 {name} 吗？") == QMessageBox.StandardButton.Yes:
            if self.template_manager.delete_template(name):
                self.update_template_list()
                self.current_template_name = None
            else:
                QMessageBox.warning(self, "错误", "删除模板失败")

    def load_template(self, data):
        self.text_input.setText(data.get("text", ""))
        self.font_combo.setCurrentText(data.get("font_family", "Arial"))
        self.size_spin.setValue(data.get("font_size", 36))
        self.bold_btn.setChecked(data.get("bold", False))
        self.italic_btn.setChecked(data.get("italic", False))
        color = data.get("color", (255, 255, 255, 255))
        self.color = QColor(color[0], color[1], color[2])
        self.update_color_btn()
        self.opacity_slider.setValue(int(data.get("opacity", 1.0) * 100))

        # --- 位置处理 ---
        pos = data.get("position", (0.5, 0.5))
        self.watermark_pos = pos
        self.clear_grid_selection()

        # 匹配九宫格标准点，允许微小误差
        matched = False
        for name, coord in [
            ("左上", (0.0, 0.0)),
            ("右上", (1.0, 0.0)),
            ("左下", (0.0, 1.0)),
            ("右下", (1.0, 1.0)),
            ("中", (0.5, 0.5))
        ]:
            if abs(coord[0] - pos[0]) < 1e-6 and abs(coord[1] - pos[1]) < 1e-6:
                btn = self.pos_buttons[name]
                btn.setChecked(True)
                btn.setStyleSheet("background-color: #1976d2; color: white; border: 1px solid #004c99;")
                self.selected_pos_btn = btn
                matched = True
                break

        if not matched:
            self.selected_pos_btn = None

        self.emit_settings()

    def clear_settings(self):
        self.text_input.clear()
        self.font_combo.setCurrentText("Arial")
        self.size_spin.setValue(36)
        self.bold_btn.setChecked(False)
        self.italic_btn.setChecked(False)
        self.color = QColor("white")
        self.update_color_btn()
        self.opacity_slider.setValue(100)
        self.watermark_pos = (0.5, 0.5)
        self.clear_grid_selection()
        self.emit_settings()
