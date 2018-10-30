from psychopy import visual, core, event, sound
from pyee import EventEmitter
import feedparser
import random
import os
import time
from ldrop import Ldrop
import glib

class Experiment(EventEmitter):
    def __init__(self):
        
        # run the superclass constructor
        EventEmitter.__init__(self)
        
        # constructor
        self.win = None
        self.draw_queue = []
        self.active_aois=[]
    def start_experiment(self):
        
        self.paused = False
        self.continued=False
        self.next=[]
        # parameters
        
        #AOIs
        self.xaois1=[-0.7,0.7,-0.7,0.7,0.0]
        self.yaois1=[-0.7,0.7,0.7,-0.7,0.0]
    
        #random.shuffle(self.aois)
        
        #Images and a start value
        self.imagedir = "images"

        #alternatively get information of image files (can also randomize the listed images)
        self.images = os.listdir(self.imagedir)
        #random.shuffle(self.images)
        self.image_number = 0

        #number of rounds and a start value
        self.rounds = 4
        self.round = 0

        #presentation times
        #self.stimulus_display_time = 2000
        waittime = 1.5 #s

        # window object
        self.res = [1024,768]
        win = visual.Window(self.res, monitor="testMonitor", units="norm",color=(-1, -1, -1))
        self.win = win

        print("Look at the screen")
        
        #active AOI
        self.active_aois=[]

        self.emit("start_collecting_data")
        glib.idle_add(self.intro)
        glib.idle_add(self.draw)
     
    def intro(self):
        self.draw_queue = []

        
        movieobject = self.load_movie(os.path.join(self.imagedir,"Intro.mkv"))
        
        print("intro")
        self.play_movie(movieobject, 0, 0, 1.8, 1.8)
        movieobject.draw()
        
     
        self.stimulus_display_time=50000
              
        self.play_movie(movieobject, 0, 0, 1.8, 1.8)
        movieobject.draw()
        self.draw_queue.append(movieobject)
        
        self.next= self.event1
        
        if self.continued:
            return
        else:
            glib.timeout_add(self.stimulus_display_time, self.event1) #defines onset asynchrony or delay

    def event1(self):
        self.emit('tag', {"tag":""})
        self.clear_draw_que()
        self.continued=False
        
        movieobject = self.load_movie(os.path.join(self.imagedir,"Lucky_straw.avi"))
        
        print("event1")
        x = self.xaois1[self.round]
        y = self.yaois1[self.round]
        self.play_movie(movieobject, x, y, 0.2, 0.2)
        movieobject.draw()
        self.draw_queue.append(movieobject)
     
        self.stimulus_display_time=2000      
        
        self.next= self.event2
        
        active_aois=[0,4, 0,6]
        
        if self.continued:
            return
        else:
            glib.timeout_add(self.stimulus_display_time, self.event2) #defines onset asynchrony or delay


    def event2(self):
        #self.continued=False
           
        #self.draw_queue = []
        self.continued=False



        if self.paused:
            glib.timeout_add(100, self.trial_start) #checks every 100 ms if paused
            return
        self.draw_queue = []

        self.emit('tag', {"tag":"calib"})

        x = self.xaois1[self.round]
        y = self.yaois1[self.round]

        stm = visual.ImageStim(win=self.win,
                                   image=os.path.join(self.imagedir,
                                                      "Target_straw.png"),
                                   pos=(x,y), size=0.2)
        stm.draw()
            # find out image dimensions
        self.draw_queue.append(stm)

#self.tag_callback({"tag":"trial_event2"}) #will be updated


# maps the limits to aoi
        lims_normalized = stm.size
        aoi = [x-lims_normalized[0]/2, x+lims_normalized[0]/2,
        y-lims_normalized[1]/2, y+lims_normalized[1]/2]
        print("event2")
        #print "aoi is " + str(aoi)

        self.stimulus_display_time=2000
        self.round += 1
        #self.image_number += 1
                    
        if self.round <= self.rounds:
            glib.timeout_add(self.stimulus_display_time, self.event1) #defines onset asynchrony or delay
        else:
            glib.timeout_add(self.stimulus_display_time, self.end) #defines onset asynchrony or delay
            #   self.experiment_cleanup()
                #here we could have a head positio checker that checks whether we continue...

    def end(self):
        self.emit("stop_collecting_data")
        self.experiment_cleanup()

 #####
    def on_data(self, dp):
        if self.win is not None:
            eye = visual.Circle(self.win, pos=(dp["right_gaze_point_on_display_area_x"]*2-1, -(dp["right_gaze_point_on_display_area_y"]*2-1)),
                            fillColor=[0.5,0.5,0.5], size=0.05, lineWidth=1.5)
        
            eye.draw()

        #active aoi check
        
        for a in self.active_aois:
            if dp["right_gaze_point_on_display_area_x"]<a[0] and dp["right_gaze_point_on_display_area_y"]>a[1]: #...is inside
                self.continued=True
                self.active_aois = []
                glib.idle_add(self.trial_event1)



    def draw(self):

        # draw screen
        for i in self.draw_queue:
            i.draw()

        self.win.flip()
        glib.timeout_add(50, self.draw)

#            self.win.flip()

    def on_stop(self):
        self.paused = True

    def on_continue(self):
        self.continued = True
        #self.draw_queue=[]

        glib.idle_add(self.next) 

    def clear_draw_que(self):
        for k in self.draw_queue:
            if k.__class__.__name__ == 'MovieStim3':
                k.seek(0)  # go start # errors some times
                k.pause()
            # k.autoDraw = False
            
            elif k.__class__.__name__ == 'SoundStim':
                k.stop()
            else:
                # imageobject
                k.autoDraw = False

        self.draw_queue = []

    def experiment_cleanup(self):

        # cleanup
        self.win.close()
        core.quit()

    def load_movie(self, filepath):
        #Load a moviefile to RAM tied to specified window.
        movieobject = visual.MovieStim3(self.win, filepath, loop=True)
        movieobject.units = "norm"
        return movieobject


    def play_movie(self, movieobject, x, y, width, height):
        #Start playing movie.
        # Transfer to psychopy coordinates (-1->1, 1->-1)
        # from normalized (0->1, 0->1)
        #p_x, p_y, width, height = utils.aoi_from_experiment_to_psychopy(aoi)
        
        movieobject.play()
        
        movieobject.pos = (x, y)
        movieobject.size = [width, height]
        movieobject.draw()
# stm.autoDraw = True


# start running here
exp = Experiment()

# create ldrop controller-instance
ldrop = Ldrop.Controller()

# use setter-functions to set details of the experiment
ldrop.set_experiment_id("test")
ldrop.set_callbacks(exp.start_experiment, exp.on_stop,
                    exp.on_continue, exp.on_data)

# make a subscription to experiment instance on ldrop to receive tags
#exp.tag_callback = ldrop.on_tag
ldrop.add_model(exp)

# autoadd mouse sensor if you have the sensor-module available
#ldrop.add_sensor('mouse')
ldrop.set_participant_id("jl")
ldrop.add_sensor('tobii')


# enable sensor-gui (optional)
ldrop.enable_gui()

# starts blocking
ldrop.run()
