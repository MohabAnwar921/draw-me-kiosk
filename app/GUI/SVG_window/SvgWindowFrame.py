"""
SVG Window Frame - Converted from SvgWindow class to work as a frame
instead of a separate window.
"""

import tkinter as tk
from tkinter import Canvas, Button, PhotoImage, BooleanVar, Scale
from tkinter import ttk
import os
from cairosvg import svg2png
from .water_mark_embedder import embed_watermark
from core.axiDraw_utils import get_time_estimate
from core.params_parser import params

FILE_PATH = os.path.dirname(os.path.abspath(__file__))
ASSETS_PATH = os.path.join(FILE_PATH, "assets", "frame0")

# Get static paths from the app paths dictionary
from core.paths import PATHS
SVG_WINDOW_PREVIEW_DIR = PATHS["SVG_WINDOW_PREVIEW_DIR"]
SVG_INPUT_DIR = PATHS["SVG_INPUT_DIR"]
SVG_OUTPUT_DIR = PATHS["SVG_OUTPUT_DIR"]
WATER_MARK_PATH = PATHS["WATER_MARK_PATH"]

# Define global variables
RED_TEXT_COLOR = "#940000"
GREEN_TEXT_COLOR = "#009400"
PREVIEW_WIDTH = 900
PREVIEW_HEIGHT = 490
DRAW_TIME_LIMIT = params['drawing_time_limit'] # Parsed from params.xml
watermark_scale = { # =0.707**n where n is the number of steps down from A3, n = 0 @ A3
    "A3": 1.0,
    "A4": 0.707,
    "A5": 0.5,
    "A6": 0.35
}


