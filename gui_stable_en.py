import os
import sys
import time
import shutil
import tempfile
from datetime import datetime
from PIL import Image, ImageDraw

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QFileDialog,
    QVBoxLayout, QHBoxLayout, QRadioButton, QLineEdit, QTextEdit,
    QButtonGroup, QGroupBox, QSlider, QGridLayout, QSizePolicy
)
from PySide6.QtGui import QPixmap, QImage, QPainter, QColor, QBrush, QPen
from PySide6.QtCore import Qt, QSize

from src.JopConverter import JopImageConverter
from src.JopImage import JopCanvasType


class JoPGUIV12(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JoP Conversion Tool – Stable V12 UI")
        self.setMinimumSize(1300, 900)

        # Core state variables
        self.current_image = None
        self.preview_qpixmap = None
        self.png_path = None
        self.grid_width = 4  
        self.split_canvas_size = 32  # 16 или 32
        self.resize_mode = "auto"
        self.converter = JopImageConverter()
        self.single_canvas_size = "32x32"

        # Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # --- LEFT PANEL ---
        left_panel = QVBoxLayout()
        left_panel.setSpacing(16)

        # File Section
        file_group = QGroupBox("FILE")
        file_layout = QVBoxLayout()
        self.btn_open_png = QPushButton("📂 Open PNG")
        self.btn_open_png.setMinimumHeight(50)
        self.btn_open_png.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_open_png.clicked.connect(self.open_png)
        file_layout.addWidget(self.btn_open_png)
        file_group.setLayout(file_layout)
        left_panel.addWidget(file_group)

        # Info Section
        info_group = QGroupBox("INFO")
        info_layout = QVBoxLayout()
        self.entry_title = QLineEdit("Untitled")
        self.entry_author = QLineEdit("Player")
        info_layout.addWidget(QLabel("Painting title:"))
        info_layout.addWidget(self.entry_title)
        info_layout.addWidget(QLabel("Author:"))
        info_layout.addWidget(self.entry_author)
        info_group.setLayout(info_layout)
        left_panel.addWidget(info_group)

        # Mode Section
        mode_group_box = QGroupBox("MODE")
        mode_layout = QVBoxLayout()
        self.mode_group = QButtonGroup()
        self.single_mode = QRadioButton("Single Canvas")
        self.split_mode = QRadioButton("Split")
        self.single_mode.setChecked(True)
        self.mode_group.addButton(self.single_mode)
        self.mode_group.addButton(self.split_mode)
        self.single_mode.toggled.connect(self.update_ui_state)
        self.split_mode.toggled.connect(self.update_ui_state)
        mode_layout.addWidget(self.single_mode)
        mode_layout.addWidget(self.split_mode)
        mode_group_box.setLayout(mode_layout)
        left_panel.addWidget(mode_group_box)

        # Canvas Size Buttons (Single)
        self.canvas_size_group = QGroupBox("CANVAS SIZE (single)")
        self.canvas_buttons = self.create_canvas_buttons(["16x16", "32x16", "16x32", "32x32"], is_split=False)
        left_panel.addWidget(self.canvas_size_group)

        # Split Canvas Size Selection (as canvas buttons)
        self.split_canvas_group = QGroupBox("TILE SIZE (split)")
        self.split_canvas_buttons = self.create_canvas_buttons(["16x16", "32x32"], is_split=True)
        left_panel.addWidget(self.split_canvas_group)

        # Grid Width Slider
        grid_group = QGroupBox("GRID WIDTH (quality)")
        grid_layout = QVBoxLayout()
        self.grid_slider = QSlider(Qt.Horizontal)
        self.grid_slider.setMinimum(1)
        self.grid_slider.setMaximum(10)
        self.grid_slider.setValue(self.grid_width)
        self.grid_slider.valueChanged.connect(self.change_grid_width)
        grid_layout.addWidget(self.grid_slider)
        grid_group.setLayout(grid_layout)
        left_panel.addWidget(grid_group)
        self.grid_group = grid_group

        # Resize Mode (hidden in single mode)
        self.resize_group = QGroupBox("RESIZE MODE")
        resize_layout = QVBoxLayout()
        self.resize_crop = QRadioButton("Crop to fit grid")
        self.resize_resize = QRadioButton("Shrink to fit grid")
        self.resize_auto = QRadioButton("Auto (minimal changes)")
        self.resize_auto.setChecked(True)
        self.resize_crop.toggled.connect(lambda: self.set_resize_mode("crop"))
        self.resize_resize.toggled.connect(lambda: self.set_resize_mode("resize"))
        self.resize_auto.toggled.connect(lambda: self.set_resize_mode("auto"))
        resize_layout.addWidget(self.resize_crop)
        resize_layout.addWidget(self.resize_resize)
        resize_layout.addWidget(self.resize_auto)
        self.resize_group.setLayout(resize_layout)
        left_panel.addWidget(self.resize_group)

        # Export Button
        self.btn_export = QPushButton("🚀 Export")
        self.btn_export.setMinimumHeight(50)
        self.btn_export.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_export.clicked.connect(self.export)
        left_panel.addWidget(self.btn_export)

        # --- PREVIEW PANEL ---
        preview_panel = QVBoxLayout()
        self.preview_label = QLabel("No image")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #222; border: 1px solid #444; font-size: 14px; color: #aaa;")
        preview_panel.addWidget(self.preview_label, stretch=1)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        preview_panel.addWidget(QLabel("Log:"))
        preview_panel.addWidget(self.log_text, stretch=0)

        main_layout.addLayout(left_panel, 2)
        main_layout.addLayout(preview_panel, 5)

        self.setStyleSheet(self._qss_style())
        self.update_ui_state()

    def _qss_style(self):
        return """ 
        QMainWindow { background-color: #1b1b1b; }
        QGroupBox {
            background-color: #1e1e1e;
            border: none;
            border-radius: 6px;
            margin-top: 10px;
            padding: 8px;
            font-weight: 600;
            color: #ccc;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 4px;
            color: #aaa;
            font-size: 11pt;
        }
        QLabel { color: #eee; }
        QLineEdit, QTextEdit {
            background-color: #2a2a2a; border: 1px solid #555;
            padding: 4px; border-radius: 4px; color: #f0f0f0;
        }
        QPushButton {
            background-color: #3a3a3a; border: 1px solid #555;
            border-radius: 6px;
            color: #ddd;
            padding: 8px 12px;
            font-size: 11pt;
        }
        QPushButton:checked {
            border: 2px solid #fff;
        }
        QPushButton:hover { background-color: #505050; }
        QRadioButton { padding: 3px; color: #ddd; }
        QSlider::groove:horizontal {
            border: 1px solid #444; height: 6px; background: #2a2a2a; border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background: #555; border: 1px solid #888; width: 14px;
            margin: -4px 0; border-radius: 7px;
        }
        """

    def create_canvas_buttons(self, sizes, is_split=False):
        grid = QGridLayout()
        grid.setSpacing(10)
        buttons = []
        for i, size in enumerate(sizes):
            btn = QPushButton()
            btn.setCheckable(True)
            if (not is_split and size == "32x32") or (is_split and size == "32x32"):
                btn.setChecked(True)
            btn.setFixedSize(QSize(60, 60))
            if is_split:
                btn.clicked.connect(lambda checked, s=size: self.set_split_canvas_size(int(s.split("x")[0])))
            else:
                btn.clicked.connect(lambda checked, s=size: self.set_canvas_size(s))
            label = QLabel(size)
            label.setAlignment(Qt.AlignCenter)
            buttons.append((btn, size, label))
            grid.addWidget(btn, i // 2 * 2, i % 2)
            grid.addWidget(label, i // 2 * 2 + 1, i % 2)

        group = self.split_canvas_group if is_split else self.canvas_size_group
        group.setLayout(grid)
        return buttons

    def set_canvas_size(self, size):
        self.single_canvas_size = size
        for btn, s, lbl in self.canvas_buttons:
            btn.setChecked(s == size)
        self.update_canvas_icons(self.canvas_buttons)
        self.update_preview()

    def set_split_canvas_size(self, size):
        self.split_canvas_size = size
        for btn, s, lbl in self.split_canvas_buttons:
            btn.setChecked(int(s.split("x")[0]) == size)
        self.update_canvas_icons(self.split_canvas_buttons)
        self.update_preview()

    def update_canvas_icons(self, button_list):
        for btn, size, lbl in button_list:
            w, h = map(int, size.split("x"))
            max_dim = 40
            scale = min(max_dim / w, max_dim / h)
            disp_w, disp_h = int(w * scale), int(h * scale)
            pen_width = 2
            if w == 16 and h == 16:
                pen_width = 4  
            pixmap = QPixmap(50, 50)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(QPen(QColor("#aaa"), pen_width))
            painter.setBrush(QBrush(QColor("#fff")))
            painter.drawRect((50 - disp_w) // 2, (50 - disp_h) // 2, disp_w, disp_h)
            painter.end()
            btn.setIcon(pixmap)
            btn.setIconSize(QSize(40, 40))

    def log(self, msg, success=False):
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        if success:
            self.log_text.append(f'<span style="color: lightgreen;">{timestamp} {msg}</span>')
        else:
            self.log_text.append(f"{timestamp} {msg}")

    def set_resize_mode(self, mode):
        self.resize_mode = mode
        self.update_preview()

    def change_grid_width(self, value):
        self.grid_width = value
        self.update_preview()

    def update_ui_state(self):
        is_single = self.single_mode.isChecked()
        self.canvas_size_group.setVisible(is_single)
        self.split_canvas_group.setVisible(not is_single)
        self.grid_group.setVisible(not is_single)
        self.resize_group.setVisible(not is_single)

        self.update_canvas_icons(self.canvas_buttons)
        self.update_canvas_icons(self.split_canvas_buttons)

        self.update_preview()

    def calculate_grid(self, img_w, img_h, grid_w):
        aspect_ratio = img_h / img_w
        grid_h = max(1, round(grid_w * aspect_ratio))
        return grid_w, grid_h

    def open_png(self):
        self.png_path, _ = QFileDialog.getOpenFileName(self, "Select PNG", "", "PNG Files (*.png)")
        if not self.png_path:
            return
        try:
            self.current_image = Image.open(self.png_path).convert("RGBA")
            self.update_preview()
            self.log(f"PNG loaded: {os.path.basename(self.png_path)}")
        except Exception as e:
            self.log(f"Error: {e}")

    def draw_preview(self, img, grid_w, grid_h):
        tile_w = img.width // grid_w
        tile_h = img.height // grid_h
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        line_color = (255, 255, 255, int(255 * 0.15))
        for x in range(1, grid_w):
            draw.line([(x * tile_w, 0), (x * tile_w, img.height)], fill=line_color)
        for y in range(1, grid_h):
            draw.line([(0, y * tile_h), (img.width, y * tile_h)], fill=line_color)
        img = Image.alpha_composite(img, overlay)
        self.display_image(img)

    def display_image(self, img):
        qimage = QImage(img.tobytes(), img.width, img.height, img.width * 4, QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimage)
        pixmap = pixmap.scaled(self.preview_label.size(), Qt.KeepAspectRatio, Qt.FastTransformation)
        self.preview_label.setPixmap(pixmap)

    def get_canvas_type(self, w, h):
        if (w, h) == (16, 16):
            return JopCanvasType.SMALL
        elif (w, h) == (32, 32):
            return JopCanvasType.LARGE
        elif (w, h) == (16, 32):
            return JopCanvasType.TALL
        elif (w, h) == (32, 16):
            return JopCanvasType.LONG
        else:
            return JopCanvasType.SMALL

    def update_preview(self):
        if not self.current_image:
            return
        img = self.current_image.copy()
        if self.single_mode.isChecked():
            w, h = map(int, self.single_canvas_size.split("x"))
            img = img.resize((w, h), Image.NEAREST)
            self.display_image(img)
        else:
            grid_w = self.grid_width
            grid_h = self.calculate_grid(img.width, img.height, grid_w)[1]
            target_w, target_h = grid_w * self.split_canvas_size, grid_h * self.split_canvas_size

            if self.resize_mode in ["resize", "auto"]:
                img = img.resize((target_w, target_h), Image.NEAREST)
            else:
                img = img.crop((0, 0, target_w, target_h))

            self.draw_preview(img, grid_w, grid_h)

    def convert_tile(self, png_path, out_path, title, author, w, h):
        ctype = self.get_canvas_type(w, h)
        self.log(f"Converting: {png_path} -> {out_path} [{ctype}]")
        self.converter.importImage(png_path, out_path, title, author, ctype)
        time.sleep(1.0)

    def export(self):
        if not self.current_image:
            self.log("Error: First load a PNG image.")
            return

        title = (self.entry_title.text().strip() or "Untitled").replace(' ', '_')
        author = self.entry_author.text().strip() or "Player"
        output_dir = QFileDialog.getExistingDirectory(self, "Select folder to export")
        if not output_dir:
            return

        if self.single_mode.isChecked():
            w, h = map(int, self.single_canvas_size.split("x"))
            temp_png = os.path.join(output_dir, "single_temp.png")
            self.current_image.resize((w, h), Image.NEAREST).save(temp_png)
            out_path = os.path.join(output_dir, f"{title}.paint")
            self.convert_tile(temp_png, out_path, title, author, w, h)
            os.remove(temp_png)
            self.log(f"1 canvas exported: {out_path}", success=True)
        else:
            grid_w = self.grid_width
            grid_h = self.calculate_grid(self.current_image.width, self.current_image.height, grid_w)[1]
            target_w, target_h = grid_w * self.split_canvas_size, grid_h * self.split_canvas_size

            if self.resize_mode in ["resize", "auto"]:
                work_img = self.current_image.resize((target_w, target_h), Image.NEAREST)
            else:
                work_img = self.current_image.crop((0, 0, target_w, target_h))

            counter = 1
            temp_dir = tempfile.mkdtemp(prefix="jop_tiles_")
            try:
                for y in range(grid_h):
                    for x in range(grid_w):
                        box = (x * self.split_canvas_size, y * self.split_canvas_size,
                               (x + 1) * self.split_canvas_size, (y + 1) * self.split_canvas_size)
                        tile = work_img.crop(box)
                        temp_png = os.path.join(temp_dir, f"tile_{counter}.png")
                        tile.save(temp_png)
                        unique_title = f"{title}_{counter}"
                        out_path = os.path.join(output_dir, f"{unique_title}.paint")
                        self.convert_tile(temp_png, out_path, unique_title, author, self.split_canvas_size, self.split_canvas_size)
                        self.log(f"Saved: {out_path}")
                        counter += 1
                self.log(f"Split завершена: {grid_w * grid_h} холстов", success=True)
            finally:
                shutil.rmtree(temp_dir)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = JoPGUIV12()
    window.show()
    sys.exit(app.exec())
