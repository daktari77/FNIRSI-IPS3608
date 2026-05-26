from __future__ import annotations

from PySide6.QtCore import QThread, Signal

# Number of back-to-back read failures before the thread gives up and signals
# an error.  A single transient glitch (garbled frame, USB hiccup) is retried
# silently; only a persistent fault escalates.
_MAX_CONSECUTIVE_ERRORS = 3


class MeasurementThread(QThread):
    """Runs read_measurements() in a background thread so the Qt main thread stays responsive.

    Transient failures (up to _MAX_CONSECUTIVE_ERRORS in a row) are retried
    without surfacing an error to the UI.  Only a persistent fault terminates
    the thread and emits error_occurred.
    """

    measurement_ready = Signal(object)  # Measurement
    error_occurred = Signal(str)

    def __init__(self, client, interval_ms: int = 500):
        super().__init__()
        self._client = client
        self._interval_ms = max(100, interval_ms)

    def run(self) -> None:
        consecutive_errors = 0
        while not self.isInterruptionRequested():
            try:
                m = self._client.read_measurements()
                consecutive_errors = 0
            except Exception as exc:
                consecutive_errors += 1
                if consecutive_errors >= _MAX_CONSECUTIVE_ERRORS:
                    if not self.isInterruptionRequested():
                        self.error_occurred.emit(str(exc))
                    return
                # Transient error: wait one interval before retrying.
                self.msleep(self._interval_ms)
                continue

            if not self.isInterruptionRequested():
                self.measurement_ready.emit(m)
            self.msleep(self._interval_ms)
