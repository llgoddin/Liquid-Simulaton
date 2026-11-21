import math
import time

import pygame

from Button import Button
from Dashboard import Dashboard
from Particle_Manager import Particle_Manager
from Text_Label import Text_Label
from ui_controls import CountRepeater

SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 120
UI_PARTICLE_CAP = 200
DEBUG_KEY = pygame.K_d


def queue(manager, action):
    if not manager.queue_control(action):
        print('Dashboard control rejected: pending control queue is full')


def queue_count(manager, action):
    # Check the count at execution time: several queued clicks can share a step.
    def apply():
        if action == '+ Particle' and manager.num_particles < UI_PARTICLE_CAP:
            manager.spawn_particle()
        elif action == '- Particle' and manager.num_particles > 0:
            manager.delete_particle()
    queue(manager, apply)


def queue_bounds(manager, axis, change):
    def apply():
        # Keep the box within the play area and large enough for the obstacle.
        radius = manager.obstacle[2] if manager.obstacle else 0
        minimum = max(10, radius + manager.particle_radius + 1)
        if axis == 'width':
            manager.update_bounds(max(minimum, min(290, manager.X_BOUND + change)), manager.Y_BOUND)
        else:
            manager.update_bounds(manager.X_BOUND, max(minimum, min(290, manager.Y_BOUND + change)))
    queue(manager, apply)


def handle_dashboard_press(manager, element, repeater, now):
    action = element.func_str
    if action == 'Gravity':
        queue(manager, lambda active=element.active: manager.set_gravity(active))
    elif action in ('+ Particle', '- Particle'):
        repeater.press(action, now)
        queue_count(manager, action)
    elif action in ('+ Container Width', '- Container Width'):
        queue_bounds(manager, 'width', 1 if action[0] == '+' else -1)
    elif action in ('+ Container Height', '- Container Height'):
        queue_bounds(manager, 'height', 1 if action[0] == '+' else -1)
    elif action in ('+ Strength', '- Strength'):
        delta = 1 if action[0] == '+' else -1
        queue(manager, lambda: setattr(manager, 'mouse_strength', max(0, min(100, manager.mouse_strength + delta))))
    elif action in ('+ Radius', '- Radius'):
        delta = 10 if action[0] == '+' else -10
        queue(manager, lambda: setattr(manager, 'mouse_radius', max(10, min(300, manager.mouse_radius + delta))))


def obstacle_hit(manager, pos):
    if manager.obstacle is None:
        return False
    x, y, radius = manager.obstacle
    return math.hypot(pos[0] - manager.x - x, manager.y - pos[1] - y) <= radius


def local_position(manager, pos):
    return pos[0] - manager.x, manager.y - pos[1]


pygame.init()
CLOCK = pygame.time.Clock()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Liquid Simulator')
liquid = Particle_Manager(x=300, y=300, num_particles=30, radius=5, x_bounds=100,
                          y_bounds=100, gravity=False, repulse=True, vertical_spawn=True)
liquid.set_obstacle(0, 0, 30)

dash = Dashboard(600, 0, 200, 600)
button_color = (51, 69, 84)
buttons = [
    Button(10, 100, 180, 40, button_color, 'Gravity', liquid.GRAVITY, 'Gravity'),
    Button(10, 150, 180, 40, button_color, 'Mouse forces', True, 'Mouse interaction'),
    Button(10, 200, 100, 40, button_color, '+ Particles', False, '+ Particle'),
    Button(10, 250, 100, 40, button_color, '- Particles', False, '- Particle'),
    Button(10, 300, 100, 40, button_color, '+ Width', False, '+ Container Width'),
    Button(10, 350, 100, 40, button_color, '- Width', False, '- Container Width'),
    Button(10, 400, 100, 40, button_color, '+ Height', False, '+ Container Height'),
    Button(10, 450, 100, 40, button_color, '- Height', False, '- Container Height'),
    Button(115, 200, 75, 40, button_color, 'Force +', False, '+ Strength'),
    Button(115, 250, 75, 40, button_color, 'Force -', False, '- Strength'),
    Button(115, 300, 75, 40, button_color, 'Radius +', False, '+ Radius'),
    Button(115, 350, 75, 40, button_color, 'Radius -', False, '- Radius'),
]
for button in buttons:
    dash.add_element(button)
