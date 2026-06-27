"""
Background Drawing Monitor
This module provides a background thread that monitors drawing progress
even when no GUI windows are actively checking for updates.
"""

import threading
import time
from typing import Optional
from .parallel_axiDraw_utils import check_drawing_results, check_drawing_status


class BackgroundDrawingMonitor:
    """
    Background monitor that continuously checks for drawing updates
    and ensures the global state is maintained.
    """
    
    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False
    
    def start(self):
        """Start the background monitoring thread."""
        if self._running:
            return
        
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        self._running = True
        print("Background drawing monitor started")
    
    def stop(self):
        """Stop the background monitoring thread."""
        if not self._running:
            return
        
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        self._running = False
        print("Background drawing monitor stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop that runs in the background thread."""
        while not self._stop_event.is_set():
            try:
                # Check for drawing results and status
                # The parallel_axiDraw_utils functions automatically handle
                # updating the global state
                check_drawing_results()
                check_drawing_status()
                
                # Sleep for a short period to avoid excessive CPU usage
                time.sleep(0.5)  # Check every 500ms
                
            except Exception as e:
                print(f"Error in background drawing monitor: {e}")
                time.sleep(1)  # Wait longer on error
    
    def is_running(self) -> bool:
        """Check if the monitor is running."""
        return self._running


# Global instance
background_monitor = BackgroundDrawingMonitor()


def start_background_monitor():
    """Start the global background monitor."""
    background_monitor.start()


def stop_background_monitor():
    """Stop the global background monitor."""
    background_monitor.stop()


def is_background_monitor_running() -> bool:
    """Check if the background monitor is running."""
    return background_monitor.is_running()