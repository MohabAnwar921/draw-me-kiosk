from random import *
import argparse
import os
import gc

from PIL import Image, ImageDraw, ImageOps

# Fix imports to use relative paths
from .filters import *
from .strokesort import *
from . import perlin
from .util import *
from core.params_parser import params

# Standalone functions for multiprocessing (outside the class to avoid pickle issues)
def process_contours_worker(image_data, alpha_mask_data, w, h, resolution, contour_simplify, no_cv):
    """Standalone function for contour processing in multiprocessing"""
    from PIL import Image
    
    # Recreate LineDrawer instance for this worker
    drawer = LineDrawer(resolution=resolution)
    drawer.contour_simplify = contour_simplify
    drawer.no_cv = no_cv
    
    # Recreate PIL images from data
    IM = Image.fromarray(image_data)
    alpha_mask = None
    if alpha_mask_data is not None:
        alpha_mask = Image.fromarray(alpha_mask_data)
    
    return drawer._process_contours(IM, alpha_mask, w, h)

def process_hatching_worker(image_data, alpha_mask_data, w, h, resolution, hatch_size, no_cv):
    """Standalone function for hatching processing in multiprocessing"""
    from PIL import Image
    
    # Recreate LineDrawer instance for this worker
    drawer = LineDrawer(resolution=resolution, hatch_size=hatch_size)
    drawer.no_cv = no_cv
    
    # Recreate PIL images from data
    IM = Image.fromarray(image_data)
    alpha_mask = None
    if alpha_mask_data is not None:
        alpha_mask = Image.fromarray(alpha_mask_data)
    
    return drawer._process_hatching(IM, alpha_mask, w, h)

