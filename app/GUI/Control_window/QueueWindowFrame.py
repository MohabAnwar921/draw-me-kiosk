"""
Queue Window Frame - Converted from QueueWindow class to work as a frame
instead of a separate window.
"""

import tkinter as tk
from tkinter import Frame, Listbox, Scrollbar, Canvas, Button, PhotoImage, RIGHT, LEFT, Y, BOTH, SINGLE, END
import os

# Import AxiDraw control functions
from core.axiDraw_utils import start_or_resume_drawing, toggle_pen, toggle_manual_align, go_home
from core.parallel_axiDraw_utils import (
    start_or_resume_drawing_parallel, 
    toggle_pen_parallel, 
    toggle_manual_align_parallel, 
    go_home_parallel,
    check_drawing_results,
    check_drawing_status,
    get_global_drawing_results,
    get_global_status_messages,
    set_current_drawing_info,
    get_current_drawing_info,
    is_drawing_active,
    is_drawing_manager_ready,
    toggle_pen
)

FILE_PATH = os.path.dirname(os.path.abspath(__file__))
ASSETS_PATH = os.path.join(FILE_PATH, "assets", "frame0")


class QueueWindowFrame(tk.Frame):
    def __init__(self, parent, controller, callbacks, session_queue, axidraw_object):
        super().__init__(parent)
        self.controller = controller
        self.callbacks = callbacks
        self.configure(bg="#EAEAEA")
        
        self.session_queue = session_queue
        self.axidraw_object = axidraw_object
        
        self.home_button_pressed = False
        
        # Check if there's already a drawing in progress from a previous window
        current_drawing_info = get_current_drawing_info()
        if current_drawing_info:
            self.current_drawing_index = current_drawing_info.get("drawing_index")
            print(f"Resuming monitoring of drawing #{self.current_drawing_index}")
        else:
            self.current_drawing_index = None
        
        # Setup UI
        self.setup_ui()
        
        # Start periodic checking for drawing updates
        self.check_drawing_updates()
    
    def relative_to_assets(self, path: str) -> str:
        return os.path.join(ASSETS_PATH, path)
    
    def setup_ui(self):
        self.canvas = Canvas(
            self,
            bg="#EAEAEA",
            height=728,
            width=1280,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        self.canvas.place(x=0, y=0)
        
        # THD Logo
        self.image_image_1 = PhotoImage(
            file=self.relative_to_assets("image_1.png"))
        self.image_1 = self.canvas.create_image(
            1071.0,
            69.0,
            image=self.image_image_1
        )

        # Capture page button (Home button)
        self.button_image_1 = PhotoImage(
            file=self.relative_to_assets("button_1.png"))
        self.button_1 = Button(
            self,
            image=self.button_image_1,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.goto_home(),
            relief="flat"
        )
        self.button_1.place(
            x=56.0,
            y=22.0,
            width=86.0,
            height=89.0
        )

        # Main work area rectangle
        self.canvas.create_rectangle(
            339.0,
            124.0,
            1239.0,
            614.0,
            fill="#FFFFFF",
            outline=""
        )
        
        # Work queue area
        self.canvas.create_rectangle(
            39.0,
            124.0,
            320.0,
            614.0,
            fill="#D9D9D9",
            outline=""
        )
            
        # Queue menu
        self.queue_frame = Frame(self, bg="#F5F5F5")
        self.queue_frame.place(x=39.0, y=173.0, width=281.0, height=430.0)
        
        # Create scrollbar
        self.queue_scrollbar = Scrollbar(self.queue_frame, width=23)
        self.queue_scrollbar.pack(side=RIGHT, fill=Y)
        
        # Create listbox
        self.queue_listbox = Listbox(
            self.queue_frame,
            yscrollcommand=self.queue_scrollbar.set,
            bg="#D9D9D9",
            font=("Montserrat Regular", 9),
            selectmode=SINGLE,
            borderwidth=0,
            highlightthickness=0
        )
        self.queue_listbox.pack(side=LEFT, fill=BOTH, expand=True)
        self.populate_listbox()
        
        # Configure scrollbar
        self.queue_scrollbar.config(command=self.queue_listbox.yview)

        # Start/Resume button
        self.button_image_2 = PhotoImage(
            file=self.relative_to_assets("button_2.png"))
        self.button_2 = Button(
            self,
            image=self.button_image_2,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.start_or_resume_selection(),
            relief="flat"
        )
        self.button_2.place(
            x=8.0,
            y=625.0,
            width=180.0,
            height=98.0
        )

        # Preview button
        self.button_image_3 = PhotoImage(
            file=self.relative_to_assets("button_3.png"))
        self.button_3 = Button(
            self,
            image=self.button_image_3,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.preview_selection(),
            relief="flat"
        )
        self.button_3.place(
            x=198.0,
            y=625.0,
            width=172.0,
            height=101.0
        )

        # Move pen to home button
        self.button_image_4 = PhotoImage(
            file=self.relative_to_assets("button_4.png"))
        self.button_4 = Button(
            self,
            image=self.button_image_4,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: go_home_parallel(),
            relief="flat"
        )
        self.button_4.place(
            x=375.0,
            y=614.0,
            width=178.0,
            height=114.0
        )

        # Manual align button
        self.button_image_5 = PhotoImage(
            file=self.relative_to_assets("button_5.png"))
        self.button_5 = Button(
            self,
            image=self.button_image_5,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: toggle_manual_align_parallel(),
            relief="flat"
        )
        self.button_5.place(
            x=559.0,
            y=614.0,
            width=172.0,
            height=114.0
        )

        # Raise/lower pen
        self.button_image_6 = PhotoImage(
            file=self.relative_to_assets("button_6.png"))
        self.button_6 = Button(
            self,
            image=self.button_image_6,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: toggle_pen_parallel(),
            relief="flat"
        )
        self.button_6.place(
            x=736.0,
            y=614.0,
            width=168.0,
            height=112.0
        )

        # Remove selection from queue
        self.button_image_7 = PhotoImage(
            file=self.relative_to_assets("button_7.png"))
        self.button_7 = Button(
            self,
            image=self.button_image_7,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.remove_current_selection(),
            relief="flat"
        )
        self.button_7.place(
            x=910.0,
            y=621.0,
            width=173.0,
            height=105.0
        )

        # Clean queue button
        self.button_image_8 = PhotoImage(
            file=self.relative_to_assets("button_8.png"))
        self.button_8 = Button(
            self,
            image=self.button_image_8,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.clear_session_queue(),
            relief="flat"
        )
        self.button_8.place(
            x=1088.0,
            y=622.0,
            width=183.0,
            height=99.0
        )

        # Instruction text
        self.canvas.create_text(
            173.0,
            22.0,
            anchor="nw",
            text="Press on the pause button found on the drawing device itself\nto pause the on going drawing, then select any of the available\noptions, listed on the right of the \"Pause\" button below",
            fill="#212121",
            font=("Montserrat Regular", 21 * -1)
        )

        # Work queue label
        self.canvas.create_text(
            100.0,
            136.0,
            anchor="nw",
            text="Work queue\n",
            fill="#000000",
            font=("Montserrat Regular", 24 * -1)
        )

        # Add drawing status indicator
        self.status_text = self.canvas.create_text(
            500.0,
            650.0,
            anchor="nw",
            text="Drawing Status: Ready",
            fill="#006400",
            font=("Montserrat Regular", 12 * -1)
        )

    def populate_listbox(self):
        """Populate the listbox with queue items"""
        self.queue_listbox.delete(0, END)  # Clear the listbox first
        
        if self.session_queue and hasattr(self.session_queue, 'queue'):
            if len(self.session_queue.queue) > 0:
                lines = []
                for item in self.session_queue.queue:
                    try:
                        line = item.get_gui_line()
                        lines.append(line)
                    except Exception as e:
                        lines.append(f"Error: {str(e)}")
            
                # Insert new items into the listbox
                for line in lines:
                    self.queue_listbox.insert(END, line)
                    self.queue_listbox.insert(END, "")  # Add empty line for readability
                
                print(f"Queue populated with {len(lines)} items")
            else:
                # Queue exists but is empty
                self.queue_listbox.insert(END, "Queue is empty")
                self.queue_listbox.insert(END, "")
                self.queue_listbox.insert(END, "To add items:")
                self.queue_listbox.insert(END, "1. Take a photo in Main window")
                self.queue_listbox.insert(END, "2. Configure settings in SVG window")
                self.queue_listbox.insert(END, "3. Click 'Add to Queue' button")
                print("Queue is empty - showing instructions")
        else:
            # No queue object
            self.queue_listbox.insert(END, "No queue data available")
            print("No session_queue object available")

    def get_current_selection(self):
        """Get the currently selected item index"""
        selection = self.queue_listbox.curselection()
        if not selection:
            return None
        
        selected_index = selection[0]
        if selected_index is not None:
            # Account for the visual empty lines in the listbox
            if selected_index % 2 == 0:  # Even number
                selected_index = selected_index // 2
                print(f"Selected index: {selected_index}")
                return selected_index
            else:
                print("Selected Empty cell")
                return None
        else:
            return None

    def remove_current_selection(self):
        """Remove the current selection from the session queue"""
        current_selection = self.get_current_selection()
        
        if current_selection is not None:
            self.session_queue.remove_task(index=current_selection)
            self.populate_listbox()

    def clear_session_queue(self):
        """Clear the entire session queue"""
        if self.session_queue:
            self.session_queue.clear_queue()
            self.populate_listbox()

    def goto_home(self):
        """Go back to main window"""
        self.callbacks['queue_to_main']()

    def preview_selection(self):
        """
        Previews the selected task in the preview frame.
        """
        current_selection = self.get_current_selection()
        
        if current_selection is None:
            return
        else:
            preview_image = self.session_queue.queue[current_selection].get_preview_path()
            self.preview_image = PhotoImage(file=preview_image)
            
            # Create or update image in the preview area
            # Clear previous image if it exists
            self.canvas.delete("preview_image")
            
            # Get preview frame dimensions
            preview_width = 1239 - 339
            preview_height = 614 - 124
            # Calculate center position for the image
            x_center = (339 + 1239) / 2
            y_center = (124 + 614) / 2
            
            # Add image to preview frame
            self.canvas.create_image(
            x_center, y_center,
            image=self.preview_image,
            tags="preview_image"
            )

    def start_or_resume_selection(self):
        """Start or resume drawing the selected item"""
        selected_drawing = self.get_current_selection()
        
        if selected_drawing is None:
            print("No drawing selected. Please select a drawing from the queue.")
            return
        
        # Check if the drawing manager is ready
        if not is_drawing_manager_ready():
            print("Drawing manager is not ready. Please wait or restart the application.")
            return
        
        # Check if a drawing is already active
        if is_drawing_active():
            print("A drawing is already in progress. Please wait for it to complete.")
            return
        
        self.current_drawing_index = selected_drawing
        self.update_task_status("In Progress")
        current_selection_file_path = self.session_queue.queue[selected_drawing].get_svg_path()
        current_selection_progress = self.session_queue.queue[selected_drawing].get_progress()
        current_selection_status = self.session_queue.queue[selected_drawing].get_status()
        
        # Set the current drawing info in the global state
        set_current_drawing_info(selected_drawing, current_selection_file_path, self.session_queue)
        
        # Start drawing in parallel
        success = start_or_resume_drawing_parallel(
            current_selection_file_path,
            current_selection_status, 
            current_selection_progress
        )
        
        if success:
            print("Drawing started successfully in parallel")
        else:
            print("Failed to start drawing")
            self.update_task_status("Error")
            self.current_drawing_index = None
        
        self.populate_listbox()

    def update_task_status(self, status):
        """Update the status of the current task"""
        if self.current_drawing_index is not None and self.session_queue:
            try:
                self.session_queue.queue[self.current_drawing_index].set_status(status)
            except (IndexError, AttributeError):
                pass

    def update_status_display(self, message: str, color: str = "#006400"):
        """Update the status display at the bottom of the window"""
        try:
            self.canvas.itemconfig(self.status_text, text=f"Drawing Status: {message}", fill=color)
        except:
            pass

    def check_drawing_updates(self):
        """Periodically check for updates from the parallel drawing process"""
        # Update status display based on current activity
        if is_drawing_active():
            current_drawing_info = get_current_drawing_info()
            if current_drawing_info:
                drawing_index = current_drawing_info.get("drawing_index", "Unknown")
                self.update_status_display(f"Drawing #{drawing_index} in progress...", "#FF8C00")
        else:
            self.update_status_display("Ready", "#006400")
        
        # Check for drawing results and status messages
        result = check_drawing_results()
        status = check_drawing_status()
        
        # Schedule the next check
        self.after(100, self.check_drawing_updates)

    def on_show(self, **kwargs):
        """Called when this frame is shown"""
        self.populate_listbox()

    def on_hide(self):
        """Called when this frame is hidden"""
        pass