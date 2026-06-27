import os

"""
This module declares the PATHS dictionary useful for the rest of the application modules.
"""

# Get the base directory path
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # This should give /home/iot/thd-draw

# Define paths relative to base directory
PATHS = {
    "DATA_DIR": os.path.join(APP_DIR, "data"),
    "SVG_INPUT_DIR": os.path.join(APP_DIR, "data", "svg_inputs_outputs", "svg_input"),
    "SVG_OUTPUT_DIR": os.path.join(APP_DIR, "data", "svg_inputs_outputs", "svg_output"),
    "SVG_WINDOW_PREVIEW_DIR": os.path.join(APP_DIR, "data", "svg_window_preview"),
    "WATER_MARK_PATH": os.path.join(APP_DIR, "data", "static", "thd_watermark.svg")
}
