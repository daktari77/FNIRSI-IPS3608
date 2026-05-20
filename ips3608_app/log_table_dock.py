from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHBoxLayout,
    QPushButton, QHeaderView
)

class LogTableDockWidget(QDockWidget):
    export_requested = Signal()
    clear_requested = Signal()
    close_requested = Signal()

    def __init__(self, parent=None):
        super().__init__("Log Table", parent)
        self.setAllowedAreas(Qt.RightDockWidgetArea)
        self.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.setObjectName("LogTableDockWidget")
        self.setVisible(False)

        main = QWidget()
        layout = QVBoxLayout(main)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "Time",
            "Voltage V",
            "Current A",
            "Power W",
            "Temperature C",
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.table.setColumnWidth(0, 160)
        self.table.setColumnWidth(1, 90)
        self.table.setColumnWidth(2, 90)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 120)

        controls = QHBoxLayout()
        self.export_btn = QPushButton("Export CSV")
        self.clear_btn = QPushButton("Clear Log")
        self.close_btn = QPushButton("Close")
        controls.addWidget(self.export_btn)
        controls.addWidget(self.clear_btn)
        controls.addStretch(1)
        controls.addWidget(self.close_btn)

        layout.addWidget(self.table)
        layout.addLayout(controls)
        main.setLayout(layout)
        self.setWidget(main)

        self.export_btn.clicked.connect(self.export_requested.emit)
        self.clear_btn.clicked.connect(self.clear_requested.emit)
        self.close_btn.clicked.connect(self._on_close)

    def _on_close(self):
        self.setVisible(False)
        self.close_requested.emit()

    def set_samples(self, samples):
        self.table.setRowCount(len(samples))
        for row, sample in enumerate(samples):
            self.table.setItem(row, 0, QTableWidgetItem(sample.timestamp.strftime("%Y-%m-%d %H:%M:%S")))
            for col, val, fmt, align in [
                (1, sample.voltage_v, "{:.2f}", Qt.AlignRight),
                (2, sample.current_a, "{:.3f}", Qt.AlignRight),
                (3, sample.power_w, "{:.3f}", Qt.AlignRight),
                (4, sample.temperature_c, "{:.1f}", Qt.AlignRight),
            ]:
                item = QTableWidgetItem(fmt.format(val))
                item.setTextAlignment(align | Qt.AlignVCenter)
                self.table.setItem(row, col, item)
        self.table.scrollToBottom()
