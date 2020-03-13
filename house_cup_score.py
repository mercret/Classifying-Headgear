import pygame
import math
import sys
import json
from enum import Enum

RESOLUTION = (1920, 1080)


class House(Enum):
    GRYFFINDOR = 1
    RAVENCLAW = 2
    SLYTHERIN = 3
    HUFFLEPUFF = 4

HOUSE_COLORS = {House(1): (188, 7, 7), House(2): (73, 73, 221),
                House(3): (11, 140, 11), House(4): (247, 247, 51)}


class HouseCrest:

    def __init__(self, image, audio, display_center, min_dim, radius=0, theta=0):
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


class Hourglass:

    def __init__(self, image, center, min_dim, color, contour):
        self.image = image
        self.max_width, self.max_height = image.get_rect().size
        self.min_width = min_dim
        self.min_height = min_dim
        self.width = self.min_width
        self.height = self.min_height
        self.small_image = pygame.transform.scale(
            self.image, (self.min_width, self.min_height))
        self.center = center
        self.fixed_center = self.center
        self.color = color
        self.contour = contour
        scale = min_dim / self.max_width
        self.scaled_contour = [(scale*v[0], scale*v[1]) for v in self.contour]
        # self.scaled_contour = (self.scaled_contour[:len(self.scaled_contour)//2], self.scaled_contour[len(self.scaled_contour)//2:])
        self.max_d = 0

    def x(self):
        return round(self.center[0] - self.width / 2)

    def y(self):
        return round(self.center[1] - self.height / 2)

    def pos(self):
        return (self.x(), self.y())

    def points(self, d):
        contour = self.scaled_contour[round((1-min(d, self.max_d))*len(self.scaled_contour)//2):len(self.scaled_contour)//2] + \
                  self.scaled_contour[len(self.scaled_contour)//2:round((1+min(d, self.max_d))*len(self.scaled_contour)//2)]
        return [(round(v[0] + self.center[0] - self.width / 2), round(v[1] + self.center[1] - self.height / 2)) for v in contour]

class Score:

    def __init__(self, font, color, center, end_value):
        self.font = font
        self.color = color
        self.center = center
        self.end_value = end_value
        self.current_value = 0
        self.text = self.font.render(str(self.current_value), True, self.color)

    def x(self):
        return round(self.center[0] - self.text.get_width() / 2)

    def y(self):
        return round(self.center[1] - self.text.get_height() / 2)

    def pos(self):
        return (self.x(), self.y())

    def increment_value(self, d):
        self.current_value += d
        self.current_value = min(self.current_value, self.end_value)
        self.text = self.font.render(str(round(self.current_value)), True, self.color)


def run(house_scores):
    pygame.init()
    pygame.mixer.init()
    display_surface = pygame.display.set_mode(RESOLUTION, flags=pygame.NOFRAME)
    pygame.display.set_caption('House Cup Score')
    background = pygame.transform.scale(
        pygame.image.load('video/background.png'), RESOLUTION)
    hourglass_image = pygame.image.load('video/hourglass3.png')

    center = (RESOLUTION[0] / 2, RESOLUTION[1] / 2)
    min_dim = 400
    offset_from_border = 10
    radius = RESOLUTION[1] / 2 - (offset_from_border + min_dim / 2)

    # font
    font = pygame.font.SysFont("", 180)
    # contour
    contour_file = open('contour.json', 'r')
    contour = json.load(contour_file)
    contour_file.close()

    channel0 = pygame.mixer.Channel(0)
    tally_sound = pygame.mixer.Sound('audio/tally.wav')

    housecrests = {}
    hourglasses = {}
    scores = {}
    max_score = 0
    for h in House:
        # housecrests
        housecrests[h] = HouseCrest(pygame.image.load('video/wiki/{}.png'.format(h.name.lower())),
                                    pygame.mixer.Sound(
                                        'audio/houses/{}.wav'.format(h.name.lower())),
                                    center, min_dim)
        housecrests[h].center = ((2*(h.value - 1) + 1)
                                 * RESOLUTION[0] / 8, RESOLUTION[1] / 5)
        # hourglasses
        hourglass_center = ((2*(h.value - 1) + 1)*RESOLUTION[0] / 8, 3*RESOLUTION[1] / 5)
        hourglasses[h] = Hourglass(hourglass_image, hourglass_center, min_dim, HOUSE_COLORS[h], contour)
        # scores
        score_center = ((2*(h.value - 1) + 1)*RESOLUTION[0] / 8, RESOLUTION[1] - 100)
        scores[h] = Score(font, HOUSE_COLORS[h], score_center, house_scores[h])
        if house_scores[h] > max_score:
            max_score = house_scores[h]
    for h in House:
        hourglasses[h].max_d = house_scores[h] / max_score

    clock = pygame.time.Clock()
    frame_rate = 60
    # wait
    wait = True
    while wait:
        display_surface.blit(background, (0, 0))
        for hc in housecrests.values():
            display_surface.blit(hc.small_image, hc.pos())
        for hg in hourglasses.values():
            display_surface.blit(hg.small_image, hg.pos())
        for sc in scores.values():
            display_surface.blit(sc.text, sc.pos())

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_callback()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    quit_callback()
                elif event.key == pygame.K_SPACE:
                    wait = False
        pygame.display.update()
        clock.tick(frame_rate)

    fill_duration = 5000 # ms
    d = max_score / fill_duration
    # fill
    channel0.play(tally_sound)
    elapsed_time = 0
    while elapsed_time < fill_duration:
        display_surface.blit(background, (0, 0))
        for hc in housecrests.values():
            display_surface.blit(hc.small_image, hc.pos())
        for hg in hourglasses.values():
            try:
                pygame.draw.polygon(display_surface, hg.color, hg.points(elapsed_time/fill_duration))
            except ValueError:
                pass
            display_surface.blit(hg.small_image, hg.pos())
        for sc in scores.values():
            sc.increment_value(d*clock.get_time())
            display_surface.blit(sc.text, sc.pos())

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_callback()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    quit_callback()
                elif event.key == pygame.K_SPACE:
                    wait = False
        pygame.display.update()
        elapsed_time += clock.get_time()
        clock.tick(frame_rate)

    channel0.stop()
    # wait
    wait = True
    while wait:
        display_surface.blit(background, (0, 0))
        for hc in housecrests.values():
            display_surface.blit(hc.small_image, hc.pos())
        for hg in hourglasses.values():
            pygame.draw.polygon(display_surface, hg.color, hg.points(d*fill_duration))
            display_surface.blit(hg.small_image, hg.pos())
        for sc in scores.values():
            display_surface.blit(sc.text, sc.pos())

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_callback()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    quit_callback()
                elif event.key == pygame.K_SPACE:
                    wait = False
        pygame.display.update()
        clock.tick(frame_rate)


def quit_callback():
    pygame.quit()
    quit()

if __name__ == "__main__":
    json_file = sys.argv[1]
    f = open(json_file, 'r')
    js = json.load(f)
    f.close()
    house_scores = {}
    for house, score in js.items():
        house_scores[House[house]] = score
    print(house_scores)
    run(house_scores)