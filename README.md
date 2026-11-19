# Liquid-Simulaton

The goal of this project is to simulate liquids using a technique called Smoothed-Particle Hydrodynamics using python

## Motivation

I created this project to practice implimenting physics in code.

## Status

Under Development

## Features

- Gravity
- Particle Repulsion
- Adjustable Container

## Time integration

Physics uses fixed 1/120-second semi-implicit steps, independent of rendering.
The existing force values are calibrated as velocity increments per 120 Hz
step: acceleration is multiplied by `dt * 120`, position by `dt` once, and
velocity damping by `0.99 ** (dt * 120)`. At 120 Hz this retains the original
update order and scale; these are not physical SI units.

At most eight steps are processed per rendered frame. Elapsed simulation time
above eight steps in a frame is discarded, and the cumulative discarded time
in seconds is available as `Particle_Manager.dropped_time`. Sustained overload
therefore slows simulation relative to wall time. Button transitions are sampled
at frame boundaries: the previous held state describes the elapsed interval.
Mouse force is weighted by the fraction of each physics step for which it was
held, including across render frames, without queuing events. Cursor position is
sampled once per frame; transitions within the same event batch have no duration
and rapid motion is approximate. Discarded stall time contributes no input.
Existing force and collision limitations are unchanged. Dashboard controls at a
physics boundary apply immediately. Otherwise, the current step completes with
its old settings and queued changes apply in order before the next step; buttons
show the requested state immediately, so the physics can lag the display by up
to one step of simulation time. Holding a button retains its existing per-render
repeat behavior. The queue holds at most 256 changes; further changes are rejected,
a warning is printed, and `Particle_Manager.rejected_controls` counts them. A
rejected toggle can leave the displayed button state different from the physics
setting; toggle it again after the queue drains to resynchronize.

Run the tests after installing the existing pygame dependency:

```sh
python -m unittest discover -s tests -v
```

## Controls

- Buttons are used to control various effects such as gravity, repulsion force, ect.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install dependencies found in requirements.txt.
Follow the instructions below to set up your virtual enviornment:

1. Create the virtual environment using python3's venv command

   > $python3 -m venv /example/path/destination/.env

   - Make sure to include /venv at the end in order to package the environment in a single directory

2. Navigate to the directory containing /.env
   > $cd /example/path/destination
3. Activate the virtual environment by calling the 'activate' script
   Mac/Linux:

   > $source .env/bin/activate

   Windows:

   > C:\\..\destination> .env\\bin\\activate.bat

4. Install dependencies using the included requirements file

   > $pip install -r requirements.txt

5. Run Graphics.py
   > $python3 Graphics.py

## Dependencies Used

## Credits

- [Smoothed Particle Hydrodynamics Wiki](https://en.wikipedia.org/wiki/Smoothed-particle_hydrodynamics)
- [Coding Adventure: Simulating Fluids By Sebastian Lague ](https://youtu.be/rSKMYc1CQHE?si=SritZ9ryH0EIech2)

## Author

Lucas Goddin
