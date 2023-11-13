import pygame
import time
import math
from New_Vector2D import Vector2D
from Particle import Particle
from Particle_Manager import Particle_Manager

pygame.init()
CLOCK = pygame.time.Clock()


#CONSTANTS

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

FPS = 120

SLOW_TIME_BY = 1

NUM_PARTICLES = 100

VERTICAL_SPAWN = True

GRAVITY = False
REPULSE = True

CONTAINER = (200, 200)


# Calculated Variables
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
liquid = Particle_Manager(num_particles=NUM_PARTICLES, radius=5, x_bounds=CONTAINER[0]/2, y_bounds=CONTAINER[1]/2, gravity=GRAVITY, repulse=REPULSE, vertical_spawn=VERTICAL_SPAWN)

now = 0
prev_time = None
test_length = FPS * 30

run = True

# Main Loop
while run:

    CLOCK.tick(FPS)

    now = time.time()

    if not prev_time:
        prev_time = now

    dt = now - prev_time
    prev_time = now

    dt = dt / SLOW_TIME_BY

    screen.fill((230, 230, 230))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    liquid.update(screen=screen, dt=dt)

    pygame.display.update()

    test_length -= 1

    if test_length < 0:
        run = False

    #run = False
