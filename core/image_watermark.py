from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox,
    QPushButton, QSlider, QColorDialog, QInputDialog, QMessageBox, QLineEdit
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import pyqtSignal, Qt
from core.template_manager import TemplateManager


class TextWatermarkSettings(QWidget):
    """
    文字水印设置面板（支持模板、九宫格位置、拖拽取消九宫格、保存/删除模板）
    发射：
      - settings_changed(dict)
      - position_changed(tuple)  # (x_ratio, y_ratio) 在 [0..1] 范围内，图片相对坐标
    """
    settings_changed = pyqtSignal(dict)
    position_changed = pyqtSignal(tuple)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.color = QColor("white")
        self.watermark_pos = (0.5, 0.5)  # 默认：中心（相对坐标）
        self.current_template_name = None
        self.template_manager = TemplateManager()
        self.selected_pos_btn = None

        self._build_ui()
        self.emit_settings()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(8)

        # 第一行：字体、字号、样式、颜色、透明度
        line1 = QHBoxLayout()
        line1.setSpacing(5)

        line1.addWidget(QLabel("字体:"))
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Arial", "Times New Roman", "SimHei", "SimSun", "Courier New"])
        self.font_combo.setCurrentText("Arial")
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
        self.text_input.setPlaceholderText("请输入水印文字")
        line2.addWidget(self.text_input)
        main_layout.addLayout(line2)

        # 第三行：九宫格 + 模板
        line3 = QHBoxLayout()
        line3.setSpacing(6)

        line3.addWidget(QLabel("位置:"))

        self.pos_buttons = {}
        self.standard_positions = {
            "左上": (0.0, 0.0),
            "右上": (1.0, 0.0),
            "左下": (0.0, 1.0),
            "右下": (1.0, 1.0),
            "中": (0.5, 0.5),
        }

        # ---------- 九宫格按钮创建 ----------
        for name, coord in self.standard_positions.items():
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setFixedSize(44, 28)
            btn.clicked.connect(lambda checked, b=btn, c=coord: self.on_grid_button_clicked(b, c))
            self.pos_buttons[name] = btn
            line3.addWidget(btn)

        line3.addSpacing(8)
        line3.addWidget(QLabel("模板:"))
        self.template_combo = QComboBox()
        self._refresh_template_combo()
        self.template_combo.currentTextChanged.connect(self.on_template_selected)
        line3.addWidget(self.template_combo)

        self.btn_save_template = QPushButton("保存模板")
        self.btn_save_template.clicked.connect(self.on_save_template_clicked)
        line3.addWidget(self.btn_save_template)

        self.btn_delete_template = QPushButton("删除模板")
        self.btn_delete_template.clicked.connect(self.on_delete_template_clicked)
        line3.addWidget(self.btn_delete_template)

        line3.addStretch()
        main_layout.addLayout(line3)

        # 信号绑定
        self.font_combo.currentTextChanged.connect(self.emit_settings)
        self.size_spin.valueChanged.connect(self.emit_settings)
        self.bold_btn.toggled.connect(self.emit_settings)
        self.italic_btn.toggled.connect(self.emit_settings)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        self.text_input.textChanged.connect(self.emit_settings)

    # ---------- UI 辅助 ----------
    def update_color_btn(self):
        self.color_btn.setStyleSheet(f"background-color: {self.color.name()}; border:1px solid gray; min-width:20px;")

    def select_color(self):
        col = QColorDialog.getColor(self.color, self, "选择文字颜色")
        if col.isValid():
            self.color = col
            self.update_color_btn()
            self.emit_settings()

    def _on_opacity_changed(self, val):
        self.opacity_label.setText(f"{val}%")
        self.emit_settings()

    # ---------- ✅ 九宫格逻辑修改 ----------
    def on_grid_button_clicked(self, btn, coord):
        """保证最多一个选中，并防止点击当前按钮后取消选中"""
        # 如果点的就是当前已选按钮，则不做任何切换（保持选中）
        if self.selected_pos_btn is btn:
            btn.setChecked(True)
            return

        # 否则清除其他选中，只保留当前
        for b in self.pos_buttons.values():
            b.setChecked(False)

        btn.setChecked(True)
        self.selected_pos_btn = btn
        self.watermark_pos = coord
        self._update_grid_styles()
        self.position_changed.emit(tuple(coord))

    def _update_grid_styles(self):
        """高亮当前选中按钮"""
        for b in self.pos_buttons.values():
            if b.isChecked():
                b.setStyleSheet("background-color: lightblue;")
            else:
                b.setStyleSheet("background-color: none;")

    def clear_grid_selection(self):
        for b in self.pos_buttons.values():
            b.setChecked(False)
        self.selected_pos_btn = None
        self._update_grid_styles()

    def on_drag_position(self, coord):
        """拖拽时清除九宫格状态"""
        self.watermark_pos = coord
        self.clear_grid_selection()
        self.position_changed.emit(tuple(coord))

    # ---------- 模板管理 ----------
    def _refresh_template_combo(self):
        self.template_combo.blockSignals(True)
        self.template_combo.clear()
        self.template_combo.addItem("不使用模板")
        for name in self.template_manager.list_templates():
            self.template_combo.addItem(name)
        self.template_combo.blockSignals(False)

    def on_template_selected(self, name):
        if name == "不使用模板":
            self.current_template_name = None
            self.clear_all_settings()
            return
        data = self.template_manager.get_template(name)
        if data:
            self.load_template(data)
            self.current_template_name = name

    # ---------- ✅ 导入模板匹配九宫格 ----------
    def load_template(self, data):
        """加载模板并匹配九宫格"""
        self.text_input.setText(data.get("text", ""))
        self.font_combo.setCurrentText(data.get("font_family", "Arial"))
        self.size_spin.setValue(data.get("font_size", 36))
        self.bold_btn.setChecked(data.get("bold", False))
        self.italic_btn.setChecked(data.get("italic", False))

        color = data.get("color", (255, 255, 255, 255))
        try:
            self.color = QColor(color[0], color[1], color[2])
        except Exception:
            self.color = QColor("white")
        self.update_color_btn()

        self.opacity_slider.setValue(int(data.get("opacity", 1.0) * 100))

        pos = tuple(data.get("position", (0.5, 0.5)))
        self.watermark_pos = pos

        # 清空选中并匹配九宫格位置
        self.clear_grid_selection()
        matched_btn = None
        for name, coord in self.standard_positions.items():
            if abs(coord[0] - pos[0]) < 1e-6 and abs(coord[1] - pos[1]) < 1e-6:
                matched_btn = self.pos_buttons[name]
                matched_btn.setChecked(True)
                self.selected_pos_btn = matched_btn
                break

        self._update_grid_styles()
        self.emit_settings()

    def clear_all_settings(self):
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
                int(255 * (self.opacity_slider.value() / 100.0))
            ),
            "opacity": self.opacity_slider.value() / 100.0,
        }

    def emit_settings(self):
        self.settings_changed.emit(self.get_settings())
