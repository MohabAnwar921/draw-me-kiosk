"""
Parallel Drawing Manager
This module handles running the drawing process in a separate process
to keep the GUI responsive while drawing is in progress.
Uses multiprocessing instead of threading for true parallelism.
"""

import multiprocessing as mp
import time
import os
from queue import Empty
from typing import Optional, Tuple, Any
from pyaxidraw import axidraw


class DrawingProcess:
    """Handles the actual drawing operations in a separate process"""
    
    @staticmethod
    def draw_worker(command_queue: mp.Queue, result_queue: mp.Queue, status_queue: mp.Queue):
        """
        Worker function that runs in a separate process to handle drawing operations.
        
        Args:
            command_queue: Queue for receiving drawing commands
            result_queue: Queue for sending back results
            status_queue: Queue for sending status updates
        """
        ad = None
        
        try:
            # Initialize AxiDraw in the worker process
            ad = axidraw.AxiDraw()
            ad.options.model = 2  # Set the model to AxiDraw CE/A3
            
            status_queue.put(("process_ready", True))
            
            while True:
                try:
                    # Wait for commands from the main process
                    command = command_queue.get(timeout=1.0)
                    
                    if command is None:  # Shutdown signal
                        break
                    
                    cmd_type = command.get("type")
                    
                    if cmd_type == "start_drawing":
                        file_path = command.get("file_path")
                        status = command.get("status", "pending")
                        progress = command.get("progress")
                        
                        progress, status = DrawingProcess._execute_drawing(
                            ad, file_path, status, progress, status_queue
                        )
                        
                        result_queue.put({
                            "type": "drawing_complete",
                            "progress": progress,
                            "status": status,
                            "success": True
                        })
                        
                    elif cmd_type == "toggle_pen":
                        DrawingProcess._toggle_pen(ad)
                        result_queue.put({
                            "type": "pen_toggled",
                            "success": True
                        })
                        
                    elif cmd_type == "go_home":
                        DrawingProcess._go_home(ad)
                        result_queue.put({
                            "type": "home_complete",
                            "success": True
                        })
                        
                    elif cmd_type == "manual_align":
                        DrawingProcess._manual_align(ad)
                        result_queue.put({
                            "type": "align_complete",
                            "success": True
                        })
                        
                except Empty:
                    # No command received, continue waiting
                    continue
                except Exception as e:
                    result_queue.put({
                        "type": "error",
                        "error": str(e),
                        "success": False
                    })
                    
        except Exception as e:
            status_queue.put(("process_error", str(e)))
        finally:
            status_queue.put(("process_shutdown", True))
    
    @staticmethod
    def _execute_drawing(ad, file_path: str, status: str, progress, status_queue: mp.Queue) -> Tuple[Any, str]:
        """Execute the drawing operation"""
        try:
            status_queue.put(("drawing_started", file_path))
            
            if status == "paused":
                status_queue.put(("drawing_status", "Resuming drawing from home position..."))
                ad.plot_setup(progress)
                ad.options.mode = "res_home"
                progress = ad.plot_run(True)
                if ad.errors.code == 102:  # Physical pause button pressed
                    status = "paused"
                    status_queue.put(("drawing_status", "Drawing paused"))
                else:
                    status = "finished"
                    status_queue.put(("drawing_status", "Drawing completed"))
                DrawingProcess._go_home(ad)
            else:
                status_queue.put(("drawing_status", "Starting new drawing..."))
                ad.plot_setup(file_path)
                progress = ad.plot_run(True)
                if ad.errors.code == 102:
                    status = "paused"
                    status_queue.put(("drawing_status", "Drawing paused"))
                else:
                    status = "finished"
                    status_queue.put(("drawing_status", "Drawing completed"))
                DrawingProcess._go_home(ad)
                
            return progress, status
            
        except Exception as e:
            status_queue.put(("drawing_error", str(e)))
            return progress, "error"
    
    @staticmethod
    def _toggle_pen(ad):
        """Toggle pen up/down"""
        ad = axidraw.AxiDraw()
        ad.options.model = 2  # Set the model to AxiDraw CE/A3
        ad.plot_setup()
        ad.options.mode = 'toggle'
        ad.plot_run()
    
    @staticmethod
    def _go_home(ad):
        """Return pen to home position"""
        ad.plot_setup()
        ad.options.mode = 'manual'
        ad.options.manual_cmd = 'walk_home'
        ad.plot_run()
    
    @staticmethod
    def _manual_align(ad):
        """Enter manual alignment mode"""
        ad.plot_setup()
        ad.options.mode = 'align'
        ad.plot_run()


