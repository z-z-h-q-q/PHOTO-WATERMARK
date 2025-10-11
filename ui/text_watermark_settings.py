from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QComboBox, QSpinBox,
    QPushButton, QSlider, QColorDialog, QLineEdit
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import pyqtSignal, Qt


class TextWatermarkSettings(QWidget):
    """
    文字水印设置面板：
    - 实时发射 settings_changed(dict) 信号，供主窗口刷新预览。
    - 提供水印位置选择（四角+中间）。
    """
    settings_changed = pyqtSignal(dict)  # 水印属性变化
    position_changed = pyqtSignal(str)   # 水印位置按钮点击

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_settings = {}
        self.color = QColor("white")  # 默认颜色

        # ====== 主布局 ======
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(8)

        # ========== 第一行：字体、字号、样式、颜色、透明度 ==========
        line1 = QHBoxLayout()
        line1.setSpacing(5)

        # 字体选择
        line1.addWidget(QLabel("字体:"))
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Arial", "Times New Roman", "Courier New", "SimHei", "SimSun"])
        self.font_combo.setCurrentText("Arial")
        line1.addWidget(self.font_combo)

        # 字号
        line1.addWidget(QLabel("字号:"))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(8, 120)
        self.size_spin.setValue(36)
        line1.addWidget(self.size_spin)

        # 样式按钮
        line1.addWidget(QLabel("样式:"))
        self.bold_btn = QPushButton("B")
        self.bold_btn.setCheckable(True)
        self.bold_btn.setStyleSheet("font-weight: bold; width: 25px;")
        self.italic_btn = QPushButton("I")
        self.italic_btn.setCheckable(True)
        self.italic_btn.setStyleSheet("font-style: italic; width: 25px;")
        line1.addWidget(self.bold_btn)
        line1.addWidget(self.italic_btn)

        # 颜色
        line1.addWidget(QLabel("颜色:"))
        self.color_btn = QPushButton()
        self.update_color_btn()
        self.color_btn.clicked.connect(self.select_color)
        line1.addWidget(self.color_btn)

        # 透明度
        line1.addWidget(QLabel("透明度:"))
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.setFixedWidth(100)
        line1.addWidget(self.opacity_slider)
        self.opacity_label = QLabel("100%")
        line1.addWidget(self.opacity_label)

        main_layout.addLayout(line1)

        # ========== 第二行：水印文字 ==========
        line2 = QHBoxLayout()
        line2.setSpacing(5)
        line2.addWidget(QLabel("水印文字:"))
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("请输入水印文字")
        line2.addWidget(self.text_input)
        main_layout.addLayout(line2)

        # ========== 第三行：四角+中心布局按钮 ==========
        positions = ['top-left', 'top-right', 'bottom-left', 'bottom-right', 'center']
        self.pos_buttons = {}
        pos_layout = QHBoxLayout()
        pos_layout.setSpacing(10)
        for pos in positions:
            btn = QPushButton(pos.replace('-', '\n').title())
            btn.setFixedSize(60, 40)
            btn.clicked.connect(lambda checked, p=pos: self.on_pos_button_clicked(p))
            pos_layout.addWidget(btn)
            self.pos_buttons[pos] = btn
        main_layout.addLayout(pos_layout)

        # ====== 信号绑定 ======
        self.font_combo.currentTextChanged.connect(self.emit_settings)
        self.size_spin.valueChanged.connect(self.emit_settings)
        self.bold_btn.toggled.connect(self.emit_settings)
        self.italic_btn.toggled.connect(self.emit_settings)
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        self.text_input.textChanged.connect(self.emit_settings)

        # 初始化
        self.emit_settings()

    # ------------------ 工具方法 ------------------
    def update_color_btn(self):
        self.color_btn.setStyleSheet(
            f"background-color: {self.color.name()}; border: 1px solid gray; width: 30px;"
        )

    def select_color(self):
        color = QColorDialog.getColor(self.color, self, "选择文字颜色")
        if color.isValid():
            self.color = color
            self.update_color_btn()
            self.emit_settings()

    def on_opacity_changed(self, value):
        self.opacity_label.setText(f"{value}%")
        self.emit_settings()

    def on_pos_button_clicked(self, pos_name):
        """水印位置按钮点击事件"""
        self.position_changed.emit(pos_name)

    # ------------------ 核心方法 ------------------
    def get_settings(self):
        rgba = (
            self.color.red(),
            self.color.green(),
            self.color.blue(),
            int(255 * (self.opacity_slider.value() / 100.0))
        )
        return {
            "text": self.text_input.text(),
            "font_family": self.font_combo.currentText(),
            "font_size": self.size_spin.value(),
            "bold": self.bold_btn.isChecked(),
            "italic": self.italic_btn.isChecked(),
            "color": rgba,
            "opacity": self.opacity_slider.value() / 100.0,
        }

    def emit_settings(self):
        self.current_settings = self.get_settings()
        self.settings_changed.emit(self.current_settings)
