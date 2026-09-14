#!/usr/bin/env python3
"""Live-demo GUI for the Hill cipher over Z_26^2 (PySide6).

Reuses cipher_tools.evaluate_key for the numeric report and visualize.py's
draw_bijective_scatter / draw_heatmap for the embedded plots, so the GUI,
the CLI tester, and the batch figure generator all share one implementation.

Run:
    source .venv/bin/activate   # needs numpy, matplotlib, PySide6
    python3 src/gui_app.py
"""

import sys

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from cipher_tools import MOD, evaluate_key
from visualize import CASES, draw_bijective_scatter, draw_heatmap

DEFAULT_MESSAGE = "ATTACKATDAWN"

PRESET_SHORT_LABELS = {
    1: "Invertible (det=9)",
    2: "Det=0, |ker|=26",
    3: "Factor 2, |ker|=2",
    4: "Factor 13, |ker|=13",
}

STYLESHEET = """
QMainWindow, QWidget {
    background-color: #f4f6f9;
    color: #22303f;
    font-family: "Helvetica Neue", "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}
QGroupBox {
    background-color: #ffffff;
    border: 1px solid #d7dee6;
    border-radius: 6px;
    margin-top: 14px;
    padding: 10px;
    font-weight: 600;
    color: #2f4a63;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}
QLabel#titleLabel {
    font-size: 19px;
    font-weight: 700;
    color: #1f3b57;
}
QLabel#subtitleLabel {
    font-size: 12px;
    color: #5b7185;
}
QLineEdit, QSpinBox {
    background-color: #ffffff;
    border: 1px solid #c3ccd6;
    border-radius: 4px;
    padding: 4px 6px;
    selection-background-color: #9dc3e6;
}
QLineEdit:focus, QSpinBox:focus {
    border: 1px solid #3b6ea5;
}
QPushButton {
    background-color: #3b6ea5;
    color: white;
    border: none;
    border-radius: 5px;
    padding: 7px 10px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #305a87;
}
QPushButton:pressed {
    background-color: #244667;
}
QPushButton#presetButton {
    background-color: #eef2f7;
    color: #2f4a63;
    border: 1px solid #c3ccd6;
    font-weight: 500;
}
QPushButton#presetButton:hover {
    background-color: #dde6ef;
}
QTextEdit#resultsView {
    background-color: #ffffff;
    border: 1px solid #d7dee6;
    border-radius: 6px;
    font-family: "Menlo", "Consolas", monospace;
    font-size: 12px;
}
QLabel#matrixPreview {
    font-family: "Menlo", "Consolas", monospace;
    color: #5b7185;
}
QLabel#statusLabel {
    color: #b3452c;
    font-weight: 600;
}
"""


