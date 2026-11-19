# Contributing

Liquid-Simulaton is a small project and the process is small with it. This file says what a change should look like; the [readme](README.md) says how to run the thing.

## Setting up

- **Python 3.12.** `requirements.txt` is pinned to the versions verified on 3.12, which is what CI uses.
- **A virtualenv.** `.env/` is gitignored.

    >$python3 -m venv .env
    >$./.env/bin/pip install -r requirements.txt

- **Run from the repository root.** The project is a flat set of modules, not an installed package, and the tests import them from the working directory -- so run the suite from the repository root.

## Making a change

1. **Branch off `main`.** There is no separate integration branch; feature branches pull request straight into `main`.
2. **One concern per commit**, lowercase conventional prefix, one line -- `fix: …`, `chore: …`, `docs: …`, `test: …`.
3. **Open a pull request against `main`**, small and focused. A large change is worth an issue first.
4. **Both gates must be green before review is requested.** They run on every pull request:

    >$python -m unittest discover -s tests
    >$ruff check .

The suite is the standard library's `unittest` and needs nothing beyond `requirements.txt`. `ruff` is **not** a project dependency -- install it separately (`pip install ruff==0.17.5`, the version CI pins) or let CI run it.

## Tests

A change in behaviour needs a test that fails without it. The suite draws into off-screen surfaces rather than a window, so it runs headless; set SDL's dummy drivers if your machine has no display:

    >$SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m unittest discover -s tests

Where the code has a known gap, mark the test `expectedFailure` with a note rather than writing it to bless the gap -- then remove the marker once the gap is closed.

## Style

`pyproject.toml` holds the rule set, the intended 88-column line length, and the reason `ruff` was chosen over a style-only checker. The rules deliberately **not** enabled are named there too, so a missing check reads as a decision rather than an oversight. `ruff check .` is the gate; run it before you push.

## Licence

Contributions are accepted under the repository's [MIT licence](LICENSE).
