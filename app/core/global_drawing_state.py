"""
Global Drawing State Manager
This module provides a global state that persists across window transitions,
allowing the drawing process to continue independently of which GUI window is open.
"""

import threading
from typing import Optional, Dict, Any


class GlobalDrawingState:
    """
    Global state manager for tracking drawing progress across the entire application.
    This ensures that drawing status is maintained even when windows are opened/closed.
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self._current_drawing_info: Optional[Dict[str, Any]] = None
        self._drawing_results = []
        self._status_messages = []
        
    def set_current_drawing(self, drawing_index: int, file_path: str, queue_reference: object):
        """
        Set the currently active drawing information.
        
        Args:
            drawing_index: Index of the drawing in the session queue
            file_path: Path to the SVG file being drawn
            queue_reference: Reference to the session queue object
        """
        with self._lock:
            self._current_drawing_info = {
                "drawing_index": drawing_index,
                "file_path": file_path,
                "queue_reference": queue_reference,
                "start_time": None
            }
    
    def get_current_drawing(self) -> Optional[Dict[str, Any]]:
        """Get the current drawing information."""
        with self._lock:
            return self._current_drawing_info.copy() if self._current_drawing_info else None
    
    def clear_current_drawing(self):
        """Clear the current drawing information."""
        with self._lock:
            self._current_drawing_info = None
    
    def add_drawing_result(self, result: Dict[str, Any]):
        """Add a drawing result to be processed by any active window."""
        with self._lock:
            self._drawing_results.append(result)
    
    def get_pending_results(self) -> list:
        """Get and clear all pending drawing results."""
        with self._lock:
            results = self._drawing_results.copy()
            self._drawing_results.clear()
            return results
    
    def add_status_message(self, message: tuple):
        """Add a status message to be processed by any active window."""
        with self._lock:
            self._status_messages.append(message)
    
    def get_pending_status_messages(self) -> list:
        """Get and clear all pending status messages."""
        with self._lock:
            messages = self._status_messages.copy()
            self._status_messages.clear()
            return messages
    
    def update_drawing_status_in_queue(self, status: str, progress=None):
        """
        Update the drawing status directly in the queue.
        This ensures the queue is updated regardless of which window is open.
        """
        with self._lock:
            if self._current_drawing_info and self._current_drawing_info.get("queue_reference"):
                drawing_index = self._current_drawing_info["drawing_index"]
                queue_ref = self._current_drawing_info["queue_reference"]
                
                try:
                    if hasattr(queue_ref, 'queue') and len(queue_ref.queue) > drawing_index:
                        queue_ref.queue[drawing_index].set_status(status)
                        if progress is not None:
                            queue_ref.queue[drawing_index].set_progress(progress)
                except Exception as e:
                    print(f"Error updating queue status: {e}")


# Global instance
global_drawing_state = GlobalDrawingState()


def get_global_drawing_state() -> GlobalDrawingState:
    """Get the global drawing state instance."""
    return global_drawing_state