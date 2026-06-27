"""
SVG Watermark Embedder

Simple module to embed one SVG file into another at specified corners.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Tuple, Optional
import re
from core.params_parser import params


def get_svg_dimensions_and_scale(svg_root: ET.Element) -> Tuple[float, float, float, float]:
    """Extract width, height, and effective scale from SVG root element."""
    width = svg_root.get('width')
    height = svg_root.get('height')
    viewBox = svg_root.get('viewBox')
    
    print(f"SVG attributes - width: {width}, height: {height}, viewBox: {viewBox}")
    
    # Default values
    display_w, display_h = 400.0, 400.0
    viewbox_w, viewbox_h = 400.0, 400.0
    
    # Get display dimensions (width/height attributes)
    if width and height:
        try:
            display_w = float(re.sub(r'[^0-9.-]', '', str(width)))
            display_h = float(re.sub(r'[^0-9.-]', '', str(height)))
            print(f"Display dimensions: {display_w} x {display_h}")
        except:
            pass
    
    # Get viewBox dimensions
    if viewBox:
        try:
            parts = viewBox.strip().split()
            if len(parts) == 4:
                viewbox_w, viewbox_h = float(parts[2]), float(parts[3])
                print(f"ViewBox dimensions: {viewbox_w} x {viewbox_h}")
        except:
            pass
    else:
        # If no viewBox, assume it matches display dimensions
        viewbox_w, viewbox_h = display_w, display_h
    
    # Calculate scale factors
    scale_x = display_w / viewbox_w if viewbox_w > 0 else 1.0
    scale_y = display_h / viewbox_h if viewbox_h > 0 else 1.0
    
    print(f"Calculated scales - X: {scale_x}, Y: {scale_y}")
    
    return display_w, display_h, scale_x, scale_y


def get_svg_dimensions(svg_root: ET.Element) -> Tuple[float, float]:
    """Extract width and height from SVG root element (legacy function)."""
    display_w, display_h, _, _ = get_svg_dimensions_and_scale(svg_root)
    return display_w, display_h


def embed_watermark(main_svg_path: str, 
                   water_mark_path: str, 
                   corner: str = params['watermark_position'], 
                   margin: int = 10,
                   scale: float = 1.0,
                   output_path: Optional[str] = None) -> str:
    """
    Embed one SVG file into another at the specified corner.
    
    Args:
        main_svg_path: Path to the main SVG file
        water_mark_path: Path to the SVG file to embed as watermark
        corner: Corner position ("Top left", "Top right", "Bottom left", "Bottom right")
        margin: Margin from the corner in pixels
        scale: Scale factor for the watermark (relative to original size)
        output_path: Output path for the resulting SVG. If None, overwrites main_svg_path
        
    Returns:
        str: Path to the output SVG file
    """
    print(f"Embedding watermark at {corner}, margin={margin}, scale={scale}")
    
    # Register namespace
    ET.register_namespace('', "http://www.w3.org/2000/svg")
    
    # Parse main SVG
    main_tree = ET.parse(main_svg_path)
    main_root = main_tree.getroot()
    
    # Parse watermark SVG  
    watermark_tree = ET.parse(water_mark_path)
    watermark_root = watermark_tree.getroot()
    
    # Get dimensions and scale information
    print("Main SVG:")
    main_display_w, main_display_h, main_scale_x, main_scale_y = get_svg_dimensions_and_scale(main_root)
    print("Watermark SVG:")
    watermark_w, watermark_h = get_svg_dimensions(watermark_root)
    
    # Calculate compensation scale to counteract host scaling
    # We want the watermark to appear at its original size relative to the display
    compensation_scale_x = 1.0 / main_scale_x if main_scale_x != 0 else 1.0
    compensation_scale_y = 1.0 / main_scale_y if main_scale_y != 0 else 1.0
    
    # Apply user-requested scale
    final_scale_x = scale * compensation_scale_x
    final_scale_y = scale * compensation_scale_y
    
    print(f"Compensation scales - X: {compensation_scale_x}, Y: {compensation_scale_y}")
    print(f"Final scales - X: {final_scale_x}, Y: {final_scale_y}")
    
    # Calculate actual watermark size in the host's coordinate system
    actual_w = watermark_w * final_scale_x
    actual_h = watermark_h * final_scale_y
    print(f"Actual watermark size in host coordinates: {actual_w} x {actual_h}")
    
    # Calculate position in the host's viewBox coordinate system
    # We need to work in viewBox coordinates, not display coordinates
    viewbox_w = main_display_w / main_scale_x
    viewbox_h = main_display_h / main_scale_y
    
    # Adjust margin to viewBox scale
    viewbox_margin_x = margin / main_scale_x
    viewbox_margin_y = margin / main_scale_y
    
    if corner == "Top left":
        x = viewbox_margin_x
        y = viewbox_margin_y
    elif corner == "Top right":
        x = max(0, viewbox_w - actual_w - viewbox_margin_x)
        y = viewbox_margin_y
    elif corner == "Bottom left":
        x = viewbox_margin_x
        y = max(0, viewbox_h - actual_h - viewbox_margin_y)
    elif corner == "Bottom right":
        x = max(0, viewbox_w - actual_w - viewbox_margin_x)
        y = max(0, viewbox_h - actual_h - viewbox_margin_y)
    else:
        x, y = viewbox_margin_x, viewbox_margin_y
    
    print(f"Calculated position in viewBox coordinates: x={x}, y={y}")
    
    # Create a new group element for the watermark
    ns = {'svg': 'http://www.w3.org/2000/svg'}
    watermark_group = ET.Element('{http://www.w3.org/2000/svg}g')
    watermark_group.set('id', f"watermark_{Path(water_mark_path).stem}")
    
    # Set transform - translate to position, then scale with compensation
    if final_scale_x == final_scale_y:
        # Uniform scaling
        transform = f"translate({x},{y}) scale({final_scale_x})"
    else:
        # Non-uniform scaling
        transform = f"translate({x},{y}) scale({final_scale_x},{final_scale_y})"
    
    watermark_group.set('transform', transform)
    print(f"Transform: {transform}")
    
    # Copy all child elements from watermark to the group
    # Use a simple approach - just copy all non-SVG root elements
    for child in watermark_root:
        # Create a copy of the child element
        child_copy = ET.SubElement(watermark_group, child.tag, child.attrib)
        child_copy.text = child.text
        child_copy.tail = child.tail
        
        # Copy all children recursively
        for subchild in child:
            child_copy.append(subchild)
    
    # Add the watermark group to the main SVG
    main_root.append(watermark_group)
    
    # Write the result
    if output_path is None:
        output_path = main_svg_path
    
    # Write with proper XML declaration
    main_tree.write(output_path, encoding='utf-8', xml_declaration=True)
    
    print(f"Watermark embedded successfully at ({x}, {y}) with compensation scaling")
    return output_path