class ParallelDrawingManager:
    """
    Manages parallel drawing operations using multiprocessing.
    Provides a simple interface for the GUI to start/stop drawing operations
    while keeping the main thread responsive.
    """
    
    def __init__(self):
        self.process: Optional[mp.Process] = None
        self.command_queue: Optional[mp.Queue] = None
        self.result_queue: Optional[mp.Queue] = None
        self.status_queue: Optional[mp.Queue] = None
        self.is_drawing = False
        self.is_process_ready = False
        
    def start_process(self) -> bool:
        """
        Start the drawing process.
        
        Returns:
            bool: True if process started successfully, False otherwise
        """
        if self.process and self.process.is_alive():
            return True
            
        try:
            # Create communication queues
            self.command_queue = mp.Queue()
            self.result_queue = mp.Queue()
            self.status_queue = mp.Queue()
            
            # Start the worker process
            self.process = mp.Process(
                target=DrawingProcess.draw_worker,
                args=(self.command_queue, self.result_queue, self.status_queue)
            )
            self.process.start()
            
            # Wait for process to be ready
            timeout = 10  # 10 seconds timeout
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    status_type, status_data = self.status_queue.get(timeout=0.1)
                    if status_type == "process_ready":
                        self.is_process_ready = True
                        return True
                    elif status_type == "process_error":
                        print(f"Process error: {status_data}")
                        return False
                except Empty:
                    continue
                    
            print("Timeout waiting for process to be ready")
            return False
            
        except Exception as e:
            print(f"Error starting process: {e}")
            return False
    
    def stop_process(self):
        """Stop the drawing process"""
        if self.process and self.process.is_alive():
            # Send shutdown signal
            if self.command_queue:
                self.command_queue.put(None)
            
            # Wait for process to terminate
            self.process.join(timeout=5)
            
            # Force terminate if still alive
            if self.process.is_alive():
                self.process.terminate()
                self.process.join()
        
        self.process = None
        self.command_queue = None
        self.result_queue = None
        self.status_queue = None
        self.is_drawing = False
        self.is_process_ready = False
    
    def start_drawing(self, file_path: str, status: str = "pending", progress=None) -> bool:
        """
        Start a drawing operation in parallel.
        
        Args:
            file_path: Path to the SVG file to draw
            status: Current status of the drawing
            progress: Current progress of the drawing
            
        Returns:
            bool: True if command was sent successfully, False otherwise
        """
        if not self.is_process_ready:
            if not self.start_process():
                return False
        
        try:
            command = {
                "type": "start_drawing",
                "file_path": file_path,
                "status": status,
                "progress": progress
            }
            self.command_queue.put(command)
            self.is_drawing = True
            return True
        except Exception as e:
            print(f"Error starting drawing: {e}")
            return False
    
    def toggle_pen(self) -> bool:
        """Toggle pen up/down"""
        if not self.is_process_ready:
            if not self.start_process():
                return False
        
        try:
            command = {"type": "toggle_pen"}
            self.command_queue.put(command)
            return True
        except Exception as e:
            print(f"Error toggling pen: {e}")
            return False
    
    def go_home(self) -> bool:
        """Move pen to home position"""
        if not self.is_process_ready:
            if not self.start_process():
                return False
        
        try:
            command = {"type": "go_home"}
            self.command_queue.put(command)
            return True
        except Exception as e:
            print(f"Error going home: {e}")
            return False
    
    def manual_align(self) -> bool:
        """Enter manual alignment mode"""
        if not self.is_process_ready:
            if not self.start_process():
                return False
        
        try:
            command = {"type": "manual_align"}
            self.command_queue.put(command)
            return True
        except Exception as e:
            print(f"Error entering manual align: {e}")
            return False
    
    def check_results(self) -> Optional[dict]:
        """
        Check for results from the drawing process.
        
        Returns:
            dict: Result data if available, None otherwise
        """
        if not self.result_queue:
            return None
        
        try:
            result = self.result_queue.get_nowait()
            if result.get("type") == "drawing_complete":
                self.is_drawing = False
            return result
        except Empty:
            return None
    
    def check_status(self) -> Optional[Tuple[str, Any]]:
        """
        Check for status updates from the drawing process.
        
        Returns:
            tuple: (status_type, status_data) if available, None otherwise
        """
        if not self.status_queue:
            return None
        
        try:
            return self.status_queue.get_nowait()
        except Empty:
            return None
    
    def is_drawing_active(self) -> bool:
        """Check if a drawing operation is currently active"""
        return self.is_drawing
    
    def is_ready(self) -> bool:
        """Check if the process is ready to accept commands"""
        return self.is_process_ready and self.process and self.process.is_alive()
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.stop_process()


# Global instance for the application
drawing_manager = ParallelDrawingManager()


def get_drawing_manager() -> ParallelDrawingManager:
    """Get the global drawing manager instance"""
    return drawing_manager
