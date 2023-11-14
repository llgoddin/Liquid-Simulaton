import pygame
import time
import math
from New_Vector2D import Vector2D
from Particle import Particle
from Particle_Manager import Particle_Manager
from Button import Button
from Dashboard import Dashboard

def update_container_settings(p_manager, dash):
    for element in dash.get_elements():
        match element.func_str:
            case 'Gravity':
                p_manager.set_gravity(element.active)

            case 'Repulse':
                p_manager.set_repulse(element.active)

            case '+ Particle':
                if element.get_clicked():
                    p_manager.spawn_particle()

            case '- Particle':
                if element.get_clicked():
                    p_manager.delete_particle()

            #TO DO - IMPLEMENT
            case '+ Container Width':
                #p_manager.increase_container_width()
                continue
            case '- Container Width':
                #p_manager.decrease_container_width()
                continue
            case '+ Container Height':
                #p_manager.increase_container_height()
                continue
            case '- Container Height':
                #p_manager.decrease_container_height()
                continue
            case '+ Repulse Force':
                #p_manager.increase_repulse()
                continue
            case '- Repulse Force':
                #p_manager.decrease_repulse()
                continue


grav_btn = Button(10, 10, 100, 40, (0, 0, 200), 'Gravity', True, 'Gravity')
repulse_btn = Button(10, 60, 100, 40, (80, 0, 200), 'Repulse', True, 'Repulse')
add_particle_btn = Button(10, 110, 100, 40, (120, 0, 200), '+ Particles', False, '+ Particle')
subtract_particle_btn = Button(10, 170, 100, 40, (80, 30, 200), '- Particles', False, '- Particle')

dash = Dashboard(600, 0, 200, 800)

dash.add_element(grav_btn)
dash.add_element(repulse_btn)
dash.add_element(add_particle_btn)
dash.add_element(subtract_particle_btn)

pygame.init()
CLOCK = pygame.time.Clock()


#CONSTANTS

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

FPS = 120

SLOW_TIME_BY = 1

NUM_PARTICLES = 4

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

    update_container_settings(liquid, dash)

    dash.render(screen=screen)

    liquid.update(screen=screen, dt=dt)

    pygame.display.update()

pygame.quit()
