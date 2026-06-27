# Draw me kiosk

<table align="center">
  <tr>
    <td align="center">
      <img src="https://github.com/user-attachments/assets/b5360ff8-3281-4166-888f-7f6591f00801" alt="Image" width="1000" height="auto">
    </td>
    <td align="center">
      <video src="https://github.com/user-attachments/assets/b18e50fe-1e17-4059-aef0-fc1431f05e84" width="400"></video>
    </td>
  </tr>
</table>   

# Introduction

This application was meant to be on a raspberry Pi + A PI global shutter camera module that launches a GUI window where the user can take a photo, remove its background and redraws the image as an SVG line draw then allows the user to draw that image on paper using an AxiDraw C3/A3 machine.

# Software dependencies and hardware

This app was built on RaspiOS 12 "Bookworm" x64, python 3.11.2 
So for usage or contribution stay within python 3.11.xx
The app uses picamera2 v0.3.27 so 0.3.xx is advised.

Python packages:
- Numpy 1.24.2
- rembg[cpu] 2.0.66
- cairosvg 2.8.2
- AxiDraw python API 3.9.6 
	- Documentation [here](https://axidraw.com/doc/py_api/#introduction)

## Hardware setup

- Raspberry pi 4
- PI Global shutter camera module
- AxiDraw C3/A3
- JOY-IT RB-LCD10-2 TFT-LED Monitor
	- Instructions for enabling the touch functionality and calibration are available in [English](https://joy-it.net/files/files/Produkte/RB-LCD10-2/RB-LCD-10-2_Manual_A6_2024-05-23.pdf) and [German](https://joy-it.net/files/files/Produkte/RB-LCD10-2/RB-LCD-10-2_Anleitung_A6_2024-05-23.pdf) more information can be found in the [official product page](https://joy-it.net/de/products/RB-LCD-10-2).
# Installation for running the source files

This project uses the RasperryPI global shutter camera module which is only interfaced by the Picamera2 python package and according to the developers' documentation it is recommended to install that specific package through apt, more information in https://github.com/raspberrypi/picamera2 and https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf.

RaspiOS 12 Bookworm x64 images comes the `python3-picamera2` package pre-installed

So first check if it exists on your system by running:
``` bash
apt list | grep picamera
```

Look for python3-picamera2 if you find 0.3.27 or 0.3.xx That should work

Otherwise try to install it with
``` bash
sudo apt update
sudo apt install python3-picamera2
```

Once that is done clone the repository and create a new virtual environment that inherits the system site packages and install the rest with pip

``` bash
git clone https://github.com/MohabAnwar921/draw-me-kiosk.git
cd thd-draw
```

``` bash
python -m venv .venv --system-site-packages
```

Activate the environment
``` bash
source .venv/bin/activate
```

Install the rest
``` bash
pip install -r requirements.txt
```

To run the app
``` bash
python app/app.py
```

Note that upon the first time running the app and calling the rembg function an initialization process will take place.

# Admin settings

- Within the app's directory the **params.xml** parameters file allows the admin to set some default values and settings and some user options. Deleting or tampering with the file's structure may affect the program's functionality.
- In ./core/ **indexes.txt** can be found this file is a dictionary that keeps track previous jobs and their statuses, it is designed to be both human and machine readable and is updated by the program its content is reflected in the work queue menu, deleting or tampering with this file will not affect the programs functionality but might cause a loss or miss information of the session's queue data.

# Functionality and workflow

- The GUI has 3 windows **Capture window, Drawing (SVG) window, Control (Queue) window**
- The app launches in the **Capture window** allowing the user to take a picture they can either take it now or with a 5 or 10 seconds delay.
- Automatically after a capture the app will transition to the **Drawing (SVG) window** where the user can adjust some of the line sketch parameters.
	- These parameters found are:
		- Resolution: The higher this value the more detail the sketch has.
		- Toggle hatch: Toggles the hatch lines ON or OFF.
		- Hatch line size: The higher this value is, the more refined the hatch lines will be.
		- Canvas size toggle: Allows the user to pick a canvas paper size.
			- Users may choose between A3, A4, A5 and A6 (Always in landscape).
	- The default values as well as their upper and lower limits can be adjusted in **params.xml**.
- The estimated drawing time is displayed on the top of the page if it exceeds a set number of minutes the process will not proceed the user then can either adjust the sketch parameters or take a new image.
- Then the user then can click on "Save and queue", that will add the sketch in the queue window, then the app automatically will go back to the **Capture window**.
- The **Control (Queue) window** is accessible via the play button on the top left there the sketch requests are shown on a list on the left side and on the bottom side a button ribbon allows the admin to delete jobs, display a preview, start a drawing, toggle the AxiDraw's pen position up or down.
- To stop the drawing and return the pen into the start position, press on the physical button found on the AxiDraw itself.

# Adding a watermark
To add a watermark on each drawing replace `app/data/static/thd_watermark.svg` with your transperant background .svg file with 350x75 pixels

# Notes on the "build.spec" file

- This file was created to build the project as binary via **pyinstaller** and is not tested yet.
