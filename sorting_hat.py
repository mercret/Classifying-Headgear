from tkinter import *
from tkinter import messagebox
import pygame
import sys
import random
import math
import json
from enum import Enum

# audio files

stalling = ['ahright', 'difficult', 'itsallhere', 'rightok']
know = ['iknowjustwhattodo', 'iknow']

# House enum

class House(Enum):
    GRYFFINDOR = 1
    RAVENCLAW = 2
    SLYTHERIN = 3
    HUFFLEPUFF = 4

# global variables

RESOLUTION = (1920, 1080)

AUDIO_END0 = pygame.USEREVENT + 1
AUDIO_END1 = pygame.USEREVENT + 2

class HouseCrest:

    def __init__(self, image, audio, display_center, radius, theta, min_dim):
        self.image = image
        self.audio = audio
        self.max_width, self.max_height = image.get_rect().size
        self.min_width = min_dim
        self.min_height = min_dim
        self.width = self.min_width
        self.height = self.min_height
        self.small_image = pygame.transform.scale(
            self.image, (self.min_width, self.min_height))
        self.theta = theta
        self.center = (display_center[0] + radius*math.cos(self.theta),
                       display_center[1] + radius*math.sin(self.theta))
        self.fixed_center = self.center

    def fixcenter(self):
        self.fixed_center = self.center

    def rotate(self, radius, display_center, dtheta):
        self.theta += dtheta
        self.center = (display_center[0] + radius*math.cos(self.theta),
                       display_center[1] + radius*math.sin(self.theta))

    def expand(self, d):
        self.width += d*(self.max_width - self.min_width)
        self.height += d*(self.max_height - self.min_height)
        self.small_image = pygame.transform.scale(
            self.image, (round(self.width), round(self.height)))

    def shrink(self, d):
        self.width -= d*self.min_width
        self.height -= d*self.min_height
        self.small_image = pygame.transform.scale(
            self.image, (round(self.width), round(self.height)))

    def translate(self, display_center, d):
        self.center = (self.center[0] - d*(self.fixed_center[0] - display_center[0]),
                       self.center[1] - d*(self.fixed_center[1] - display_center[1]))

    def x(self):
        return round(self.center[0] - self.width / 2)

    def y(self):
        return round(self.center[1] - self.height / 2)

    def pos(self):
        return (self.x(), self.y())


def run(players):
    # init pygame
    pygame.init()
    pygame.mixer.init()
    # display surface
    display_surface = pygame.display.set_mode(RESOLUTION, flags=pygame.NOFRAME)
    pygame.display.set_caption('Sorting Hat')

    # get the player button frame
    player_list = PlayerList(players)

    # hide mouse cursor
    pygame.mouse.set_visible(False)
    # background
    background = pygame.transform.scale(pygame.image.load('video/background.png'), RESOLUTION)
    # geometry
    center = (RESOLUTION[0] / 2, RESOLUTION[1] / 2)
    min_dim = 400
    offset_from_border = 10
    radius = RESOLUTION[1] / 2 - (offset_from_border + min_dim / 2)
    # housecrest objects
    housecrests = {}
    for h in House:
        housecrests[h] = HouseCrest(pygame.image.load('video/wiki/{}.png'.format(h.name.lower())),
                                    pygame.mixer.Sound('audio/houses/{}.wav'.format(h.name.lower())),
                                    center, radius, math.pi*(h.value - 1)/2, min_dim)

    # settings
    step = 5  # ms (=interval between updates)
    zoom_duration = 1000  # ms
    reset_duration = 1000  # ms
    stalling_interval = 3000  # ms (=interval between 2 soundbites)
    rotation_speed = 2*math.pi/5  # rad/s
    dtheta = rotation_speed * step / 1000  # rad

    # load sorting hat sounds
    stalling_sounds = [pygame.mixer.Sound(
        'audio/stalling/{}.wav'.format(a)) for a in stalling]
    know_sounds = [pygame.mixer.Sound(
        'audio/know/{}.wav'.format(a)) for a in know]

    # create two channels
    channel0 = pygame.mixer.Channel(0)
    channel0.set_endevent(AUDIO_END0)
    channel1 = pygame.mixer.Channel(1)
    channel1.set_endevent(AUDIO_END1)

    # start background music
    # pygame.mixer.music.load('audio/background.mp3')
    # pygame.mixer.music.play(-1)

    # main loop
    while True:
        total_steps = 0
        rotate = True
        # rotate
        while rotate:
            display_surface.blit(background, (0, 0))

            for hc in housecrests.values():
                hc.rotate(radius, center, dtheta)
                display_surface.blit(hc.small_image, hc.pos())

            if total_steps*step % stalling_interval == 0 and not player_list.house:
                channel0.play(random.choice(stalling_sounds))

            if player_list.house and not channel0.get_busy() and not channel1.get_busy():
                channel1.play(random.choice(know_sounds))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    quit_callback()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        quit_callback()
                elif player_list.house and event.type == AUDIO_END1:
                    rotate = False

            # Draws the surface object to the screen.
            pygame.display.update()
            player_list.update()
            pygame.time.delay(step)
            total_steps += 1

        # zoom
        steps = zoom_duration / step
        d = 1 / steps
        # keep the original center of the housecrests
        for hc in housecrests.values():
            hc.fixcenter()
        channel1.play(housecrests[player_list.house].audio)
        for i in range(int(steps)):
            display_surface.blit(background, (0, 0))

            for hc in [hc for key, hc in  housecrests.items() if key != player_list.house]:
                hc.shrink(d)
                display_surface.blit(hc.small_image, hc.pos())
            
            housecrests[player_list.house].expand(d)
            housecrests[player_list.house].translate(center, d)
            display_surface.blit(housecrests[player_list.house].small_image, 
                                 housecrests[player_list.house].pos())

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    quit_callback()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        quit_callback()
            pygame.display.update()
            player_list.update()
            pygame.time.delay(step)

        # wait
        player_list.reset = False
        while not player_list.reset:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    quit_callback()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        quit_callback()
            pygame.display.update()
            player_list.update()
            pygame.time.delay(step)

        # reset
        steps = reset_duration / step
        d = 1 / steps
        for i in range(int(steps)):
            display_surface.blit(background, (0, 0))

            for hc in [hc for key, hc in  housecrests.items() if key != player_list.house]:
                hc.shrink(-d)
                display_surface.blit(hc.small_image, hc.pos())
            housecrests[player_list.house].expand(-d)
            housecrests[player_list.house].translate(center, -d)
            display_surface.blit(housecrests[player_list.house].small_image, 
                                 housecrests[player_list.house].pos())

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    quit_callback()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        quit_callback()
            pygame.display.update()
            player_list.update()
            pygame.time.delay(step)
        player_list.house = None