class SvgWindowFrame(tk.Frame):
    def __init__(self, parent, controller, callbacks):
        super().__init__(parent)
        self.controller = controller
        self.callbacks = callbacks
        self.configure(bg="#EAEAEA")
        
        # Drawing data - will be set when switching to this frame
        self.linedrawer = None
        self.drawing = None
        self.session_queue = None
        
        # Initialize variables
        self.user_selected_paper_size = "A3"
        self.time_acceptable = False
        self.prompt_label_message = "Loading..."
        self.prompt_label_color = "#000000"
        
        # Setup UI elements
        self.setup_ui()
    
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
            1078.0,
            64.0,
            image=self.image_image_1
        )
        
        # Queue window button
        self.button_image_1 = PhotoImage(
            file=self.relative_to_assets("button_1.png"))
        self.button_1 = Button(
            self,
            image=self.button_image_1,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.queue_button_pressed(),
            relief="flat"
        )
        self.button_1.place(
            x=56.0,
            y=22.0,
            width=86.0,
            height=89.0
        )
        
        # Preview window placeholder (will be updated when drawing is set)
        self.preview_image_item = self.canvas.create_rectangle(
            324.0, 123.0, 1224.0, 613.0,
            fill="#FFFFFF", outline=""
        )
        
        # Settings box
        self.canvas.create_rectangle(
            24.0,
            122.0,
            305.0,
            613.0,
            fill="#D9D9D9",
            outline="")
        
        # Add to Queue button
        self.button_image_2 = PhotoImage(
            file=self.relative_to_assets("button_2.png"))
        self.button_2 = Button(
            self,
            image=self.button_image_2,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.save_changes_and_add_to_queue(),
            relief="flat"
        )
        self.button_2.place(
            x=890.0,
            y=622.0,
            width=335.0,
            height=87.0
        )
        
        # Apply changes button
        self.button_image_3 = PhotoImage(
            file=self.relative_to_assets("button_3.png"))
        self.button_3 = Button(
            self,
            image=self.button_image_3,
            borderwidth=0,
            highlightthickness=0,
            command=self.apply_changes,
            relief="flat"
        )
        self.button_3.place(
            x=471.0,
            y=622.0,
            width=337.0,
            height=86.0
        )
        
        # Retake button
        self.button_image_4 = PhotoImage(
            file=self.relative_to_assets("button_4.png"))
        self.button_4 = Button(
            self,
            image=self.button_image_4,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.retake_button_clicked(),
            relief="flat"
        )
        self.button_4.place(
            x=48.0,
            y=623.0,
            width=339.0,
            height=84.0
        )
        
        # Prompt message label
        self.status_text = self.canvas.create_text(
            178.0,
            50.0,
            anchor="nw",
            text=self.prompt_label_message,
            fill=self.prompt_label_color,
            font=("Montserrat Regular", 24 * -1)
        )
        
        # Canvas settings label
        self.canvas.create_text(
            62.0,
            142.0,
            anchor="nw",
            text="Canvas settings",
            fill="#000000",
            font=("Montserrat Regular", 24 * -1)
        )
        
        # Draw hatch label and toggle
        self.canvas.create_text(
            40.0,
            225.0,
            anchor="nw",
            text="Draw hatch",
            fill="#000000",
            font=("Roboto Regular", 20 * -1)
        )
        
        # Initialize toggle switch images and variable
        self.toggle_on_image = PhotoImage(
            file=self.relative_to_assets("toggle_switch_on.png"))
        self.toggle_off_image = PhotoImage(
            file=self.relative_to_assets("toggle_switch_off.png"))
        self.draw_hatch_var = BooleanVar()
        self.draw_hatch_var.set(params['draw_hatch'])
        
        def update_toggle_image():
            if self.draw_hatch_var.get():
                self.draw_hatch_toggle.configure(image=self.toggle_on_image)
            else:
                self.draw_hatch_toggle.configure(image=self.toggle_off_image)
        
        def toggle_switch():
            self.draw_hatch_var.set(not self.draw_hatch_var.get())
            update_toggle_image()
        
        self.draw_hatch_toggle = Button(
            self,
            image=self.toggle_on_image,
            borderwidth=0,
            highlightthickness=0,
            command=toggle_switch,
            relief="flat",
            bg="#D9D9D9",
            activebackground="#D9D9D9"
        )
        self.draw_hatch_toggle.place(
            x=220.0,
            y=215.0
        )

        # Hatch size label and slider
        self.canvas.create_text(
            40.0,
            288.0,
            anchor="nw",
            text="Hatch size",
            fill="#000000",
            font=("Roboto Regular", 20 * -1)
        )

        self.hatch_size_slider = Scale(
            self,
            from_=params['hatch_size_max'],
            to=params['hatch_size_min'],
            orient='horizontal',
            length=120,
            width=15,
            bg="#D9D9D9",
            highlightthickness=0,
            sliderrelief="flat"
        )
        self.hatch_size_slider.set(params['hatch_size'])
        self.hatch_size_slider.place(
            x=175.0,
            y=280.0
        )

        self.canvas.create_text(
            40.0,
            320.0,
            anchor="nw",
            text="The lower the more\nrefined the hatch lines",
            fill="#2E2E2E",
            font=("Roboto Italic", 12 * -1)
        )
        
        # Resolution label and slider
        self.canvas.create_text(
            40.0,
            385.0,
            anchor="nw",
            text="Resolution",
            fill="#000000",
            font=("Roboto Regular", 20 * -1)
        )
        
        self.resolution_slider = Scale(
            self,
            from_=params['min_resolution'],
            to=params['max_resolution'],
            orient='horizontal',
            length=120,
            width=15,
            bg="#D9D9D9",
            highlightthickness=0,
            sliderrelief="flat"
        )
        self.resolution_slider.set(params['resolution'])
        self.resolution_slider.place(
            x=175.0,
            y=367.0
        )
        
        # Canvas size label
        self.canvas.create_text(
            40.0,
            458.0,
            anchor="nw",
            text="Canvas size",
            fill="#000000",
            font=("Roboto Regular", 20 * -1)
        )
        
        # Paper size cycling functionality
        self.paper_sizes = ['A3', 'A4', 'A5', 'A6']
        self.current_size_index = 0
        
        # Load paper size images
        self.paper_size_images = {
            'A3': PhotoImage(file=self.relative_to_assets("a3.png")),
            'A4': PhotoImage(file=self.relative_to_assets("a4.png")),
            'A5': PhotoImage(file=self.relative_to_assets("a5.png")),
            'A6': PhotoImage(file=self.relative_to_assets("a6.png"))
        }
        
        def cycle_paper_size():
            self.current_size_index = (self.current_size_index + 1) % len(self.paper_sizes)
            current_size = self.paper_sizes[self.current_size_index]
            self.paper_size_button.configure(image=self.paper_size_images[current_size])
            self.user_selected_paper_size = current_size
        
        # Paper size button
        self.paper_size_button = Button(
            self,
            image=self.paper_size_images['A3'],
            borderwidth=0,
            highlightthickness=0,
            command=cycle_paper_size,
            relief="flat",
            bg="#D9D9D9",
            activebackground="#D9D9D9"
        )
        self.paper_size_button.place(
            x=215.0,
            y=448.0
        )
        
        # Watermark position label and dropdown
        self.canvas.create_text(
            40.0,
            530.0,
            anchor="nw",
            text="Watermark\nposition",
            fill="#000000",
            font=("Roboto Regular", 20 * -1)
        )
        
        style = ttk.Style()
        style.configure('Wide.TCombobox',
                       background='#D9D9D9',
                       fieldbackground='#FFFFFF',
                       selectbackground='#0078D7',
                       selectforeground='white',
                       arrowsize=30)
        
        self.watermark_position = ttk.Combobox(
            self,
            values=["Top left", "Top right", "Bottom left", "Bottom right"],
            state="readonly",
            width=15,
            style='Wide.TCombobox'
        )
        self.watermark_position.set(params['watermark_position'])
        self.watermark_position.place(
            x=175.0,
            y=530.0,
            width=120,
            height=50
        )

        # Black line separator
        self.canvas.create_rectangle(
            55.0,
            188.0,
            274.0,
            190.0,
            fill="#000000",
            outline=""
        )
    
    def set_drawing_data(self, linedrawer, drawing, session_queue):
        """Set the drawing data for this frame"""
        self.linedrawer = linedrawer
        self.drawing = drawing
        self.session_queue = session_queue
        
        if drawing and hasattr(drawing, 'get_preview_path'):
            try:
                # Load and display the preview image
                preview_path = drawing.get_preview_path()
                if os.path.exists(preview_path):
                    preview_img = PhotoImage(file=preview_path)
                    # Update the preview image
                    self.canvas.delete(self.preview_image_item)
                    self.preview_image_item = self.canvas.create_image(
                        774.0,  # Center x coordinate
                        368.0,  # Center y coordinate
                        image=preview_img
                    )
                    self.preview_img = preview_img  # Keep reference
                    
                    # Update status with time estimate
                    time_estimate = get_time_estimate(drawing.get_svg_path())
                    self.prompt_label_message, self.prompt_label_color = self.update_label_message(time_estimate)
                    self.canvas.itemconfig(self.status_text, text=self.prompt_label_message, fill=self.prompt_label_color)
            except Exception as e:
                print(f"Error loading preview: {e}")
    
    def retake_button_clicked(self):
        """Handle retake button click - go back to main window"""
        self.callbacks['svg_to_main']()
    
    def apply_changes(self):
        """Apply the user's changes to the drawing"""
        if not self.drawing or not self.linedrawer:
            print("No drawing or linedrawer available")
            return
            
        # Update status to "applying changes"
        self.prompt_label_message, self.prompt_label_color = self.update_label_message(applying_changes=True)
        self.canvas.itemconfig(self.status_text, text=self.prompt_label_message, fill=self.prompt_label_color)
        self.update()
        
        try:
            # Get the values from the sliders
            svg_width, svg_height = self.paper_size_to_pixel_values(self.user_selected_paper_size)
            
            # Get current drawing parameters (paths) from the object
            current_drawing_svg_path = self.drawing.get_svg_path()
            
            # Update the linedrawer parameters with the user selected values
            self.linedrawer.update_parameters(
                draw_hatch=self.draw_hatch_var.get(),
                hatch_size=self.hatch_size_slider.get(),
                resolution=self.resolution_slider.get(),
                svg_width=svg_width,
                svg_height=svg_height
            )
            
            self.linedrawer.sketch(os.path.join(SVG_INPUT_DIR, "capture.png"), current_drawing_svg_path)
            embed_watermark(
                main_svg_path=current_drawing_svg_path,
                water_mark_path=WATER_MARK_PATH,
                corner=self.watermark_position.get(),
                scale=watermark_scale[self.user_selected_paper_size],
                output_path=current_drawing_svg_path
            )
            
            # Generate preview
            print("Generating preview...")
            preview_path = self.drawing.get_preview_path()
            svg2png(
                url=current_drawing_svg_path,
                write_to=preview_path,
                output_width=PREVIEW_WIDTH,
                output_height=PREVIEW_HEIGHT
            )
            print("Preview generated")
            
            # Update the preview image
            new_preview = PhotoImage(file=preview_path)
            self.canvas.itemconfig(self.preview_image_item, image=new_preview)
            self.preview_img = new_preview  # Keep a reference
            
            # Update status with time estimate
            time_estimate = get_time_estimate(current_drawing_svg_path)
            self.prompt_label_message, self.prompt_label_color = self.update_label_message(time_estimate)
            self.canvas.itemconfig(self.status_text, text=self.prompt_label_message, fill=self.prompt_label_color)
            
        except Exception as e:
            print(f"Error applying changes: {e}")
            self.canvas.itemconfig(self.status_text, text=f"Error: {e}", fill=RED_TEXT_COLOR)
    
    def paper_size_to_pixel_values(self, paper_size):
        """Convert paper size to pixel values"""
        if paper_size == "A3":
            return 1450, 1050
        elif paper_size == "A4":
            return 1025, 743
        elif paper_size == "A5":
            return 725, 525
        elif paper_size == "A6":
            return 512, 371
    
    def update_label_message(self, time_estimate=0, applying_changes=False):
        """Update the status message based on time estimate"""
        if applying_changes:
            message = "Applying changes, please wait..."
            text_color = "#000000"
        elif time_estimate > DRAW_TIME_LIMIT:
            message = "This will take long, try adjusting the canvas settings."
            text_color = RED_TEXT_COLOR
            self.time_acceptable = False
        else:
            message = f"Ready to draw! Estimated drawing time: {time_estimate} minutes"
            text_color = GREEN_TEXT_COLOR
            self.time_acceptable = True
        return message, text_color
    
    def save_changes_and_add_to_queue(self):
        """Save changes and add drawing to queue"""
        if self.time_acceptable and self.drawing and self.session_queue:
            self.drawing.set_paper_size(self.user_selected_paper_size)
            self.session_queue.add_task(self.drawing)
            print(f"Added task: {self.drawing.get_file()} to queue")
            self.session_queue.update_file()
            # Switch to queue window
            self.callbacks['svg_to_queue']()
        else:
            print("Cannot add to queue: time not acceptable or missing data")
    
    def queue_button_pressed(self):
        """Handle queue button click - go to queue window"""
        self.callbacks['svg_to_queue']()
    
    def on_show(self, **kwargs):
        """Called when this frame is shown"""
        pass

    def on_hide(self):
        """Called when this frame is hidden"""
        pass
