import pygame
import time
import math
from Particle import Particle

def render_particles(screen, particles):
    X_OFFSET = SCREEN_WIDTH/2
    Y_OFFSET = -SCREEN_HEIGHT/2

    for particle in particles:
        pygame.draw.circle(screen, particle.color, (particle.x + X_OFFSET, 600 - particle.y + Y_OFFSET), particle.radius)

def create_particles(num):
    particles = []
    num_particles = num
    radius = 5

    for _ in range(num_particles):
        particles.append(Particle(x=0, y=0, radius=radius, magnitude=10, direction=270))

    square = round(math.ceil(math.sqrt(num_particles)), 0)

    buffer = 10

    i = 0

    for x in range(square):
        for y in range(square):
            print(f"i = {i}")

            if i < len(particles):
                particles[i].bind_x(SCREEN_WIDTH/2, -SCREEN_WIDTH/2)
                particles[i].bind_y(SCREEN_HEIGHT/2, -SCREEN_HEIGHT/2)
                particles[i].x = (buffer + radius) * x
                particles[i].y = (buffer + radius) * y
            else:
                continue

            i += 1

    return particles


pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

particles = create_particles(100)

FPS = 60
now = 0
prev_time = None
clock = pygame.time.Clock()
run = True


while run:

    clock.tick(FPS)

    now = time.time()

    if not prev_time:
        prev_time = now

    dt = now - prev_time
    prev_time = now

    screen.fill((230, 230, 230))

    for particle in particles:
        particle.move(dt)

    render_particles(screen, particles)


    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    pygame.display.update()