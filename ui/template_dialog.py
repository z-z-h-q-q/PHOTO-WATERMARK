"""
模板编辑对话框，用于创建和编辑水印模板。
依赖：PyQt6
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox,
                           QPushButton, QColorDialog)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt

class TemplateDialog(QDialog):
    def __init__(self, parent=None, template_data=None):
        super().__init__(parent)
        self.setWindowTitle("水印模板编辑")
        self.template_data = template_data or {}
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # 模板名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("模板名称:"))
        self.name_input = QLineEdit(self.template_data.get('name', ''))
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # 字体大小
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("字体大小:"))
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 72)
        self.font_size.setValue(self.template_data.get('font_size', 36))
        font_layout.addWidget(self.font_size)
        layout.addLayout(font_layout)

        # 不透明度
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("不透明度:"))
        self.opacity = QDoubleSpinBox()
        self.opacity.setRange(0.1, 1.0)
        self.opacity.setSingleStep(0.1)
        self.opacity.setValue(self.template_data.get('opacity', 1.0))
        opacity_layout.addWidget(self.opacity)
        layout.addLayout(opacity_layout)

        # 位置
        position_layout = QHBoxLayout()
        position_layout.addWidget(QLabel("位置:"))
        self.position = QComboBox()
        self.position.addItems(['右下角', '右上角', '左下角', '左上角', '居中'])
        pos_map = {'right-bottom': 0, 'right-top': 1, 'left-bottom': 2, 
                   'left-top': 3, 'center': 4}
        self.position.setCurrentIndex(pos_map.get(
            self.template_data.get('position', 'right-bottom'), 0))
        position_layout.addWidget(self.position)
        layout.addLayout(position_layout)

        # 颜色选择
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("颜色:"))
        self.color_btn = QPushButton()
        self.color = QColor(self.template_data.get('color', '#FFFFFF'))
        self.update_color_button()
        self.color_btn.clicked.connect(self.choose_color)
        color_layout.addWidget(self.color_btn)
        layout.addLayout(color_layout)

        # 确定取消按钮
        buttons = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

    def choose_color(self):
        color = QColorDialog.getColor(self.color, self)
        if color.isValid():
            self.color = color
            self.update_color_button()

    def update_color_button(self):
        self.color_btn.setStyleSheet(
            f"background-color: {self.color.name()}; min-width: 60px;")

    def get_template_data(self):
        pos_map = {0: 'right-bottom', 1: 'right-top', 2: 'left-bottom',
                  3: 'left-top', 4: 'center'}
        return {
            'name': self.name_input.text(),
            'font_size': self.font_size.value(),
            'opacity': self.opacity.value(),
            'position': pos_map[self.position.currentIndex()],
            'color': self.color.name()
        }