grav_btn, mouse_btn = buttons[:2]
labels = [
    Text_Label(5, 5, 190, 25, button_color, 'LIQUID SIMULATOR', 'heading'),
    Text_Label(5, 30, 190, 25, button_color, '', 'Particle Count'),
    Text_Label(5, 55, 190, 25, button_color, '', 'FPS Count'),
    Text_Label(5, 495, 190, 20, button_color, '', 'settings'),
    Text_Label(5, 515, 190, 20, button_color, 'Left: attract / move', 'help1'),
    Text_Label(5, 535, 190, 20, button_color, 'Right: repel', 'help2'),
    Text_Label(5, 555, 190, 20, button_color, 'D: diagnostics', 'help3'),
]
for label in labels:
    dash.add_element(label)

repeater = CountRepeater()
prev_time = None
mouse_left = mouse_right = obstacle_dragging = False
drag_offset = (0.0, 0.0)
debug_overlays = False
run = True
while run:
    CLOCK.tick(FPS)
    now = time.monotonic()
    dt = 0 if prev_time is None else now - prev_time
    prev_time = now
    screen.fill((230, 230, 230))

    # Input states describe the elapsed interval, before processing new events.
    mouse_forces = []
    pos = pygame.mouse.get_pos()
    if mouse_btn.active and pos[0] < dash.x:
        if mouse_left:
            mouse_forces.append((pos, False))
        if mouse_right:
            mouse_forces.append((pos, True))
    liquid.advance(dt, mouse_forces)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        elif event.type == pygame.KEYDOWN and event.key == DEBUG_KEY:
            debug_overlays = not debug_overlays
        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = getattr(event, 'pos', pygame.mouse.get_pos())
            if event.button == 1 and pos[0] >= dash.x:
                dash.check_click(pos)
                for button in buttons:
                    if button.get_clicked():
                        handle_dashboard_press(liquid, button, repeater, now)
                        break
            elif event.button == 1 and obstacle_hit(liquid, pos):
                obstacle_dragging = True
                px, py = local_position(liquid, pos)
                drag_offset = (liquid.obstacle[0] - px, liquid.obstacle[1] - py)
            elif event.button == 1:
                mouse_left = True
            elif event.button == 3 and pos[0] < dash.x:
                mouse_right = True
        elif event.type == pygame.MOUSEMOTION and obstacle_dragging:
            px, py = local_position(liquid, event.pos)
            target = (px + drag_offset[0], py + drag_offset[1])
            queue(liquid, lambda target=target: liquid.move_obstacle(*target))
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                mouse_left = False
                obstacle_dragging = False
                repeater.release()
                dash.reset_clicked_elements()
            elif event.button == 3:
                mouse_right = False

    for _ in range(repeater.update(now)):
        queue_count(liquid, repeater.action)
    grav_btn.text = f'Gravity: {"on" if grav_btn.active else "off"}'
    mouse_btn.text = f'Mouse forces: {"on" if mouse_btn.active else "off"}'
    labels[1].set_text(f'Particles: {liquid.num_particles} / {UI_PARTICLE_CAP}')
    labels[2].set_text(f'FPS: {int(CLOCK.get_fps())}  |  SPH on')
    labels[3].set_text(f'Force {liquid.mouse_strength:g}  |  Radius {liquid.mouse_radius:g}')
    liquid.render(screen=screen, debug=debug_overlays)
    dash.render(screen=screen)
    pygame.display.update()

pygame.quit()
