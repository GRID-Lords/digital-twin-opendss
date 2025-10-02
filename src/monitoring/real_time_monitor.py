"""
Real-time Monitoring Module
"""
import time
import threading
from datetime import datetime
from typing import Dict, Any, Callable

class RealTimeMonitor:
    def __init__(self):
        self.running = False
        self.callbacks = []
        self.metrics = {}
        self.thread = None

    def start(self):
        """Start monitoring"""
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        """Stop monitoring"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)

    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            self.update_metrics()
            time.sleep(1)

    def update_metrics(self):
        """Update current metrics"""
        self.metrics = {
            "timestamp": datetime.now().isoformat(),
            "cpu_usage": 25.5,
            "memory_usage": 45.2,
            "active_connections": 3,
            "data_points_per_sec": 100
        }

        # Notify callbacks
        for callback in self.callbacks:
            try:
                callback(self.metrics)
            except Exception as e:
                print(f"Callback error: {e}")

    def register_callback(self, callback: Callable):
        """Register a callback for metric updates"""
        self.callbacks.append(callback)

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return self.metrics