class CipherExplorer(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Secret Code Explorer — Hill Cipher over Z₂₆²")
        self.resize(1180, 700)

        self._build_ui()
        self._connect_signals()
        self._update_matrix_preview()

    # ---- UI construction ---------------------------------------------------

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        root.addWidget(self._build_control_panel(), stretch=0)
        root.addWidget(self._build_plot_panel(), stretch=1)

    def _build_control_panel(self) -> QWidget:
        panel = QWidget()
        panel.setFixedWidth(360)
        layout = QVBoxLayout(panel)
        layout.setSpacing(12)

        title = QLabel("Secret Code Explorer")
        title.setObjectName("titleLabel")
        subtitle = QLabel("MAT-208 · Hill cipher, T(v) = Kv mod 26")
        subtitle.setObjectName("subtitleLabel")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        layout.addWidget(self._build_message_box())
        layout.addWidget(self._build_key_box())
        layout.addWidget(self._build_preset_box())

        self.run_button = QPushButton("Run Transformation")
        layout.addWidget(self.run_button)

        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        layout.addWidget(self._build_results_box(), stretch=1)
        return panel

    def _build_message_box(self) -> QGroupBox:
        box = QGroupBox("Message")
        v = QVBoxLayout(box)
        self.message_edit = QLineEdit(DEFAULT_MESSAGE)
        self.message_edit.setPlaceholderText("Enter message to encode...")
        v.addWidget(self.message_edit)
        return box

    def _build_key_box(self) -> QGroupBox:
        box = QGroupBox("Key Matrix K")
        v = QVBoxLayout(box)

        grid = QGridLayout()
        self.spin_a = self._make_spinbox()
        self.spin_b = self._make_spinbox()
        self.spin_c = self._make_spinbox()
        self.spin_d = self._make_spinbox()
        for label, spin, row, col in (
            ("a", self.spin_a, 0, 0), ("b", self.spin_b, 0, 2),
            ("c", self.spin_c, 1, 0), ("d", self.spin_d, 1, 2),
        ):
            grid.addWidget(QLabel(label), row, col)
            grid.addWidget(spin, row, col + 1)
        v.addLayout(grid)

        self.matrix_preview = QLabel()
        self.matrix_preview.setObjectName("matrixPreview")
        v.addWidget(self.matrix_preview)

        # Default to the Case 1 canonical invertible key.
        self.spin_a.setValue(3)
        self.spin_b.setValue(3)
        self.spin_c.setValue(2)
        self.spin_d.setValue(5)
        return box

    def _make_spinbox(self) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(0, MOD - 1)
        return spin

    def _build_preset_box(self) -> QGroupBox:
        box = QGroupBox("Preset Evaluation Cases")
        v = QVBoxLayout(box)
        self.preset_buttons = []
        for case in CASES:
            label = f"Case {case['id']}: {PRESET_SHORT_LABELS[case['id']]}"
            btn = QPushButton(label)
            btn.setObjectName("presetButton")
            btn.setProperty("case_id", case["id"])
            btn.setToolTip(f"{case['name']} — K = {case['K'].tolist()}")
            v.addWidget(btn)
            self.preset_buttons.append(btn)
        return box

    def _build_results_box(self) -> QGroupBox:
        box = QGroupBox("Report")
        v = QVBoxLayout(box)
        self.results_view = QTextEdit()
        self.results_view.setObjectName("resultsView")
        self.results_view.setReadOnly(True)
        v.addWidget(self.results_view)
        return box

    def _build_plot_panel(self) -> QWidget:
        panel = QFrame()
        panel.setStyleSheet("background-color: #ffffff; border: 1px solid #d7dee6; border-radius: 6px;")
        layout = QVBoxLayout(panel)
        self.figure = Figure(figsize=(9, 6.5))
        self.canvas = FigureCanvasQTAgg(self.figure)
        layout.addWidget(self.canvas)
        return panel

    # ---- Signals -------------------------------------------------------------

    def _connect_signals(self) -> None:
        for spin in (self.spin_a, self.spin_b, self.spin_c, self.spin_d):
            spin.valueChanged.connect(self._update_matrix_preview)
        self.run_button.clicked.connect(self._on_run_clicked)
        for btn in self.preset_buttons:
            btn.clicked.connect(self._on_preset_clicked)

    def _update_matrix_preview(self) -> None:
        a, b, c, d = self.spin_a.value(), self.spin_b.value(), self.spin_c.value(), self.spin_d.value()
        self.matrix_preview.setText(f"K = [[{a}, {b}], [{c}, {d}]]")

    # ---- Actions ---------------------------------------------------------

    def _on_run_clicked(self) -> None:
        K = np.array([
            [self.spin_a.value(), self.spin_b.value()],
            [self.spin_c.value(), self.spin_d.value()],
        ])
        self._run_pipeline(K, title="Custom Key", heatmap_vmin=None, heatmap_vmax=None)

    def _on_preset_clicked(self) -> None:
        case_id = self.sender().property("case_id")
        case = next(c for c in CASES if c["id"] == case_id)
        K = case["K"]
        self.spin_a.setValue(int(K[0, 0]))
        self.spin_b.setValue(int(K[0, 1]))
        self.spin_c.setValue(int(K[1, 0]))
        self.spin_d.setValue(int(K[1, 1]))
        title = f"Case {case['id']}: {case['name']}"
        self._run_pipeline(
            K, title=title,
            heatmap_vmin=case.get("heatmap_vmin"), heatmap_vmax=case.get("heatmap_vmax"),
        )

    def _run_pipeline(self, K: np.ndarray, title: str, heatmap_vmin, heatmap_vmax) -> None:
        message = self.message_edit.text().strip()
        if not message:
            self.status_label.setText("Enter a message before running the transformation.")
            return
        self.status_label.setText("")

        result = evaluate_key(message, K)
        self._render_report(message, K, result)

        self.figure.clf()
        if result["invertible"]:
            draw_bijective_scatter(self.figure, K, title)
        else:
            draw_heatmap(self.figure, K, title, vmin=heatmap_vmin, vmax=heatmap_vmax)
        self.canvas.draw_idle()

    def _render_report(self, message: str, K: np.ndarray, result: dict) -> None:
        lines = [
            f"K = {K.tolist()}",
            f"det(K) mod 26 = {result['det']}",
            f"gcd(det(K), 26) = {result['gcd']}",
            f"Invertible mod 26: {result['invertible']}",
            "",
            f"Message:    {message.upper()}",
            f"Ciphertext: {result['ciphertext']}",
        ]
        if result["invertible"]:
            lines += [
                f"K^-1 mod 26 = {result['K_inv'].tolist()}",
                f"Decoded:    {result['decoded']}",
            ]
        else:
            v0 = result["kernel_vector"]
            lines += [
                "",
                f"Decoding cannot proceed: (det K)^-1 mod 26 does not exist "
                f"because gcd(det(K), 26) = {result['gcd']} != 1.",
                f"Nonzero kernel vector v0 (K v0 = 0 mod 26): {v0.tolist() if v0 is not None else None}",
                "Any plaintext digraph v collides with v + v0 under this key (sec 2.4) —",
                "decoding is many-to-one, not just hard.",
            ]
        self.results_view.setPlainText("\n".join(lines))


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = CipherExplorer()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
