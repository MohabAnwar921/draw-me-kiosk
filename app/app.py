"""
Modified app.py to use the unified GUI with frames instead of separate windows
"""

from core.paths import PATHS
from core.linedraw.linedraw_class import LineDrawer
from pyaxidraw import axidraw 
from core.queue import Queue
from core.parallel_axiDraw_utils import initialize_drawing_manager, shutdown_drawing_manager
from core.background_monitor import start_background_monitor, stop_background_monitor
from GUI.THDDrawApplication import THDDrawApplication


def main():
    # Initializations
    session_queue = Queue()
    session_queue.retrive_from_file()
    lineDrawer = LineDrawer()
    ad = axidraw.AxiDraw()
    ad.options.model = 2
    
    # Initialize parallel drawing manager
    print("Initializing parallel drawing manager...")
    if not initialize_drawing_manager():
        print("Failed to initialize drawing manager.")
    
    # Start background monitor
    print("Starting background drawing monitor...")
    start_background_monitor()
    
    try:
        # Create and run the unified GUI application
        app = THDDrawApplication()
        app.initialize_frames(session_queue, lineDrawer, ad)
        app.run()
        
    except KeyboardInterrupt:
        print("Application interrupted by user")
    finally:
        # Cleanup
        print("Shutting down background monitor...")
        stop_background_monitor()
        print("Shutting down parallel drawing manager...")
        shutdown_drawing_manager()
        print("Application terminated successfully")


if __name__ == "__main__":
    main()