class LineDrawer:
    def __init__(self, 
                 draw_contours = True, 
                 draw_hatch = params['draw_hatch'], 
                 resolution = params['resolution'],
                 hatch_size = params['hatch_size'],
                 svg_width = 1450,
                 svg_height = 1050):
        
        self.no_cv = False
        self.draw_contours = draw_contours
        self.draw_hatch = draw_hatch
        self.show_bitmap = False
        self.resolution = resolution
        self.hatch_size = hatch_size
        self.contour_simplify = 2
        self.svg_width = svg_width
        self.svg_height = svg_height
        
        # Try to import OpenCV if available
        try:
            import numpy as np
            import cv2
            self.cv2 = cv2
            self.np = np
        except:
            print("Cannot import numpy/openCV. Switching to NO_CV mode.")
            self.no_cv = True
            self.cv2 = None
            self.np = None
        print (f"lined draw was intialized with the following parameters: {self.no_cv} {self.draw_contours} {self.draw_hatch} {self.show_bitmap} {resolution} {self.hatch_size} {self.contour_simplify} {svg_width} {svg_height}" )
   
    def update_parameters(self,
                          draw_hatch,
                          resolution,
                          hatch_size,
                          svg_width,
                          svg_height):
        
        self.draw_hatch = draw_hatch
        self.resolution = resolution
        self.hatch_size = hatch_size
        self.svg_width = svg_width
        self.svg_height = svg_height
    
    def find_edges(self, IM, mask=None):
        print("finding edges...")
        if self.no_cv:
            #appmask(IM,[F_Blur])
            appmask(IM,[F_SobelX,F_SobelY])
        else:
            im = self.np.array(IM) 
            im = self.cv2.GaussianBlur(im,(3,3),0)
            im = self.cv2.Canny(im,100,200)
            IM = Image.fromarray(im)
        
        # Apply mask if provided (to ignore transparent areas)
        if mask:
            IM_masked = Image.new("L", IM.size, 0)
            IM_masked.paste(IM, mask=mask)
            return IM_masked.point(lambda p: p > 128 and 255)
        
        return IM.point(lambda p: p > 128 and 255)  

    def getdots(self, IM):
        print("getting contour points...")
        PX = IM.load()
        dots = []
        w,h = IM.size
        for y in range(h-1):
            row = []
            for x in range(1,w):
                if PX[x,y] == 255:
                    if len(row) > 0:
                        if x-row[-1][0] == row[-1][-1]+1:
                            row[-1] = (row[-1][0],row[-1][-1]+1)
                        else:
                            row.append((x,0))
                    else:
                        row.append((x,0))
            dots.append(row)
        return dots
        
    def connectdots(self, dots):
        print("connecting contour points...")
        contours = []
        for y in range(len(dots)):
            for x,v in dots[y]:
                if v > -1:
                    if y == 0:
                        contours.append([(x, y)])
                    else:
                        closest = -1
                        cdist = 100
                        for x0,v0 in dots[y-1]:
                            if abs(x0-x) < cdist:
                                cdist = abs(x0-x)
                                closest = x0

                        if cdist > 3:
                            contours.append([(x, y)])
                        else:
                            found = 0
                            for i in range(len(contours)):
                                if contours[i][-1] == (closest,y-1):
                                    contours[i].append((x,y,))
                                    found = 1
                                    break
                            if found == 0:
                                contours.append([(x,y)])
            for c in contours:
                if c[-1][1] < y-1 and len(c)<4:
                    contours.remove(c)
        return contours

    def getcontours(self, IM, sc=2, alpha_mask=None):
        print("generating contours...")
        try:
            IM = self.find_edges(IM, alpha_mask)
            IM1 = IM.copy()
            IM2 = IM.rotate(-90,expand=True).transpose(Image.FLIP_LEFT_RIGHT)
            
            dots1 = self.getdots(IM1)
            contours1 = self.connectdots(dots1)
            
            # Clear IM1 from memory
            del IM1
            gc.collect()
            
            dots2 = self.getdots(IM2)
            contours2 = self.connectdots(dots2)
            
            # Clear IM2 from memory
            del IM2
            gc.collect()

            for i in range(len(contours2)):
                contours2[i] = [(c[1],c[0]) for c in contours2[i]]    
            contours = contours1+contours2
            
            # Clear intermediate lists
            del contours1, contours2
            gc.collect()

            for i in range(len(contours)):
                for j in range(len(contours)):
                    if len(contours[i]) > 0 and len(contours[j])>0:
                        if distsum(contours[j][0],contours[i][-1]) < 8:
                            contours[i] = contours[i]+contours[j]
                            contours[j] = []

            for i in range(len(contours)):
                contours[i] = [contours[i][j] for j in range(0,len(contours[i]),8)]

            contours = [c for c in contours if len(c) > 1]

            for i in range(0,len(contours)):
                contours[i] = [(v[0]*sc,v[1]*sc) for v in contours[i]]

            for i in range(0,len(contours)):
                for j in range(0,len(contours[i])):
                    contours[i][j] = int(contours[i][j][0]+10*perlin.noise(i*0.5,j*0.1,1)),int(contours[i][j][1]+10*perlin.noise(i*0.5,j*0.1,2))

            # Final cleanup
            gc.collect()
            return contours
            
        except Exception as e:
            print(f"Error in contour generation: {e}")
            gc.collect()
            return []

    def hatch(self, IM, sc=16, alpha_mask=None):
        print("hatching...")
        try:
            PX = IM.load()
            w,h = IM.size
            lg1 = []
            lg2 = []
            
            # If we have an alpha mask, load it
            mask_pixels = None
            if alpha_mask:
                mask_pixels = alpha_mask.load()
            
            # Process in smaller chunks to reduce memory usage
            chunk_size = 100  # Process 100 rows at a time
            
            for y_start in range(0, h, chunk_size):
                y_end = min(y_start + chunk_size, h)
                
                for y0 in range(y_start, y_end):
                    for x0 in range(w):
                        # Skip if this pixel is transparent (check mask)
                        if alpha_mask and not mask_pixels[x0, y0]:
                            continue
                            
                        x = x0*sc
                        y = y0*sc
                        
                        try:
                            pixel_val = PX[x0,y0]
                            if pixel_val > 144:
                                pass
                            elif pixel_val > 64:
                                lg1.append([(x,y+sc/4),(x+sc,y+sc/4)])
                            elif pixel_val > 16:
                                lg1.append([(x,y+sc/4),(x+sc,y+sc/4)])
                                lg2.append([(x+sc,y),(x,y+sc)])
                            else:
                                lg1.append([(x,y+sc/4),(x+sc,y+sc/4)])
                                lg1.append([(x,y+sc/2+sc/4),(x+sc,y+sc/2+sc/4)])
                                lg2.append([(x+sc,y),(x,y+sc)])
                        except IndexError:
                            continue
                
                # Force garbage collection after each chunk
                if y_start % (chunk_size * 5) == 0:
                    gc.collect()

            lines = [lg1,lg2]
            for k in range(0,len(lines)):
                for i in range(0,len(lines[k])):
                    for j in range(0,len(lines[k])):
                        if lines[k][i] != [] and lines[k][j] != []:
                            if lines[k][i][-1] == lines[k][j][0]:
                                lines[k][i] = lines[k][i]+lines[k][j][1:]
                                lines[k][j] = []
                lines[k] = [l for l in lines[k] if len(l) > 0]
            lines = lines[0] + lines[1]

            for i in range(0,len(lines)):
                for j in range(0,len(lines[i])):
                    lines[i][j] = int(lines[i][j][0]+sc*perlin.noise(i*0.5,j*0.1,1)),int(lines[i][j][1]+sc*perlin.noise(i*0.5,j*0.1,2))-j
            
            # Final garbage collection
            gc.collect()
            return lines
            
        except Exception as e:
            print(f"Error in hatching: {e}")
            gc.collect()
            return []

    def _process_contours(self, IM, alpha_mask, w, h):
        """Helper method for processing contours in parallel"""
        try:
            # Scale the mask to match the resized image
            contour_mask = None
            if alpha_mask:
                contour_mask = alpha_mask.resize((self.resolution//self.contour_simplify, 
                                                self.resolution//self.contour_simplify*h//w), 
                                                Image.LANCZOS)
            
            contours = self.getcontours(IM.resize((self.resolution//self.contour_simplify, 
                                            self.resolution//self.contour_simplify*h//w)), 
                                    self.contour_simplify, contour_mask)
            
            # Force garbage collection after processing
            gc.collect()
            return contours
        except Exception as e:
            print(f"Error in contour processing: {e}")
            return []

    def _process_hatching(self, IM, alpha_mask, w, h):
        """Helper method for processing hatching in parallel"""
        try:
            # Scale the mask to match the resized image
            hatch_mask = None
            if alpha_mask:
                hatch_mask = alpha_mask.resize((self.resolution//self.hatch_size, 
                                            self.resolution//self.hatch_size*h//w), 
                                            Image.LANCZOS)
            
            hatches = self.hatch(IM.resize((self.resolution//self.hatch_size, 
                                        self.resolution//self.hatch_size*h//w)), 
                            self.hatch_size, hatch_mask)
            
            # Force garbage collection after processing
            gc.collect()
            return hatches
        except Exception as e:
            print(f"Error in hatch processing: {e}")
            return []

    def sketch(self, path, export_path=None):
        """
        Convert an image to a line drawing
        
        Args:
            path (str): Path to the input image
            export_path (str, optional): Path for the output SVG. If None, SVG is not saved.
            
        Returns:
            list: List of polylines used to create the drawing
        """
        try:
            IM = None
            possible = [path, "images/"+path, "images/"+path+".jpg", "images/"+path+".png", "images/"+path+".tif"]
            for p in possible:
                try:
                    IM = Image.open(p)
                    break
                except FileNotFoundError:
                    pass
            
            if IM is None:
                print("The Input File wasn't found. Check Path")
                return []
                
            w,h = IM.size
            print("Image size was read to be", (w, h))
            
            # Limit maximum image size to prevent memory issues on Raspberry Pi
            MAX_DIMENSION = 2000
            if max(w, h) > MAX_DIMENSION:
                scale_factor = MAX_DIMENSION / max(w, h)
                new_w = int(w * scale_factor)
                new_h = int(h * scale_factor)
                IM = IM.resize((new_w, new_h), Image.LANCZOS)
                w, h = new_w, new_h
                print(f"Resized image to {w}x{h} for performance")
            
            # Calculate aspect ratio
            aspect_ratio = float(w) / float(h)

            # Check if image has an alpha channel
            alpha_mask = None
            if IM.mode == 'RGBA':
                print("Image has transparency, processing alpha channel...")
                # Extract the alpha channel as a mask
                alpha_mask = IM.split()[3]
                # Convert to binary mask (255 for foreground, 0 for transparent areas)
                alpha_mask = alpha_mask.point(lambda p: p > 0 and 255)
            
            # Convert to grayscale for processing
            IM = IM.convert("L")
            IM = ImageOps.autocontrast(IM, 10)

            lines = []
            
            if self.draw_contours and self.draw_hatch:
                print("Processing contours and hatching in parallel...")
                from multiprocessing import Pool
                import numpy as np
                
                # Use half the CPU cores to avoid overwhelming the Pi
                num_processes = max(1, os.cpu_count() // 2)
                
                try:
                    with Pool(num_processes) as pool:
                        # Convert PIL images to numpy arrays for serialization
                        image_data = np.array(IM)
                        alpha_mask_data = np.array(alpha_mask) if alpha_mask else None
                        
                        # Process contours and hatching concurrently
                        print(f"Starting parallel processing with {num_processes} processes")
                        contour_future = pool.apply_async(process_contours_worker, 
                                                        (image_data, alpha_mask_data, w, h, 
                                                         self.resolution, self.contour_simplify, self.no_cv))
                        hatch_future = pool.apply_async(process_hatching_worker, 
                                                      (image_data, alpha_mask_data, w, h, 
                                                       self.resolution, self.hatch_size, self.no_cv))
                        
                        # Get results
                        contours = contour_future.get(timeout=300)  # 5 minute timeout
                        hatches = hatch_future.get(timeout=300)     # 5 minute timeout
                        
                        lines = contours + hatches
                        
                except Exception as e:
                    print(f"Parallel processing failed: {e}")
                    print("Falling back to sequential processing...")
                    # Fall back to sequential processing
                    if self.draw_contours:
                        lines += self._process_contours(IM, alpha_mask, w, h)
                    if self.draw_hatch:
                        lines += self._process_hatching(IM, alpha_mask, w, h)
            
            else:
                if self.draw_contours:
                    print("Processing contours...")
                    lines += self._process_contours(IM, alpha_mask, w, h)
                
                if self.draw_hatch:
                    print("Processing hatching...")
                    lines += self._process_hatching(IM, alpha_mask, w, h)

            # Sort lines for optimal drawing path
            lines = sortlines(lines)
            
            # Force garbage collection after heavy processing
            gc.collect()
            
            if self.show_bitmap:
                disp = Image.new("RGB", (self.resolution, self.resolution*h//w), (255, 255, 255))
                draw = ImageDraw.Draw(disp)
                for l in lines:
                    draw.line(l, (0, 0, 0), 5)
                disp.show()

            if export_path:
                try:
                    with open(export_path, 'w') as f:
                        f.write(self.makesvg(lines, self.svg_width, self.svg_height, aspect_ratio))
                    print(f"{len(lines)} strokes generated and saved to {export_path}")
                    print("done.")
                except IOError as e:
                    print(f"Error saving SVG file: {e}")
                    
            return lines
            
        except MemoryError:
            print("Memory error encountered. Try reducing resolution or image size.")
            gc.collect()
            return []
        except Exception as e:
            print(f"Unexpected error in sketch processing: {e}")
            gc.collect()
            return []

    def makesvg(self, lines, width=800, height=600, aspect_ratio=None):
        print("generating svg file...")
        
        # Determine viewBox dimensions
        viewBox_width = self.resolution * 0.5
        viewBox_height = self.resolution * 0.5
        
        if aspect_ratio:
            # Adjust either width or height to maintain aspect ratio
            if width / height > aspect_ratio:
                # Width is too big for the aspect ratio
                width = int(height * aspect_ratio)
            else:
                # Height is too big for the aspect ratio
                height = int(width / aspect_ratio)
            
            # Adjust viewBox dimensions to match aspect ratio
            if viewBox_width / viewBox_height > aspect_ratio:
                viewBox_width = viewBox_height * aspect_ratio
            else:
                viewBox_height = viewBox_width / aspect_ratio
        
        # Find the max coordinates to determine scaling
        max_x = 0
        max_y = 0
        
        for line in lines:
            for point in line:
                max_x = max(max_x, point[0] * 0.5)
                max_y = max(max_y, point[1] * 0.5)
        
        # Create SVG with specific dimensions
        out = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        out += f'viewBox="0 0 {viewBox_width} {viewBox_height}" preserveAspectRatio="xMidYMid meet">\n'
        
        # Add polylines
        for l in lines:
            l = ",".join([str(p[0]*0.5)+","+str(p[1]*0.5) for p in l])
            out += '<polyline points="'+l+'" stroke="black" stroke-width="2" fill="none" />\n'
        
        out += '</svg>'
        return out
    
    def visualize(self, lines):
        """
        Visualize the drawing lines using turtle graphics
        
        Args:
            lines (list): List of polylines to visualize
        """
        import turtle
        wn = turtle.Screen()
        t = turtle.Turtle()
        t.speed(0)
        t.pencolor('red')
        t.pd()
        for i in range(0,len(lines)):
            for p in lines[i]:
                t.goto(p[0]*640/1024-320,-(p[1]*640/1024-320))
                t.pencolor('black')
            t.pencolor('red')
        turtle.mainloop()
        
    def set_options(self, **kwargs):
        """
        Set drawing options
        
        Args:
            **kwargs: Arbitrary keyword arguments to set class properties
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                print(f"Warning: LineDrawer has no attribute '{key}'")
        return self

def main():
    parser = argparse.ArgumentParser(description='Convert image to vectorized line drawing for plotters.')
    parser.add_argument('-i','--input',dest='input_path',
        default='lenna',action='store',nargs='?',type=str,
        help='Input path')

    parser.add_argument('-o','--output',dest='output_path',
        default='output/out.svg',action='store',nargs='?',type=str,
        help='Output path.')

    parser.add_argument('-b','--show_bitmap',dest='show_bitmap',
        const=True, default=False, action='store_const',
        help="Display bitmap preview.")

    parser.add_argument('-nc','--no_contour',dest='no_contour',
        const=True, default=False, action='store_const',
        help="Don't draw contours.")
       
    parser.add_argument('-nh','--no_hatch',dest='no_hatch',
        const=True, default=False, action='store_const',
        help='Disable hatching.')

    parser.add_argument('--no_cv',dest='no_cv',
        const=True, default=False, action='store_const',
        help="Don't use openCV.")

    parser.add_argument('--hatch_size',dest='hatch_size',
        default=16, action='store', nargs='?', type=int,
        help='Patch size of hatches. eg. 8, 16, 32')
        
    parser.add_argument('--contour_simplify',dest='contour_simplify',
        default=2, action='store', nargs='?', type=int,
        help='Level of contour simplification. eg. 1, 2, 3')
    
    parser.add_argument('--svg_width',dest='svg_width',
        default=1200, action='store', nargs='?', type=int,
        help='Width of the output SVG in pixels')
        
    parser.add_argument('--svg_height',dest='svg_height',
        default=800, action='store', nargs='?', type=int,
        help='Height of the output SVG in pixels')
        
    parser.add_argument('--resolution',dest='resolution',
        default=3000, action='store', nargs='?', type=int,
        help='Resolution for processing')

    args = parser.parse_args()
    
    # Create line drawer instance
    drawer = LineDrawer()
    
    # Set options from command line arguments
    drawer.draw_contours = not args.no_contour
    drawer.draw_hatch = not args.no_hatch
    drawer.hatch_size = args.hatch_size
    drawer.contour_simplify = args.contour_simplify
    drawer.show_bitmap = args.show_bitmap
    drawer.no_cv = args.no_cv
    drawer.svg_width = args.svg_width
    drawer.svg_height = args.svg_height
    drawer.resolution = args.resolution
    
    # Process the image
    drawer.sketch(args.input_path, args.output_path)

if __name__ == "__main__":
    main()