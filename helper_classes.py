import os
import threading
from PyQt6.QtCore import QObject, pyqtSignal

class FifoWatcher(QObject):
    """
    Watches a single FIFO file and emits a signal with the new data when available.
    The data is emitted as a string; parsing is up to the receiver.
    """
    data_received = pyqtSignal(str)

    def __init__(self, fifo_path, poll_interval=0.1, parent=None):
        super().__init__(parent)
        self.fifo_path = fifo_path
        self.poll_interval = poll_interval
        self._running = False
        self._thread = None

    def start(self):
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._watch_fifo, daemon=True)
            self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)
            self._thread = None

    def _watch_fifo(self):
        while self._running:
            try:
                with open(self.fifo_path, 'r') as f:
                    for line in f:
                        if not self._running:
                            break
                        self.data_received.emit(line.strip())
            except Exception:
                # If FIFO doesn't exist or is not open for writing, wait and retry
                pass
            # Sleep before retrying
            import time
            time.sleep(self.poll_interval)
