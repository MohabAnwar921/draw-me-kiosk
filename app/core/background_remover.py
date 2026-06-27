"""
Background Remover Module

This module removes the background from an image using the rembg library.

Args:
    image: Image as a numpy array
    saves the image in /app/core/data/svg_inputs_outputs/svg_input/
    for the linedraw module to use as input

Returns:
    None
"""

import cv2
from rembg import remove
import os

# file_path = os.path.dirname(os.path.abspath(__file__))
# parent_directory = os.path.dirname(file_path)
# app_directory = os.path.dirname(parent_directory)
# output_path = os.path.join(app_directory, "data", "svg_inputs_outputs", "svg_input")

def remove_background(input_image, output_path, image_name):
   
    output_path = os.path.join(output_path, image_name)
    print("Removing background...")
    output_image = remove(input_image)
    print("Background removed!")
    print("Writing image...")
    cv2.imwrite(output_path, output_image)
    print("Image written!")
    
if __name__ == "__main__":
    pass