import pygame
import time
import math
from New_Vector2D import Vector2D
from Particle import Particle
from Particle_Manager import Particle_Manager
from Button import Button
from Dashboard import Dashboard

def update_container_settings(p_manager, grav_btn):
    p_manager.set_gravity(grav_btn.active)


btn1 = Button(10, 10, 100, 40, (0, 0, 200), 'Gravity', True)

dash = Dashboard(600, 0, 200, 800)

dash.add_element(btn1)

pygame.init()
CLOCK = pygame.time.Clock()


#CONSTANTS

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

FPS = 120

SLOW_TIME_BY = 1

NUM_PARTICLES = 2

VERTICAL_SPAWN = True

GRAVITY = False
REPULSE = True

CONTAINER = (200, 200)


# Calculated Variables
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Liquid Simulator")
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

        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()

            dash.check_click(pos)

        if event.type == pygame.MOUSEBUTTONUP:
            dash.reset_clicked_elements()

    update_container_settings(liquid, btn1)

    dash.render(screen=screen)

    liquid.update(screen=screen, dt=dt)

    pygame.display.update()

    test_length -= 1

    if test_length < 0:
        run = False

    #run = False
