import pygame
import time
import math
from New_Vector2D import Vector2D
from Particle import Particle
from Particle_Manager import Particle_Manager
from Button import Button
from Dashboard import Dashboard

colors = {
    'red': (255, 0, 0),
    'green': (0, 255, 0),
    'blue': (0, 0, 255),
    'blue': (0, 0, 0),
    'blue': (0, 0, 0),
    'blue': (0, 0, 0),
    'blue': (0, 0, 0),
}

def update_container_settings(p_manager, dash):
    for element in dash.get_elements():
        if element.get_clicked():
            match element.func_str:
                case 'Gravity':
                    p_manager.set_gravity(element.active)

                case 'Repulse':
                    p_manager.set_repulse(element.active)

                case '+ Particle':
                    p_manager.spawn_particle()

                case '- Particle':
                    p_manager.delete_particle()

                #TO DO - IMPLEMENT
                case '+ Container Width':
                    p_manager.increase_container_width()

                case '- Container Width':
                    p_manager.decrease_container_width()

                case '+ Container Height':
                    p_manager.increase_container_height()

                case '- Container Height':
                    p_manager.decrease_container_height()

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
increase_container_width_btn = Button(10, 230, 100, 40, (80, 30, 200), '+ Width', False, '+ Container Width')
decrease_container_width_btn = Button(10, 290, 100, 40, (80, 30, 200), '- Width', False, '- Container Width')
increase_container_height_btn = Button(10, 350, 100, 40, (80, 30, 200), '+ Height', False, '+ Container Height')
decrease_container_height_btn = Button(10, 410, 100, 40, (80, 30, 200), '- Height', False, '- Container Height')

dash = Dashboard(600, 0, 200, 800)

dash.add_element(grav_btn)
dash.add_element(repulse_btn)
dash.add_element(add_particle_btn)
dash.add_element(subtract_particle_btn)
dash.add_element(increase_container_width_btn)
dash.add_element(decrease_container_width_btn)
dash.add_element(increase_container_height_btn)
dash.add_element(decrease_container_height_btn)

pygame.init()
CLOCK = pygame.time.Clock()


#CONSTANTS

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

FPS = 120
DASH_FPS = FPS / 10

SLOW_TIME_BY = 1

NUM_PARTICLES = 4

VERTICAL_SPAWN = True

GRAVITY = False
REPULSE = True

CONTAINER = (200, 200)


# Calculated Variables
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Liquid Simulator")
liquid = Particle_Manager(x=(SCREEN_WIDTH/2 - 100), y=SCREEN_HEIGHT/2, num_particles=NUM_PARTICLES, radius=5, x_bounds=CONTAINER[0]/2, y_bounds=CONTAINER[1]/2, gravity=GRAVITY, repulse=REPULSE, vertical_spawn=VERTICAL_SPAWN)

dash_tick = 0

now = 0
prev_time = None

mouse_left = False
mouse_right = False

run = True

# Main Loop
while run:

    CLOCK.tick(FPS)

    dash_tick += 1

    now = time.time()

    if not prev_time:
        prev_time = now

    dt = now - prev_time
    prev_time = now

    dt = dt / SLOW_TIME_BY

    screen.fill((230, 230, 230))

    if mouse_left:
        pos = pygame.mouse.get_pos()
        if not pos[0] > dash.x:
            liquid.apply_mouse_force(pos)
    
    if mouse_right:
        pos = pygame.mouse.get_pos()
        if not pos[0] > dash.x:
            liquid.apply_mouse_force(pos, True)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_left = True

            elif event.button == 3:
                mouse_right = True

            pos = pygame.mouse.get_pos()

            if pos[0] > dash.x:
                dash.check_click(pos)

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                mouse_left = False

            elif event.button == 3:
                mouse_right = False

            dash.reset_clicked_elements()

    update_container_settings(liquid, dash)

    liquid.update(screen=screen, dt=dt)

    dash.render(screen=screen)

    pygame.display.update()

pygame.quit()