def quit_callback():
    pygame.quit()
    quit()

# Tk widgets

class PlayerList(Tk):

    def __init__(self, players):
        Tk.__init__(self)
        self.title('Sorting Hat')
        self.protocol("WM_DELETE_WINDOW", quit_callback)
        self.frame = Frame(self)
        self.frame.pack()
        # get widest button text
        max_width = 0
        for player in players:
            button_text = '{} {} ({})'.format(
                player['playerId'], player['name'], player['house'].name)
            if len(button_text) > max_width:
                max_width = len(button_text)
        for player in players:
            player_id = player['playerId']
            b = PlayerButtonFrame(self.frame, self, player_id,
                                  player['name'], player['house'], max_width)
            b.grid(row=(player_id-1) % 20, column=(player_id-1) // 20, sticky=EW)
        self.continue_button = Button(self.frame, text='Continue', command=self.continue_callback)
        self.continue_button.grid(row=20, columnspan=2, sticky='EW', padx=5, pady=5)
        self.reset = False
        self.house = None

    def continue_callback(self):
        self.reset = True

    def selection_callback(self, house):
        self.house = house

class PlayerButtonFrame(Frame):

    def __init__(self, master, player_list, player_id, name, house, width):
        Frame.__init__(self, master)
        self.player_list = player_list
        self.b1 = Button(self, text='{} {} ({})'.format(
            player_id, name, house.name), width=width, command=self.callback)
        self.b1.grid(row=0, column=0, padx=5, pady=5)
        self.b2 = Button(self, text='X', command=self.toggle)
        self.b2.grid(row=0, column=1, padx=5, pady=5)
        self.player_id = player_id
        self.name = name
        self.house = house

    def callback(self):
        if not self.player_list.house:
            print('{} {} gesorteerd in {}'.format(
                self.player_id, self.name, self.house.name))
            self.b1.config(state=DISABLED)
            self.player_list.selection_callback(self.house)

    def toggle(self):
        if self.b1['state'] == DISABLED:
            self.b1.config(state=NORMAL)
        elif self.b1['state'] == NORMAL:
            self.b1.config(state=DISABLED)
            

# main method

if __name__ == '__main__':
    json_file = sys.argv[1]
    f = open(json_file, 'r')
    js = json.load(f)
    f.close()
    # sort in houses
    # first use name of enum
    for player in js['players']:
        player['house'] = House((player['playerId'] - 1) % 4 + 1).name
    f = open(json_file, 'w')
    json.dump(js, f)
    f.close()
    # replace name with enum itself after written to file
    for player in js['players']:
        player['house'] = House((player['playerId'] - 1) % 4 + 1)
    # run main loop
    run(js['players'])
