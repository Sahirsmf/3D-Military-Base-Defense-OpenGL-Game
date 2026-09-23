# 3D Military Base Defense

A real-time 3D base-defense shooter built for CSE423 (Computer Graphics), implemented entirely in Python with raw OpenGL (PyOpenGL + GLUT) — no external game engine or imported 3D models; every object is built from primitive shapes.

## Gameplay

- Defend your base against enemies approaching across a procedurally scattered battlefield, across 3 escalating waves
- Two enemy types: fast, low-health scouts and slow, high-health tanks
- Two weapons: a rifle (limited ammo, reload) and an RPG (splash damage, cooldown)
- Collect health and enemy-slow boosts that spawn periodically during each wave
- Base health depletes as enemies reach it — survive all waves to win

## Controls

| Key | Action |
|---|---|
| `W` / `S` | Move forward / backward |
| `A` / `D` | Rotate aim |
| Left click | Fire current weapon |
| `E` | Switch weapon |
| `Q` | Fire / switch to RPG |
| `Space` | Sprint (with cooldown) |
| Right click | Toggle camera (third-person orbit ↔ first-person aim) |
| Arrow keys | Rotate / tilt the orbit camera |
| `R` | Restart |

## Technical Highlights

- **Primitive-only rendering** — all geometry (trees, boulders, sandbags, trucks, tower, player, enemies) is built from `glutSolidCube`, `gluSphere`, `gluCylinder`, and a custom `draw_disk()` (`GL_TRIANGLE_FAN`) replacement for `gluDisk`, per course constraints on allowed primitives
- **Procedural environment generation** — trees, boulders, sandbags, and trucks are placed using seeded random placement with minimum-distance spacing checks, so the layout is reproducible without being hardcoded
- **Dual camera system** — a third-person orbit camera (adjustable angle, height, distance) and a first-person aim camera, toggled at runtime
- **Ray-based hit detection** — bullets and rockets use point-to-line-segment projection against enemy positions; the RPG applies splash damage within a radius
- **Obstacle-avoiding enemy AI** — enemies steer around trees, boulders, trucks, and sandbags using a repulsion-based steering adjustment while pathing toward the base
- **Particle effects** — muzzle flashes, shell casings, and explosions implemented as lightweight physics-driven particles
- **Wave-based state machine** — handles wave spawning, pacing, completion, and game-over/restart logic

## Tech Stack

Python · PyOpenGL (`OpenGL.GL`, `OpenGL.GLUT`, `OpenGL.GLU`)

## Running It

```bash
pip install PyOpenGL PyOpenGL_accelerate
python final.py
```

Requires GLUT support — this comes bundled with PyOpenGL on most platforms; on Linux you may need to separately install `freeglut3-dev`.

## Course Info

Built for CSE423, Computer Graphics.
