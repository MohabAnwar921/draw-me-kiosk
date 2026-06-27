# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

# Get the project root directory
project_root = os.path.dirname(os.path.abspath(SPEC))
app_dir = os.path.join(project_root, 'app')

# Collect all data files and assets
datas = []

# Add GUI assets (PNG files for buttons, icons, etc.)
gui_assets = []
for root, dirs, files in os.walk(os.path.join(app_dir, 'GUI')):
    for file in files:
        if file.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico')):
            src_path = os.path.join(root, file)
            rel_path = os.path.relpath(src_path, app_dir)
            dest_path = os.path.dirname(rel_path)
            gui_assets.append((src_path, dest_path))

datas.extend(gui_assets)

# Add configuration files
config_files = [
    (os.path.join(app_dir, 'params.xml'), '.'),
]
datas.extend(config_files)

# Add static data files (watermark SVG, etc.)
static_files = []
static_dir = os.path.join(app_dir, 'data', 'static')
if os.path.exists(static_dir):
    for root, dirs, files in os.walk(static_dir):
        for file in files:
            if file.endswith(('.svg', '.xml', '.json', '.txt')):
                src_path = os.path.join(root, file)
                rel_path = os.path.relpath(src_path, app_dir)
                dest_path = os.path.dirname(rel_path)
                static_files.append((src_path, dest_path))

datas.extend(static_files)

# Add linedraw module data files
linedraw_dir = os.path.join(app_dir, 'core', 'linedraw')
linedraw_files = []
for root, dirs, files in os.walk(linedraw_dir):
    for file in files:
        if file.endswith(('.txt', '.md', 'LICENSE')):
            src_path = os.path.join(root, file)
            rel_path = os.path.relpath(src_path, app_dir)
            dest_path = os.path.dirname(rel_path)
            linedraw_files.append((src_path, dest_path))

datas.extend(linedraw_files)

# Ensure required directories exist
data_dirs = [
    (os.path.join(app_dir, 'data', 'svg_inputs_outputs', 'svg_input'), 'data/svg_inputs_outputs/svg_input'),
    (os.path.join(app_dir, 'data', 'svg_inputs_outputs', 'svg_output'), 'data/svg_inputs_outputs/svg_output'),
    (os.path.join(app_dir, 'data', 'svg_window_preview'), 'data/svg_window_preview'),
    (os.path.join(app_dir, 'core', 'linedraw', 'images'), 'core/linedraw/images'),
    (os.path.join(app_dir, 'core', 'linedraw', 'output'), 'core/linedraw/output'),
]

for src_dir, dest_dir in data_dirs:
    if not os.path.exists(src_dir):
        os.makedirs(src_dir, exist_ok=True)
        placeholder_file = os.path.join(src_dir, '.placeholder')
        with open(placeholder_file, 'w') as f:
            f.write("# Directory placeholder")
    datas.append((src_dir, dest_dir))

# Hidden imports
hiddenimports = [
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'numpy',
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'rembg',
    'cairosvg',
    'pyaxidraw',
    'axidraw',
    'cv2',
    'multiprocessing',
    'threading',
    'queue',
    'xml.etree.ElementTree',
]

a = Analysis(
    [os.path.join(app_dir, 'app.py')],
    pathex=[project_root, app_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy.stats',
        'scipy.spatial',
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='thd-draw',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='thd-draw'
)
