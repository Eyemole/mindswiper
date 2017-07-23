import argparse
import math
import time
import socket
import os.path
import sys
import os
import threading
import queue
import multiprocessing
import numpy as np
import pynder
import itertools
from PIL import Image
import requests
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.patheffects as PathEffects
from datetime import datetime
from pythonosc import dispatcher as dp
from pythonosc import osc_server
import matplotlib.animation as animation
import matplotlib.transforms as mtransforms
from matplotlib.patches import FancyBboxPatch


IMAGE_DIR = "images"
REFRESH_RATE = 0.1
NUM_RECORDINGS = 10
ANIMATION_FRAMES = 5
THRESHOLD = 0.9
IMG_SIZE = [640, 640]
LIKE_IMG = mpimg.imread("like.png")
NOPE_IMG = mpimg.imread("nope.png")
interval = int(IMG_SIZE[1]/ANIMATION_FRAMES)


ACCESS_TOKEN = # Your Tinder acess token. To get it, follow this link: https://www.facebook.com/v2.6/dialog/oauth?redirect_uri=fb464891386855067%3A%2F%2Fauthorize%2F&state=%7B%22challenge%22%3A%22q1WMwhvSfbWHvd8xz5PT6lk6eoA%253D%22%2C%220_auth_logger_id%22%3A%2254783C22-558A-4E54-A1EE-BB9E357CC11F%22%2C%22com.facebook.sdk_client_state%22%3Atrue%2C%223_method%22%3A%22sfvc_auth%22%7D&scope=user_birthday%2Cuser_photos%2Cuser_education_history%2Cemail%2Cuser_relationship_details%2Cuser_friends%2Cuser_work_history%2Cuser_likes&response_type=token%2Csigned_request&default_audience=friends&return_scopes=true&auth_type=rerequest&client_id=464891386855067&ret=login&sdk=android&logger_id=54783C22-558A-4E54-A1EE-BB9E357CC11F#_=_
FB_ID = # Your Facebook ID here. Find out what your ID is on 
SAVE_NAME = 'img.png'


class EEGData():

    def __init__(self):
        self.lock = multiprocessing.Lock()
        self.currx = []
        self.curry = []
        self.currmax = 0
        self.lastmax = 1

    def add_data(self, new_data):

        if self.currx == []:
            self.currx = [0]
        else:
            self.currx.append(self.currx[-1] + 1)
        self.curry.append(new_data)
        self.currmax = new_data
        if self.currmax > self.lastmax:
            self.lastmax = self.currmax

    def press(self,event):

        if event.key == 'q':
            sys.exit()


def setup_server(data):
    parser = argparse.ArgumentParser()
    ip = socket.gethostbyname(socket.gethostname())
    parser.add_argument("--ip",
                        default=str(ip),
                        help="The ip to listen on")
    parser.add_argument("--port",
                        type=int,
                        default=5000,
                        help="The port to listen on")
    args = parser.parse_args()

    dispatcher = dp.Dispatcher()
    dispatcher.map("/debug", print)
    dispatcher.map("/muse/eeg", lambda addr, args, ch1, ch2, ch3, ch4, ch5: eeg_handler(addr, args, ch1, ch2, ch3, ch4, ch5, data), "EEG")

    server = osc_server.ThreadingOSCUDPServer(
        (args.ip, args.port), dispatcher)
    server.socket.setblocking(0)
    print("Serving on {}".format(server.server_address))
    return server

def eeg_handler(unused_addr, args, ch1, ch2, ch3, ch4, ch5, eeg):

    data = [ch1, ch2, ch3, ch4]
    currmax = np.nanmean(data)
    eeg.add_data(currmax)


def start_server(data):
    t = threading.Thread(target=setup_server(data))
    t.setDaemon(True)
    t.start()

if __name__ == "__main__":
    data = EEGData()
    server = setup_server(data)
    plt.ion()
    session = pynder.Session(facebook_id = FB_ID, facebook_token = ACCESS_TOKEN)

    fig = plt.figure()
    ax = plt.Axes(fig, [0., 0.2, 1., 1.])
    ax1 = plt.Axes(fig, [0., 0., 1., 0.2])
    ax.set_axis_off()
    ax1.set_axis_off()
    fig.add_axes(ax)
    fig.add_axes(ax1)
    fig.canvas.mpl_connect('key_press_event', data.press)

    img = None

    count_trials = 0
    like = False
    while 1:

        # Record the data 

        num_requests = 0
        while num_requests < NUM_RECORDINGS:
            server.handle_request()
            graph = ax1.plot(data.currx, data.curry)
            fig.canvas.draw()
            fig.canvas.flush_events() 
            num_requests = num_requests + 1

        # Clear last graph
        try:
            graph.remove()
        except Exception as e:
            pass

        data.currx = []
        data.curry = []
        ax1.cla()
        fig.canvas.draw()
        fig.canvas.flush_events() 

        # Swipe left or right 

        threshold_data = [data.lastmax*THRESHOLD for x in range(NUM_RECORDINGS)]
        t_x = range(NUM_RECORDINGS)
        threshold_graph = ax1.plot(t_x, threshold_data, color = 'r', linewidth = 3)

        if count_trials > 0: # Don't swipe if no pictures had been shown yet 

            if data.currmax/data.lastmax >= THRESHOLD: # If maximum signal exceeds threshold, swipe right 
                like = True
            else:
                like = False
            if like:
                swipe = ax.imshow(LIKE_IMG, transform=ax.transAxes, extent = [0,1,0,1])
            else:
                swipe = ax.imshow(NOPE_IMG, transform=ax.transAxes, extent = [0,1,0,1])
            fig.canvas.draw()
            fig.canvas.flush_events() 
            now = datetime.now()
            while (datetime.now() - now).total_seconds() <= 0.1:
                pass
            data.currmax = 0
            data.currx = []
            data.curry = []

        ax.cla()
        ax.set_axis_off()

        # Get next picture to show 
        try:
            users = session.nearby_users() # returns a iterable of users nearby

            for user in itertools.islice(users, 1):  

                # Clear all previous images 

                try:
                    txt.remove()
                except Exception as e:
                    pass
                try:
                    biotxt.remove()
                except Exception as e:
                    pass
                try:
                    swipe.remove()
                except Exception as e:
                    pass

                # Temporarily store the profile picture 
                pic_url = user.get_photos()[1]
                response = requests.get(pic_url)
                img = Image.open(BytesIO(response.content)).convert("RGBA")
                img = img.resize(IMG_SIZE, Image.ANTIALIAS)
                img.save(SAVE_NAME)
                img = mpimg.imread(SAVE_NAME)
                imgplot = ax.imshow(img, transform = ax.transAxes, extent = [0,1,0,1])

                # Print the name and age 
                txt = ax.text(0.0, 0.25, s = (user.name + ", " + str(user.age)), transform=ax.transAxes, color = 'w', fontsize=16, fontweight='bold', path_effects=[PathEffects.withStroke(linewidth=3, foreground="k")])
                
                # Print the bio if it is available 
                try:
                    biotext = ax.text(0.0, 0.20, s = (user.bio), transform=ax.transAxes, color = 'k', fontsize=11, wrap = True, fontweight='bold', verticalalignment = 'top',  path_effects=[PathEffects.withStroke(linewidth=3, foreground="w")])
                except Exception as e:
                    pass
                

        except Exception as e:
            print(str(e))

        count_trials += 1
        fig.canvas.draw()
        fig.canvas.flush_events() 