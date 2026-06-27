"""
Main Window Frame - Converted from MainWindow class to work as a frame
instead of a separate window.
"""

import tkinter as tk
from tkinter import Canvas, Button, PhotoImage, Label
from picamera2 import Picamera2
import cv2
from PIL import Image, ImageTk
from rembg import remove
import os

FILE_PATH = os.path.dirname(os.path.abspath(__file__))
ASSETS_PATH = os.path.join(FILE_PATH, "assets", "frame0")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
APP_DIR = os.path.dirname(PARENT_DIR)

CAPTURE_PATH = os.path.join(APP_DIR, "data", "svg_inputs_outputs", "svg_input")


class MainWindowFrame(tk.Frame):
    def __init__(self, parent, controller, callbacks):
        super().__init__(parent)
        self.controller = controller
        self.callbacks = callbacks
        self.configure(bg="#EAEAEA")
        
        # Camera initialization - will be done in on_show
        self.picam2 = None
        self._camera_update_after_id = None
        
        self.queue_button_pressed_flag = False
        
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
        
        self.image_image_1 = PhotoImage(
            file=self.relative_to_assets("image_1.png"))
        self.image_1 = self.canvas.create_image(
            1078.0,
            64.0,
            image=self.image_image_1
        )

        # Create the status text on canvas
        self.status_text = self.canvas.create_text(
            250.0,
            48.0,
            anchor="nw",
            text="Ready to take image!",
            fill="#000000",
            font=("Montserrat Bold", 30 * -1)
        )

        # Create buttons
        self.setup_buttons()

        # Create camera frame
        self.camera_frame = Label(self, bg="#D9D9D9")
        self.camera_frame.place(x=300, y=123, width=667, height=483)
    
    def setup_buttons(self):
        self.button_image_1 = PhotoImage(
            file=self.relative_to_assets("button_1.png"))
        self.button_1 = Button(
            self,
            image=self.button_image_1,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.capture_removebg_save(time_delay=10),
            relief="flat"
        )
        self.button_1.place(
            x=890.0,
            y=622.0,
            width=335.0,
            height=87.0
        )

        self.button_image_2 = PhotoImage(
            file=self.relative_to_assets("button_2.png"))
        self.button_2 = Button(
            self,
            image=self.button_image_2,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.capture_removebg_save(time_delay=5),
            relief="flat"
        )
        self.button_2.place(
            x=471.0,
            y=622.0,
            width=337.0,
            height=86
        )

        self.button_image_3 = PhotoImage(
            file=self.relative_to_assets("button_3.png"))
        self.button_3 = Button(
            self,
            image=self.button_image_3,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.capture_removebg_save(time_delay=0),
            relief="flat"
        )
        self.button_3.place(
            x=48.0,
            y=622.0,
            width=339.0,
            height=84.0
        )

        self.button_image_4 = PhotoImage(
            file=self.relative_to_assets("button_4.png"))
        self.button_4 = Button(
            self,
            image=self.button_image_4,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.queue_button_pressed(),
            relief="flat"
        )
        self.button_4.place(
            x=56.0,
            y=22.0,
            width=86.0,
            height=89.0
        )

    def queue_button_pressed(self):
        """Switch to queue window"""
        self.callbacks['main_to_queue']()

    def capture_removebg_save(self, time_delay):
        """Handle image capture with optional countdown"""
        if time_delay > 0:
            self.countdown_and_capture(time_delay)
            return

        self.update_status_text("Captured! now generating the drawing...")

        if self.picam2 is None:
            self.update_status_text("Camera not initialized!")
            return

        try:
            self.master.config(cursor="watch")
            self.update()
            print("Capturing image...")
            frame = self.picam2.capture_array()
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            img = Image.fromarray(frame_bgr)
            print("Removing background...")
            img = remove(img)
            print("Saving image...")
            img.save(os.path.join(CAPTURE_PATH, "capture.png"))
            print("Image saved to: ", os.path.join(CAPTURE_PATH, "capture.png"))
            
            self.master.config(cursor="")
            
            # Generate new drawing and switch to SVG window
            from core.drawing import Drawing
            from cairosvg import svg2png
            from GUI.SVG_window.water_mark_embedder import embed_watermark
            from core.paths import PATHS
            
            lineDrawer = self.controller.get_app_data('linedrawer')
            current_drawing = Drawing()
            current_drawing_file_path = current_drawing.get_svg_path()
            current_drawing_preview_path = current_drawing.get_preview_path()
            
            # Generate primary svg drawing
            lineDrawer.sketch(os.path.join(PATHS["SVG_INPUT_DIR"], "capture.png"), current_drawing_file_path)
            embed_watermark(main_svg_path=current_drawing_file_path, 
                          water_mark_path=PATHS["WATER_MARK_PATH"], 
                          output_path=current_drawing_file_path)

            # Generate the preview image from the SVG file
            svg2png(url=current_drawing_file_path, write_to=current_drawing_preview_path, output_width=900, output_height=490)
            
            # Switch to SVG window
            self.callbacks['main_to_svg'](current_drawing=current_drawing)
            
        except Exception as e:
            print(f"Capture error: {e}")
            self.update_status_text(f"Error: {e}")
            self.master.config(cursor="")

    def update_status_text(self, text):
        """Update the status text on the canvas"""
        if hasattr(self, 'status_text'):
            self.canvas.itemconfig(self.status_text, text=text)

    def countdown_and_capture(self, seconds):
        """Show countdown before capture"""
        def update_countdown(remaining):
            if remaining > 0:
                self.update_status_text(f"{remaining}...")
                self.after(1000, lambda: update_countdown(remaining - 1))
            else:
                self.after(100, lambda: self.capture_removebg_save(0))
        update_countdown(seconds)

    def init_camera(self):
        """Initialize camera when frame is shown"""
        if self.picam2 is None:
            try:
                self.picam2 = Picamera2()
                config = self.picam2.create_preview_configuration(main={"format": 'RGB888', "size": (667, 483)})
                self.picam2.configure(config)
                self.picam2.start()
                self.update_camera_feed()
            except Exception as e:
                print(f"Camera initialization failed: {e}")
                self.camera_frame.config(text=f"Camera Error: {e}")

    def update_camera_feed(self):
        """Update the camera feed display"""
        if self.picam2 is not None:
            try:
                frame = self.picam2.capture_array()
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                img = Image.fromarray(frame_bgr)
                imgtk = ImageTk.PhotoImage(image=img)
                self.camera_frame.imgtk = imgtk
                self.camera_frame.config(image=imgtk)
                self._camera_update_after_id = self.after(10, self.update_camera_feed)
            except Exception as e:
                print(f"Camera feed error: {e}")

    def stop_camera(self):
        """Stop camera when frame is hidden"""
        if self._camera_update_after_id:
            self.after_cancel(self._camera_update_after_id)
            self._camera_update_after_id = None
        
        if self.picam2 is not None:
            try:
                self.picam2.stop()
                self.picam2.close()
                self.picam2 = None
            except Exception as e:
                print(f"Camera cleanup error: {e}")

    def on_show(self, **kwargs):
        """Called when this frame is shown"""
        self.init_camera()
        self.update_status_text("Ready to take image!")

    def on_hide(self):
        """Called when this frame is hidden"""
        self.stop_camera()
