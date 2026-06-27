from pyaxidraw import axidraw
import time

def get_time_estimate(drawing_file_path):
    ad = axidraw.AxiDraw()
    ad.options.model = 2
    ad.plot_setup(drawing_file_path)
    ad.options.report_time = True
    ad.options.preview = True
    ad.plot_run()
    time_estimate_in_seconds = ad.time_estimate
    time_estimate_in_minutes = time_estimate_in_seconds / 60
    return round(time_estimate_in_minutes)  # Round to one decimal place

def toggle_pen(ad: object):
    ad = axidraw.AxiDraw()
    ad.options.model = 2  # Set the model to AxiDraw CE/A3
    
    ad.plot_setup()
    ad.options.mode = 'toggle'
    ad.plot_run()

def start_or_resume_drawing(ad: object, file_path: str, status, progress): #TODO: Handle resuming from home or reset progress if so
    if status == "paused":
        print ("Resuming drawing from home position...")
        ad.plot_setup(progress)
        ad.options.mode = "res_home"
        progress = ad.plot_run(True)
        if ad.errors.code == 102: # Physical pause button pressed
            status = "paused" 
        else:
            status = "finished"
        go_home(ad)
    else:
        ad.plot_setup(file_path)
        progress = ad.plot_run(True)
        if ad.errors.code == 102:
            status = "paused"
        else:
            status = "finished"
        go_home(ad)

    return progress, status


def toggle_manual_align(ad: object):
    ad.plot_setup()
    ad.options.mode = 'align'
    ad.plot_run()
    
def go_home(ad: object): # Returns the pen to the position where it started at
    ad.plot_setup()
    ad.options.mode = 'manual'
    ad.options.manual_cmd = 'walk_home'
    ad.plot_run()
