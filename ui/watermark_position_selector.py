# ui/watermark_position_selector.py
from PyQt6.QtWidgets import QWidget, QPushButton, QGridLayout
from PyQt6.QtCore import pyqtSignal

class WatermarkPositionSelector(QWidget):
    """
    水印位置选择面板：
    - 提供五个按钮：左上、右上、左下、右下、中间
    - 点击按钮发射 position_changed(str) 信号
    """

    position_changed = pyqtSignal(str)  # 信号参数: "top-left", "top-right", "bottom-left", "bottom-right", "center"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QGridLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(0,0,0,0)

        # 定义五个位置按钮
        self.buttons = {}

        positions = {
            "top-left": (0, 0),
            "top-right": (0, 2),
            "bottom-left": (2, 0),
            "bottom-right": (2, 2),
            "center": (1, 1),
        }

        for name, (row, col) in positions.items():
            btn = QPushButton()
            btn.setFixedSize(30, 30)
            btn.setToolTip(name.replace("-", " ").title())
            btn.clicked.connect(lambda checked, n=name: self.on_button_clicked(n))
            layout.addWidget(btn, row, col)
            self.buttons[name] = btn

        # 占位按钮（不可点击）
        for r in range(3):
            for c in range(3):
                if layout.itemAtPosition(r, c) is None:
                    layout.addWidget(QWidget(), r, c)

    def on_button_clicked(self, name: str):
        self.position_changed.emit(name)
