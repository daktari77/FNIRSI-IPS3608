from __future__ import annotations

from PySide6.QtCore import QThread, Signal


class MeasurementThread(QThread):
    """Runs read_measurements() in a background thread so the Qt main thread stays responsive."""

    measurement_ready = Signal(object)  # Measurement
    error_occurred = Signal(str)

    def __init__(self, client, interval_ms: int = 500):
        super().__init__()
        self._client = client
        self._interval_ms = max(100, interval_ms)

    def run(self) -> None:
        while not self.isInterruptionRequested():
            try:
                m = self._client.read_measurements()
            except Exception as exc:
                if not self.isInterruptionRequested():
                    self.error_occurred.emit(str(exc))
                return
            if not self.isInterruptionRequested():
                self.measurement_ready.emit(m)
            self.msleep(self._interval_ms)
