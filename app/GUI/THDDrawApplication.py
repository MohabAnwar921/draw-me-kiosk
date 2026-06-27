"""
Unified GUI Application for THD Draw
This module contains the main application window that manages different frames
instead of separate windows.
"""

import tkinter as tk
from tkinter import ttk


class THDDrawApplication:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("THD Draw")
        self.root.geometry("1280x728+0+5")
        self.root.configure(bg="#EAEAEA")
        self.root.resizable(False, False)
        
        # Store the icon to prevent garbage collection
        try:
            # Try to load icon from MainWindow assets
            import os
            icon_path = os.path.join(os.path.dirname(__file__), "Main_window", "assets", "frame0", "icon.png")
            if os.path.exists(icon_path):
                self.icon_image = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(True, self.icon_image)
        except Exception as e:
            print(f"Could not load icon: {e}")
        
        # Container frame for all pages
        self.container = tk.Frame(self.root)
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        
        # Dictionary to store frames
        self.frames = {}
        
        # Current frame reference
        self.current_frame = None
        
        # Application state
        self.app_data = {
            'session_queue': None,
            'linedrawer': None,
            'axidraw_object': None,
            'current_drawing': None
        }
        
        # Callbacks for frame communication
        self.frame_callbacks = {
            'main_to_svg': self.show_svg_window,
            'main_to_queue': self.show_queue_window,
            'svg_to_main': self.show_main_window,
            'svg_to_queue': self.show_queue_window,
            'queue_to_main': self.show_main_window,
            'queue_to_svg': self.show_svg_window
        }
    
    def initialize_frames(self, session_queue, linedrawer, axidraw_object):
        """Initialize all frames with required objects"""
        from GUI.Main_window.MainWindowFrame import MainWindowFrame
        from GUI.SVG_window.SvgWindowFrame import SvgWindowFrame
        from GUI.Control_window.QueueWindowFrame import QueueWindowFrame
        
        self.app_data['session_queue'] = session_queue
        self.app_data['linedrawer'] = linedrawer
        self.app_data['axidraw_object'] = axidraw_object
        
        # Create frames
        self.frames['main'] = MainWindowFrame(
            parent=self.container,
            controller=self,
            callbacks=self.frame_callbacks
        )
        
        self.frames['svg'] = SvgWindowFrame(
            parent=self.container,
            controller=self,
            callbacks=self.frame_callbacks
        )
        
        self.frames['queue'] = QueueWindowFrame(
            parent=self.container,
            controller=self,
            callbacks=self.frame_callbacks,
            session_queue=session_queue,
            axidraw_object=axidraw_object
        )
        
        # Position all frames in the same location
        for frame in self.frames.values():
            frame.grid(row=0, column=0, sticky="nsew")
        
        # Show main window initially
        self.show_main_window()
    
    def show_main_window(self, **kwargs):
        """Switch to main window frame"""
        if self.current_frame:
            self.current_frame.on_hide()
        
        self.current_frame = self.frames['main']
        self.current_frame.tkraise()
        self.current_frame.on_show(**kwargs)
    
    def show_svg_window(self, **kwargs):
        """Switch to SVG window frame"""
        if self.current_frame:
            self.current_frame.on_hide()
        
        # Pass required data to SVG frame
        if 'current_drawing' in kwargs:
            self.app_data['current_drawing'] = kwargs['current_drawing']
        
        self.frames['svg'].set_drawing_data(
            self.app_data['linedrawer'],
            self.app_data['current_drawing'],
            self.app_data['session_queue']
        )
        
        self.current_frame = self.frames['svg']
        self.current_frame.tkraise()
        self.current_frame.on_show(**kwargs)
    
    def show_queue_window(self, **kwargs):
        """Switch to queue window frame"""
        if self.current_frame:
            self.current_frame.on_hide()
        
        self.current_frame = self.frames['queue']
        self.current_frame.tkraise()
        self.current_frame.on_show(**kwargs)
    
    def get_app_data(self, key):
        """Get application data"""
        return self.app_data.get(key)
    
    def set_app_data(self, key, value):
        """Set application data"""
        self.app_data[key] = value
    
    def run(self):
        """Start the application"""
        self.root.mainloop()
    
    def quit(self):
        """Quit the application"""
        if self.current_frame:
            self.current_frame.on_hide()
        self.root.quit()
        self.root.destroy()
