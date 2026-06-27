"""
Parallel AxiDraw Utils
Updated utilities that work with the parallel drawing system.
These functions interface with the ParallelDrawingManager to provide
non-blocking drawing operations.
"""

from pyaxidraw import axidraw
import time
from .parallel_drawing import get_drawing_manager
from .global_drawing_state import get_global_drawing_state


def get_time_estimate(drawing_file_path):
    """
    Get time estimate for drawing (this still needs to be synchronous)
    """
    ad = axidraw.AxiDraw()
    ad.options.model = 2
    ad.plot_setup(drawing_file_path)
    ad.options.report_time = True
    ad.options.preview = True
    ad.plot_run()
    time_estimate_in_seconds = ad.time_estimate
    time_estimate_in_minutes = time_estimate_in_seconds / 60
    return round(time_estimate_in_minutes)


def start_or_resume_drawing_parallel(file_path: str, status: str, progress):
    """
    Start or resume drawing using the parallel drawing manager.
    This function is non-blocking and returns immediately.
    
    Args:
        file_path: Path to the SVG file to draw
        status: Current status of the drawing
        progress: Current progress of the drawing
        
    Returns:
        bool: True if drawing was started successfully, False otherwise
    """
    manager = get_drawing_manager()
    return manager.start_drawing(file_path, status, progress)


def toggle_pen_parallel():
    """
    Toggle pen up/down using the parallel drawing manager.
    This function is non-blocking.
    
    Returns:
        bool: True if command was sent successfully, False otherwise
    """
    manager = get_drawing_manager()
    return manager.toggle_pen()


def go_home_parallel():
    """
    Move pen to home position using the parallel drawing manager.
    This function is non-blocking.
    
    Returns:
        bool: True if command was sent successfully, False otherwise
    """
    manager = get_drawing_manager()
    return manager.go_home()


def toggle_manual_align_parallel():
    """
    Enter manual alignment mode using the parallel drawing manager.
    This function is non-blocking.
    
    Returns:
        bool: True if command was sent successfully, False otherwise
    """
    manager = get_drawing_manager()
    return manager.manual_align()


def check_drawing_results():
    """
    Check for results from the drawing process.
    Call this periodically to get updates on drawing progress.
    Also processes results through the global state manager.
    
    Returns:
        dict: Result data if available, None otherwise
    """
    manager = get_drawing_manager()
    result = manager.check_results()
    
    if result:
        # Store result in global state for other windows to access
        global_state = get_global_drawing_state()
        global_state.add_drawing_result(result)
        
        # If drawing is complete, update the status in the global state
        if result.get("type") == "drawing_complete":
            status = result.get("status")
            progress = result.get("progress")
            global_state.update_drawing_status_in_queue(status, progress)
            global_state.clear_current_drawing()
        elif result.get("type") == "error":
            global_state.update_drawing_status_in_queue("Error")
            global_state.clear_current_drawing()
    
    return result


def check_drawing_status():
    """
    Check for status updates from the drawing process.
    Call this periodically to get status messages.
    Also processes status through the global state manager.
    
    Returns:
        tuple: (status_type, status_data) if available, None otherwise
    """
    manager = get_drawing_manager()
    status = manager.check_status()
    
    if status:
        # Store status in global state for other windows to access
        global_state = get_global_drawing_state()
        global_state.add_status_message(status)
    
    return status


def get_global_drawing_results():
    """
    Get drawing results from the global state.
    This allows any window to check for completed drawings.
    
    Returns:
        list: List of pending drawing results
    """
    global_state = get_global_drawing_state()
    return global_state.get_pending_results()


def get_global_status_messages():
    """
    Get status messages from the global state.
    This allows any window to check for status updates.
    
    Returns:
        list: List of pending status messages
    """
    global_state = get_global_drawing_state()
    return global_state.get_pending_status_messages()


def set_current_drawing_info(drawing_index: int, file_path: str, queue_reference: object):
    """
    Set the current drawing information in the global state.
    This allows tracking which drawing is active across window transitions.
    
    Args:
        drawing_index: Index of the drawing in the session queue
        file_path: Path to the SVG file being drawn
        queue_reference: Reference to the session queue object
    """
    global_state = get_global_drawing_state()
    global_state.set_current_drawing(drawing_index, file_path, queue_reference)


def get_current_drawing_info():
    """
    Get the current drawing information from the global state.
    
    Returns:
        dict: Current drawing info if available, None otherwise
    """
    global_state = get_global_drawing_state()
    return global_state.get_current_drawing()


def is_drawing_active():
    """
    Check if a drawing operation is currently active.
    
    Returns:
        bool: True if drawing is active, False otherwise
    """
    manager = get_drawing_manager()
    return manager.is_drawing_active()


def is_drawing_manager_ready():
    """
    Check if the drawing manager is ready to accept commands.
    
    Returns:
        bool: True if ready, False otherwise
    """
    manager = get_drawing_manager()
    return manager.is_ready()


def initialize_drawing_manager():
    """
    Initialize the drawing manager process.
    Should be called when the application starts.
    
    Returns:
        bool: True if initialized successfully, False otherwise
    """
    manager = get_drawing_manager()
    return manager.start_process()


def shutdown_drawing_manager():
    """
    Shutdown the drawing manager process.
    Should be called when the application exits.
    """
    manager = get_drawing_manager()
    manager.stop_process()


# Keep the original synchronous functions for backward compatibility
def toggle_pen(ad: object):
    """Original synchronous toggle pen function"""
    ad = axidraw.AxiDraw()
    ad.options.model = 2
    print ("Toggle pen up/down called..")
    ad.plot_setup()
    ad.options.mode = 'toggle'
    ad.plot_run()


def start_or_resume_drawing(ad: object, file_path: str, status, progress):
    """Original synchronous drawing function"""
    if status == "paused":
        print("Resuming drawing from home position...")
        ad.plot_setup(progress)
        ad.options.mode = "res_home"
        progress = ad.plot_run(True)
        if ad.errors.code == 102:  # Physical pause button pressed
            status = "paused" 
        else:
            status = "finished"
        time.sleep(0.2)
        go_home(ad)
    else:
        ad.plot_setup(file_path)
        progress = ad.plot_run(True)
        if ad.errors.code == 102:
            status = "paused"
        else:
            status = "finished"
        time.sleep(0.2)  # Wait 200 milliseconds
        go_home(ad)

    return progress, status


def toggle_manual_align(ad: object):
    """Original synchronous manual align function"""
    ad.plot_setup()
    ad.options.mode = 'align'
    ad.plot_run()
    

def go_home(ad: object):
    """Original synchronous go home function"""
    ad.plot_setup()
    ad.options.mode = 'manual'
    ad.options.manual_cmd = 'walk_home'
    ad.plot_run()