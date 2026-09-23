from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random


def draw_disk(outer_radius, slices):
    """Replacement for gluDisk(quadric, 0, outer_radius, slices, loops).
    Draws a solid circle using GL_TRIANGLE_FAN — only allowed primitives used."""
    glBegin(GL_TRIANGLE_FAN)
    glVertex3f(0.0, 0.0, 0.0)
    for i in range(slices + 1):
        a = 2.0 * math.pi * i / slices
        glVertex3f(outer_radius * math.cos(a), outer_radius * math.sin(a), 0.0)
    glEnd()


WINDOW_W      = 1000
WINDOW_H      = 800
MAP_RADIUS    = 1400        
INNER_RADIUS  = 500         

camera_angle    = 0         
camera_distance = 1200
camera_height   = 900
camera_min_h    = 400
camera_max_h    = 1600
fovY            = 90
camera_mode     = 0   

def _make_trees(count=25):
    positions = []
    rng = random.Random(42)
    attempts = 0
    while len(positions) < count and attempts < 10000:
        attempts += 1
        angle = rng.uniform(0, 2 * math.pi)
        dist  = rng.uniform(INNER_RADIUS + 80, MAP_RADIUS - 150)
        x, y  = dist * math.cos(angle), dist * math.sin(angle)
        ok = all(math.hypot(x - tx, y - ty) > 120 for tx, ty, _ in positions)
        if ok:
            positions.append((x, y, rng.uniform(0.85, 1.25)))
    return positions

def _make_boulders(count=10):
    positions = []
    rng = random.Random(77)
    attempts = 0
    while len(positions) < count and attempts < 10000:
        attempts += 1
        angle = rng.uniform(0, 2 * math.pi)
        dist  = rng.uniform(INNER_RADIUS + 60, MAP_RADIUS - 200)
        x, y  = dist * math.cos(angle), dist * math.sin(angle)
        ok = all(math.hypot(x - bx, y - by) > 90 for bx, by, _ in positions)
        if ok:
            positions.append((x, y, rng.uniform(0.7, 1.4)))
    return positions

def _make_trucks(count=6):
    positions = []
    rng = random.Random(13)
    for i in range(count):
        angle = i * (360 / count) + rng.uniform(-15, 15)
        dist  = rng.uniform(260, 380)
        x     = dist * math.cos(math.radians(angle))
        y     = dist * math.sin(math.radians(angle))
        positions.append((x, y, angle + 90))
    return positions

def draw_boosts():
    for b in boosts:
        glPushMatrix()
        hover_y = math.sin(math.radians(b["anim_rot"] * 2)) * 5
        glTranslatef(b["x"], b["y"], b["z"] + hover_y)
        glRotatef(b["anim_rot"], 0, 0, 1) 
        
        if b["type"] == "health":
            glColor3f(0.1, 0.9, 0.2)

            glPushMatrix()
            glScalef(1.8, 0.6, 0.6)
            glutSolidCube(12)
            glPopMatrix()
    
            glPushMatrix()
            glScalef(0.6, 1.8, 0.6)
            glutSolidCube(12)
            glPopMatrix()
        
        elif b["type"] == "slow":
            glColor3f(0.4, 0.8, 1.0)
            glPushMatrix()
            gluCylinder(gluNewQuadric(), 10, 0, 15, 4, 1) 
            glRotatef(180, 1, 0, 0)
            gluCylinder(gluNewQuadric(), 10, 0, 15, 4, 1) 
            glPopMatrix()
            
        glPopMatrix()

def _make_sandbags(count=24):
    positions = []
    rng = random.Random(99)
    for i in range(count):
        angle = i * (360 / count) + rng.uniform(-5, 5)
        dist  = rng.uniform(220, 255)
        x     = dist * math.cos(math.radians(angle))
        y     = dist * math.sin(math.radians(angle))
        positions.append((x, y, angle))
    return positions

TREE_POSITIONS    = _make_trees(25)
BOULDER_POSITIONS = _make_boulders(10)
TRUCK_POSITIONS   = _make_trucks(6)
SANDBAG_POSITIONS = _make_sandbags(24)

OBSTACLE_CIRCLES = (
    [(x, y, 55)  for (x, y, _) in TREE_POSITIONS]   +   
    [(x, y, 50)  for (x, y, _) in BOULDER_POSITIONS]    
)

player_x           = 0.0       
player_y           = -300.0    
player_z           = 2.0       
player_angle       = 180.0       
player_gun_angle   = 180.0       

PLAYER_MOVE_SPEED   = 15.0      
PLAYER_SPRINT_SPEED = 25.0      
PLAYER_GUN_ROTATE   = 8.0       

sprint_active      = False
SPRINT_DURATION    = 10*60        
SPRINT_COOLDOWN    = 20 * 60   
sprint_timer       = 0         
sprint_cooldown_timer = 0      
sprint_glow_t      = 0.0     

RIFLE_BULLETS      = 30        
RIFLE_RELOAD_TIME  = 120       
rifle_ammo         = RIFLE_BULLETS
rifle_reloading    = False
rifle_reload_timer = 0
rifle_anim_t       = 0.0       
RIFLE_DAMAGE       = 20

RPG_COOLDOWN_TIME  = 10 * 60   
rpg_ready          = True
rpg_cooldown_timer = 0
rpg_anim_t         = 0.0       
RPG_DAMAGE         = 120

current_weapon     = 0
weapon_switch_anim = 0         

player_bullets     = []
BULLET_SPEED       = 28.0
BULLET_RANGE       = 2200      

player_rockets     = []
ROCKET_SPEED       = 18.0
ROCKET_RANGE       = 2600
ROCKET_SPLASH_R    = 120       

muzzle_particles   = []        

def _player_world_pos():
    """Return (px, py, pz) — the player's 3-D world position on the ground."""
    return player_x, player_y, player_z

def _gun_origin():
    px, py, pz = _player_world_pos()
    rad = math.radians(player_gun_angle)
    
    bx  = px + (15 * 1.5) * math.sin(rad)   
    by  = py + (15 * 1.5) * math.cos(rad)
    bz  = pz + (38 * 1.5)                   
    return bx, by, bz

def _fire_rifle():
    global rifle_ammo, rifle_reloading, rifle_reload_timer, rifle_anim_t
    if rifle_reloading or rifle_ammo <= 0:
        return
    bx, by, bz = _gun_origin()      
    rad = math.radians(player_gun_angle)
    
    dx = math.sin(rad)             
    dy = math.cos(rad)
    dz = 0.0                       

    player_bullets.append([bx, by, bz, dx, dy, dz, 0.0])
    rifle_ammo  -= 1
    rifle_anim_t = 12
    _spawn_shell_particle(bx, by, bz)
    if rifle_ammo <= 0:
        rifle_reloading    = True
        rifle_reload_timer = RIFLE_RELOAD_TIME

def _fire_rpg():
    global rpg_ready, rpg_cooldown_timer, rpg_anim_t
    if not rpg_ready:
        return
    bx, by, bz = _gun_origin()
    rad = math.radians(player_gun_angle)
    
    dx = math.sin(rad)
    dy = math.cos(rad)
    dz = 0.0
    
    player_rockets.append([bx, by, bz, dx, dy, dz, 0.0])
    rpg_ready          = False
    rpg_cooldown_timer = RPG_COOLDOWN_TIME
    rpg_anim_t         = 20

def _spawn_shell_particle(bx, by, bz):
    rad = math.radians(player_gun_angle + 90)   
    muzzle_particles.append({
        "x": bx, "y": by, "z": bz,
        "vx": math.sin(rad) * 6 + random.uniform(-1, 1),
        "vy": math.cos(rad) * 6 + random.uniform(-1, 1),
        "vz": random.uniform(3, 7),
        "life": 18, "max_life": 18,
        "kind": "shell",
    })

def _is_boost_pos_clear(x, y):
    if math.hypot(x, y) < 200: 
        return False
    
    px, py, _ = _player_world_pos()
    if math.hypot(x - px, y - py) < 100:
        return False
        
    for (ox, oy, orad) in OBSTACLE_CIRCLES:
        if math.hypot(x - ox, y - oy) < orad + 30: 
            return False
            
    for (tx, ty, _) in TRUCK_POSITIONS:
        if math.hypot(x - tx, y - ty) < 90:
            return False
            
    for (sx, sy, _) in SANDBAG_POSITIONS:
        if math.hypot(x - sx, y - sy) < 60:
            return False
            
    for b in boosts:
        if math.hypot(x - b["x"], y - b["y"]) < 50:
            return False 
    return True

def update_boosts():
    global boost_spawn_timer, boost_spawn_queue, boosts, sprint_active, sprint_timer, sprint_cooldown_timer
    global base_health, base_health_boost_timer, base_health_boost_amount, enemy_slow_timer

    if game_over:
        return

    if wave_started and boost_spawn_queue:
        boost_spawn_timer -= 1
        if boost_spawn_timer <= 0:
            b_type = boost_spawn_queue.pop(0)
            
            spawned = False
            attempts = 0
            while not spawned and attempts < 100:
                angle = random.uniform(0, 2 * math.pi)
                dist = random.uniform(250, MAP_RADIUS - 150) 
                bx = dist * math.cos(angle)
                by = dist * math.sin(angle)
                
                if _is_boost_pos_clear(bx, by):
                    boosts.append({
                        "type": b_type,
                        "x": bx,
                        "y": by,
                        "z": 15,
                        "anim_rot": 0.0,
                        "life": 25 * 60  
                    })
                    spawned = True
                    
            boost_spawn_timer = random.randint(10 * 60, 20 * 60)

    px, py, pz = _player_world_pos()
    alive_boosts = []
    
    for b in boosts:
        b["anim_rot"] += 3.0   
        b["life"] -= 1
        
        dist_to_player = math.hypot(b["x"] - px, b["y"] - py)
        if dist_to_player < 40:  
            if b["type"] == "health":
                base_health_boost_amount += base_health 
                base_health += base_health
                base_health_boost_timer = 10 * 60 
            elif b["type"] == "slow":            
                enemy_slow_timer = 10 * 60
            continue 
            
        if b["life"] > 0:
            alive_boosts.append(b)
            
    boosts[:] = alive_boosts

    if base_health_boost_timer > 0:
        base_health_boost_timer -= 1
        if base_health_boost_timer <= 0:
            base_health = max(1, base_health - base_health_boost_amount)
            base_health_boost_amount = 0

    if enemy_slow_timer > 0:
        enemy_slow_timer -= 1

def update_player():
    global sprint_timer, sprint_cooldown_timer, sprint_active, sprint_glow_t
    global rifle_reloading, rifle_reload_timer, rifle_ammo, rifle_anim_t
    global rpg_ready, rpg_cooldown_timer, rpg_anim_t
    global weapon_switch_anim
    global player_bullets, player_rockets, muzzle_particles

    if game_over:
        return
    
    if sprint_active:
        sprint_timer -= 1
        sprint_glow_t += 0.3
        if sprint_timer <= 0:
            sprint_active = False
            sprint_timer  = 0
    else:
        if sprint_cooldown_timer > 0:
            sprint_cooldown_timer -= 1

    if rifle_reloading:
        rifle_reload_timer -= 1
        if rifle_reload_timer <= 0:
            rifle_ammo      = RIFLE_BULLETS
            rifle_reloading = False
    if rifle_anim_t > 0:
        rifle_anim_t -= 1

    if not rpg_ready:
        rpg_cooldown_timer -= 1
        if rpg_cooldown_timer <= 0:
            rpg_ready = True
    if rpg_anim_t > 0:
        rpg_anim_t -= 1

    if weapon_switch_anim > 0:
        weapon_switch_anim -= 1

    new_bullets = []
    for b in player_bullets:
        b[0] += b[3] * BULLET_SPEED
        b[1] += b[4] * BULLET_SPEED
        b[2] += b[5] * BULLET_SPEED
        b[6] += BULLET_SPEED
        if b[6] > BULLET_RANGE or b[2] < -10:
            continue
        hit = False
        for e in enemies:
            if not e["alive"]:
                continue
            ox = b[0] - b[3] * b[6]   
            oy = b[1] - b[4] * b[6]   
            ex_rel = e["x"] - ox
            ey_rel = e["y"] - oy
            dot = ex_rel * b[3] + ey_rel * b[4]
            if dot < 0 or dot > b[6]:
                continue
            perp = math.hypot(ex_rel - dot * b[3], ey_rel - dot * b[4])
            if perp < 55:
                damage_enemy(e, RIFLE_DAMAGE)
                hit = True
                break
        if not hit:
            new_bullets.append(b)
    player_bullets[:] = new_bullets

    new_rockets = []
    for r in player_rockets:
        r[0] += r[3] * ROCKET_SPEED
        r[1] += r[4] * ROCKET_SPEED
        r[2] += r[5] * ROCKET_SPEED
        r[6] += ROCKET_SPEED
        if r[6] > ROCKET_RANGE or r[2] < -10:
            continue
        hit = False
        for e in enemies:
            if not e["alive"]:
                continue
            ox = r[0] - r[3] * r[6]
            oy = r[1] - r[4] * r[6]
            ex_rel = e["x"] - ox
            ey_rel = e["y"] - oy
            dot = ex_rel * r[3] + ey_rel * r[4]
            if dot < 0 or dot > r[6]:
                continue
            perp = math.hypot(ex_rel - dot * r[3], ey_rel - dot * r[4])
            if perp < ROCKET_SPLASH_R:
                for e2 in enemies:
                    if not e2["alive"]:
                        continue
                    d2 = math.hypot(r[0] - e2["x"], r[1] - e2["y"])
                    if d2 < ROCKET_SPLASH_R:
                        damage_enemy(e2, RPG_DAMAGE)
                _spawn_explosion(r[0], r[1], 1.8)
                hit = True
                break
        if not hit:
            new_rockets.append(r)
    player_rockets[:] = new_rockets
    
    for p in muzzle_particles:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["z"] += p["vz"]
        p["vz"] -= 0.6          
        p["life"] -= 1
    muzzle_particles[:] = [p for p in muzzle_particles if p["life"] > 0]

def draw_player():
    px, py, pz = _player_world_pos()

    glPushMatrix()
    glTranslatef(px, py, pz)
    glRotatef(-player_gun_angle, 0, 0, 1)   
    glScalef(1.5, 1.5, 1.5)
    
    if sprint_active:
        t   = sprint_glow_t
        glPushMatrix()
        glTranslatef(0, 0, -4)
        r = 0.5 + 0.5 * abs(math.sin(t * 0.5))
        g = 0.8 + 0.2 * abs(math.cos(t * 0.4))
        glColor3f(r, g, 0.0)
        glScalef(1.0, 1.0, 0.15)
        gluCylinder(gluNewQuadric(), 26, 0, 20, 16, 4)   
        glPopMatrix()

    walk_t = sprint_glow_t if sprint_active else 0.0
    anim   = math.sin(walk_t) * 10
    for side in (-1, 1):
        glPushMatrix()
        glTranslatef(side * 8, 0, 0)
        glRotatef(side * anim, 1, 0, 0)
        glColor3f(0.15, 0.25, 0.15)     
        gluCylinder(gluNewQuadric(), 6, 5, 32, 10, 4)
        glTranslatef(0, 0, 32)
        glColor3f(0.18, 0.12, 0.06)     
        gluCylinder(gluNewQuadric(), 6, 7, 14, 10, 4)
        glPopMatrix()

    glPushMatrix()
    glTranslatef(0, 0, 30)
    glColor3f(0.22, 0.30, 0.18)         
    glScalef(1.1, 0.75, 1.0)
    glutSolidCube(30)
    glPopMatrix()

    if rifle_reloading:
        frac = 1.0 - rifle_reload_timer / RIFLE_RELOAD_TIME
        glPushMatrix()
        glTranslatef(0, 0, 30)
        glColor3f(frac, frac * 0.8, 0.0)
        glScalef(1.15, 0.80, 1.05)
        glutSolidCube(31)               
        glPopMatrix()

    glPushMatrix()
    glTranslatef(0, 0, 38)
    glRotatef(0, 0, 0, 1)             
    
    glPushMatrix()
    glTranslatef(-14, 0, 0)
    if current_weapon == 1:
        glRotatef(-85, 1, 0, 0)  # Point arm forward to balance RPG
    else:
        glRotatef(-85, 0, 1, 0)  # Rest at side)
    glColor3f(0.22, 0.30, 0.18)
    gluCylinder(gluNewQuadric(), 5, 4, 26, 8, 3)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(14, 0, 0)
    glTranslatef(14, 0, 0)
    if current_weapon == 0:
        glRotatef(-75, 1, 0, 0)  # Point arm forward to hold Rifle
    else:
        glRotatef(85, 0, 1, 0)   # Rest at side
    glColor3f(0.22, 0.30, 0.18)
    gluCylinder(gluNewQuadric(), 5, 4, 26, 8, 3)
    glPopMatrix()

    if current_weapon == 0:
        glPushMatrix()
        glTranslatef(14, 22, -4)
        glRotatef(90, 1, 0, 0)             

        if rifle_anim_t > 0:
            flash_s = rifle_anim_t / 12.0
            glPushMatrix()
            glTranslatef(0, 0, -32)        
            glColor3f(1.0, 0.85 * flash_s, 0.0)
            glScalef(flash_s, flash_s, flash_s)
            gluSphere(gluNewQuadric(), 8, 8, 6)
            glPopMatrix()

        glColor3f(0.12, 0.12, 0.12)        
        gluCylinder(gluNewQuadric(), 3, 2, 36, 12, 4)

        glPushMatrix()
        glTranslatef(0, 0, 8)
        glScalef(1.5, 0.5, 0.5)
        glutSolidCube(12)
        glPopMatrix()

        glTranslatef(0, 0, 4)
        glColor3f(0.20, 0.18, 0.16)        
        glScalef(1, 1, 1)
        glutSolidCube(10)
        glPopMatrix()

    else:
        glPushMatrix()
        glTranslatef(-14, 15, 6)
        glRotatef(90, 1, 0, 0)

        if rpg_anim_t > 0:
            flash_s = rpg_anim_t / 20.0
            glPushMatrix()
            glTranslatef(0, 0, -42)
            glColor3f(1.0, 0.5 * flash_s, 0.0)
            glScalef(flash_s * 1.5, flash_s * 1.5, flash_s * 1.5)
            gluSphere(gluNewQuadric(), 10, 10, 8)
            glPopMatrix()

        glColor3f(0.28, 0.30, 0.26)        
        gluCylinder(gluNewQuadric(), 5, 5, 46, 12, 4)
        glColor3f(0.50, 0.50, 0.48)        
        gluCylinder(gluNewQuadric(), 5, 10, 12, 10, 4)
        glPopMatrix()

    glPopMatrix()  
    
    glPushMatrix()
    glTranslatef(0, 0, 56)
    glColor3f(0.72, 0.62, 0.48)            
    gluSphere(gluNewQuadric(), 13, 12, 8)
    glTranslatef(0, 0, 10)
    glColor3f(0.20, 0.28, 0.16)            
    glScalef(1.1, 1.1, 0.7)
    gluSphere(gluNewQuadric(), 14, 12, 8)
    glPopMatrix()

    if weapon_switch_anim > 0:
        frac = weapon_switch_anim / 20.0
        glPushMatrix()
        glTranslatef(0, 0, 38)
        glColor3f(0.0, frac, frac)
        glScalef(frac * 0.8, frac * 0.8, frac * 0.8)
        gluSphere(gluNewQuadric(), 20, 10, 8)
        glPopMatrix()

    glPopMatrix()  

def draw_player_bullets():
    for b in player_bullets:
        glPushMatrix()
        glTranslatef(b[0], b[1], b[2])
        glColor3f(1.0, 0.55, 0.0)
        glutSolidCube(8)
        glPopMatrix()

    for r in player_rockets:
        glPushMatrix()
        glTranslatef(r[0], r[1], r[2])
        yaw   = math.degrees(math.atan2(r[3], r[4]))
        glRotatef(-yaw, 0, 0, 1)
        glColor3f(0.9, 0.8, 0.0)
        glRotatef(90, 1, 0, 0)
        gluCylinder(gluNewQuadric(), 5, 2, 28, 10, 4)   
        glColor3f(1.0, 0.3, 0.0)
        gluCylinder(gluNewQuadric(), 8, 0, 14, 10, 4)   
        glPopMatrix()

def draw_muzzle_particles():
    for p in muzzle_particles:
        frac = p["life"] / p["max_life"]
        glPushMatrix()
        glTranslatef(p["x"], p["y"], p["z"])
        glColor3f(0.8 * frac, 0.65 * frac, 0.10 * frac)
        glScalef(frac, frac, frac)
        gluSphere(gluNewQuadric(), 4, 6, 4)
        glPopMatrix()

def draw_player_hud():
    y = 70
    wname = "RIFLE" if current_weapon == 0 else "RPG"
    wcol  = (0.4, 1.0, 0.4) if current_weapon == 0 else (1.0, 0.6, 0.1)
    draw_text(WINDOW_W - 220, y + 50, f"Weapon: {wname}", color=wcol)

    if rifle_reloading:
        pct = 1.0 - rifle_reload_timer / RIFLE_RELOAD_TIME
        draw_text(WINDOW_W - 220, y + 25,
                  f"RELOADING... {int(pct*100)}%", color=(1.0, 0.8, 0.0))
    else:
        draw_text(WINDOW_W - 220, y + 25,
                  f"Ammo: {rifle_ammo}/{RIFLE_BULLETS}", color=(0.9, 0.9, 0.9))

    if rpg_ready:
        draw_text(WINDOW_W - 220, y,
                  "RPG: READY", color=(0.3, 1.0, 0.3))
    else:
        secs = rpg_cooldown_timer // 60
        draw_text(WINDOW_W - 220, y,
                  f"RPG: {secs}s cooldown", color=(1.0, 0.4, 0.2))

    if sprint_active:
        draw_text(WINDOW_W - 220, y - 25,
                  "SPRINT ACTIVE!", color=(0.2, 0.9, 1.0))
    elif sprint_cooldown_timer > 0:
        secs = sprint_cooldown_timer // 60
        draw_text(WINDOW_W - 220, y - 25,
                  f"Sprint CD: {secs}s", color=(0.6, 0.6, 0.6))
    else:
        draw_text(WINDOW_W - 220, y - 25,
                  "Sprint: READY [SPACE]", color=(0.5, 0.9, 0.5))

    draw_text(WINDOW_W - 220, y - 50,
              "W/S:move  A/D:aim  Q:RPG  E:switch", color=(0.7, 0.7, 0.6))

def reset_player():
    global player_x, player_y, player_angle, player_gun_angle
    global sprint_active, sprint_timer, sprint_cooldown_timer, sprint_glow_t
    global rifle_ammo, rifle_reloading, rifle_reload_timer, rifle_anim_t
    global rpg_ready, rpg_cooldown_timer, rpg_anim_t
    global current_weapon, weapon_switch_anim
    
    player_x              = 0.0
    player_y              = -300.0
    player_angle          = 180.0
    player_gun_angle      = 180.0
    sprint_active         = False
    sprint_timer          = 0
    sprint_cooldown_timer = 0
    sprint_glow_t         = 0.0
    rifle_ammo            = RIFLE_BULLETS
    rifle_reloading       = False
    rifle_reload_timer    = 0
    rifle_anim_t          = 0.0
    rpg_ready             = True
    rpg_cooldown_timer    = 0
    rpg_anim_t            = 0.0
    current_weapon        = 0
    weapon_switch_anim    = 0
    player_bullets.clear()
    player_rockets.clear()
    muzzle_particles.clear()

ENEMY_TYPES = {
    "fast": {
        "speed":        0.75,    
        "health":       40,
        "max_health":   40,
        "attack":       8,      
        "scale":        0.65,   
        "color_body":   (0.70, 0.15, 0.10),   
        "color_head":   (0.80, 0.55, 0.35),
    },
    "tank": {
        "speed":        0.35,    
        "health":       180,
        "max_health":   180,
        "attack":       25,
        "scale":        1.25,   
        "color_body":   (0.15, 0.20, 0.60),   
        "color_head":   (0.55, 0.65, 0.80),
    },
}

WAVES = [
    ["fast"] * 5,                    
    ["fast"] * 5 + ["tank"] * 2,     
    ["fast"] * 5 + ["tank"] * 4,     
]

boosts = []                   
boost_spawn_queue=[]
boost_spawn_timer = 300       
base_health_boost_timer = 0   
base_health_boost_amount = 0  
enemy_slow_timer = 0 

base_health       = 100
base_max_health   = 100
current_wave      = 0          
wave_started      = False
wave_complete     = False
game_over         = False
wave_pause_timer  = 0          
WAVE_PAUSE_FRAMES = 180        

enemies           = []         
spawn_queue       = []         
spawn_timer       = 0          
SPAWN_INTERVAL    = 40         

explosions        = []         

def _make_enemy(etype):
    angle = random.uniform(0, 2 * math.pi)
    x = MAP_RADIUS * math.cos(angle)
    y = MAP_RADIUS * math.sin(angle)
    t = ENEMY_TYPES[etype]
    return {
        "type":       etype,
        "x":          x,
        "y":          y,
        "health":     t["health"],
        "max_health": t["max_health"],
        "attack":     t["attack"],
        "speed":      t["speed"],
        "scale":      t["scale"],
        "color_body": t["color_body"],
        "color_head": t["color_head"],
        "alive":      True,
        "anim_t":     random.uniform(0, 2 * math.pi)
    }

def _steer_around_obstacles(ex, ey, dx, dy):
    AVOID_RADIUS = 80   
    steer_x, steer_y = 0.0, 0.0
    for (ox, oy, orad) in OBSTACLE_CIRCLES:
        dist = math.hypot(ex - ox, ey - oy)
        margin = orad + AVOID_RADIUS
        if dist < margin and dist > 0.01:
            rx = (ex - ox) / dist
            ry = (ey - oy) / dist
            strength = (margin - dist) / margin
            steer_x += rx * strength
            steer_y += ry * strength

    nx = dx + steer_x * 1.5
    ny = dy + steer_y * 1.5
    length = math.hypot(nx, ny)
    if length > 0.01:
        return nx / length, ny / length
    return dx, dy

def start_wave(wave_idx):
    global spawn_queue, spawn_timer, wave_started, wave_complete
    global boost_spawn_queue, boost_spawn_timer
    
    spawn_queue   = list(WAVES[wave_idx])
    random.shuffle(spawn_queue)
    spawn_timer   = 0
    
    num_boosts = wave_idx + 1
    boost_spawn_queue = ["health"] * num_boosts + ["slow"] * num_boosts
    random.shuffle(boost_spawn_queue) 
    boost_spawn_timer = 300 
    
    wave_started  = True
    wave_complete = False

def update_enemies():
    global enemies, spawn_queue, spawn_timer, current_wave
    global wave_started, wave_complete, wave_pause_timer
    global base_health, game_over, explosions

    if game_over:
        return

    explosions = [e for e in explosions if e["frame"] < e["max_frame"]]
    for e in explosions:
        e["frame"] += 1

    if not wave_started:
        if wave_pause_timer > 0:
            wave_pause_timer -= 1
        else:
            if current_wave < len(WAVES):
                start_wave(current_wave)
        return

    if spawn_queue:
        spawn_timer -= 1
        if spawn_timer <= 0:
            etype = spawn_queue.pop(0)
            enemies.append(_make_enemy(etype))
            spawn_timer = SPAWN_INTERVAL

    BASE_REACH_DIST = 160   

    for e in enemies:
        if not e["alive"]:
            continue

        dist_to_base = math.hypot(e["x"], e["y"])

        if dist_to_base <= BASE_REACH_DIST:
            base_health -= e["attack"]
            e["alive"]   = False
            _spawn_explosion(e["x"], e["y"], e["scale"])
            if base_health <= 0:
                base_health = 0
                game_over   = True
            continue

        raw_dx = -e["x"] / dist_to_base
        raw_dy = -e["y"] / dist_to_base

        dx, dy = _steer_around_obstacles(e["x"], e["y"], raw_dx, raw_dy)

        current_speed = e["speed"] * (0.4 if enemy_slow_timer > 0 else 1.0)

        e["x"]    += dx * current_speed
        e["y"]    += dy * current_speed
        e["anim_t"] += 0.12 * (0.4 if enemy_slow_timer > 0 else 1.0) 

    enemies = [e for e in enemies if e["alive"]]

    if not spawn_queue and not enemies and not wave_complete:
        wave_complete  = True
        wave_started   = False
        current_wave  += 1
        if current_wave >= len(WAVES):
            pass
        else:
            wave_pause_timer = WAVE_PAUSE_FRAMES

def _spawn_explosion(x, y, scale):
    explosions.append({
        "x": x, "y": y,
        "frame": 0,
        "max_frame": 30,
        "scale": scale,
    })

def draw_explosions():
    for e in explosions:
        t       = e["frame"] / e["max_frame"]         
        radius  = e["scale"] * 30 * (1 + t * 3)      
        alpha_r = 1.0 - t                              
        glPushMatrix()
        glTranslatef(e["x"], e["y"], 15)
        glScalef(radius, radius, radius)              
        glColor3f(1.0, 0.55 * alpha_r, 0.0)
        gluSphere(gluNewQuadric(), 1, 12, 8)
        glScalef(0.5, 0.5, 0.5)
        glColor3f(1.0, 1.0, alpha_r)
        gluSphere(gluNewQuadric(), 1, 8, 6)
        glPopMatrix()

def _draw_fast_enemy(e):
    anim = math.sin(e["anim_t"]) * 8    

    for side in (-1, 1):
        glPushMatrix()
        glTranslatef(side * 7, 0, 0)
        glRotatef(side * anim, 1, 0, 0)
        glColor3f(0.15, 0.15, 0.15)
        gluCylinder(gluNewQuadric(), 5, 4, 30, 8, 3)
        glPopMatrix()

    glPushMatrix()
    glTranslatef(0, 0, 28)
    glColor3f(*e["color_body"])
    glScalef(1.0, 0.7, 1.0)
    glutSolidCube(28)
    glPopMatrix()

    for side in (-1, 1):
        glPushMatrix()
        glTranslatef(side * 20, 0, 33)
        glRotatef(90 + side * anim * 0.5, 0, 1, 0)
        glColor3f(*e["color_body"])
        gluCylinder(gluNewQuadric(), 4, 3, 20, 8, 3)
        glPopMatrix()

    glPushMatrix()
    glTranslatef(0, 0, 54)
    glColor3f(*e["color_head"])
    gluSphere(gluNewQuadric(), 13, 12, 8)
    glPopMatrix()

def _draw_tank_enemy(e):
    anim = math.sin(e["anim_t"]) * 5

    for side in (-1, 1):
        glPushMatrix()
        glTranslatef(side * 12, 0, 0)
        glRotatef(side * anim, 1, 0, 0)
        glColor3f(0.10, 0.10, 0.12)
        gluCylinder(gluNewQuadric(), 9, 8, 35, 10, 3)
        glPopMatrix()

    glPushMatrix()
    glTranslatef(0, 0, 33)
    glColor3f(*e["color_body"])
    glScalef(1.6, 0.9, 1.2)               
    glutSolidCube(35)
    glPopMatrix()

    for side in (-1, 1):
        glPushMatrix()
        glTranslatef(side * 32, 0, 45)
        glScalef(0.6, 0.5, 0.5)
        glColor3f(0.20, 0.20, 0.45)
        glutSolidCube(30)
        glPopMatrix()

    for side in (-1, 1):
        glPushMatrix()
        glTranslatef(side * 32, 0, 35)
        glRotatef(90 + side * anim * 0.4, 0, 1, 0)
        glColor3f(*e["color_body"])
        gluCylinder(gluNewQuadric(), 7, 5, 25, 10, 3)
        glPopMatrix()

    glPushMatrix()
    glTranslatef(0, 0, 66)
    glColor3f(*e["color_head"])
    gluSphere(gluNewQuadric(), 18, 14, 10)
    glTranslatef(0, 0, 14)
    glColor3f(0.12, 0.12, 0.25)
    glScalef(1, 1, 0.5)
    glutSolidCube(26)
    glPopMatrix()

def _draw_health_bar(e):
    hp_frac = e["health"] / e["max_health"]
    bar_w   = 40
    bar_h   = 6
    head_z  = (70 if e["type"] == "fast" else 100) * e["scale"] + 10

    glPushMatrix()
    glTranslatef(0, 0, head_z)

    glColor3f(0.4, 0.05, 0.05)
    glScalef(bar_w, bar_h, 1)
    glutSolidCube(1)

    glPopMatrix()

    glPushMatrix()
    glTranslatef(0, 0, head_z)
    offset_x = (hp_frac - 1.0) * bar_w * 0.5   
    glTranslatef(offset_x, 1, 0)
    r = 1.0 - hp_frac
    g = hp_frac
    glColor3f(r, g, 0.0)
    glScalef(bar_w * hp_frac, bar_h, 1)
    glutSolidCube(1)
    glPopMatrix()

def draw_enemies():
    for e in enemies:
        if not e["alive"]:
            continue

        angle_to_base = math.degrees(math.atan2(-e["y"], -e["x"]))

        glPushMatrix()
        glTranslatef(e["x"], e["y"], 2)          
        glRotatef(angle_to_base - 90, 0, 0, 1)  
        glScalef(e["scale"], e["scale"], e["scale"])

        if e["type"] == "fast":
            _draw_fast_enemy(e)
        else:
            _draw_tank_enemy(e)

        _draw_health_bar(e)
        glPopMatrix()

    draw_explosions()

def damage_enemy(enemy, amount):
    enemy["health"] -= amount
    if enemy["health"] <= 0:
        enemy["alive"] = False
        _spawn_explosion(enemy["x"], enemy["y"], enemy["scale"])
        return True
    return False

def draw_enemy_hud():
    hp_frac = base_health / base_max_health
    
    draw_text(10, WINDOW_H - 80, f"BASE HP:", color=(1, 1, 1))

    if current_wave < len(WAVES):
        draw_text(10, WINDOW_H - 105,
                  f"Wave {current_wave + 1} / {len(WAVES)}",
                  color=(1.0, 0.85, 0.3))
    else:
        draw_text(10, WINDOW_H - 105, "All waves complete!", color=(0.3, 1.0, 0.3))

    draw_text(10, WINDOW_H - 130,
              f"Enemies: {len(enemies)}  |  Spawning: {len(spawn_queue)}",
              color=(1.0, 0.6, 0.3))
    
    if base_health_boost_timer > 0:
        secs_left = base_health_boost_timer // 60
        draw_text(10, WINDOW_H - 155, 
                  f"HEALTH OVERDRIVE: {secs_left}s", 
                  color=(0.2, 1.0, 0.2))
    
    if enemy_slow_timer > 0:
        secs_left = enemy_slow_timer // 60
        draw_text(10, WINDOW_H - 180, 
                  f"ENEMY SLOW: {secs_left}s", 
                  color=(0.4, 0.8, 1.0))
        
    color = (0.2, 1.0, 0.2) if hp_frac > 0.5 else (1.0, 0.6, 0.0) if hp_frac > 0.25 else (1.0, 0.1, 0.1)
    draw_text(90, WINDOW_H - 80, f"{base_health} / {base_max_health}", color=color)

    if game_over:
        draw_text(WINDOW_W // 2 - 110, WINDOW_H // 2 + 20,
                  "GAME OVER — Base Destroyed",
                  font=GLUT_BITMAP_HELVETICA_18,
                  color=(1.0, 0.1, 0.1))
        draw_text(WINDOW_W // 2 - 70, WINDOW_H // 2 - 20,
                  "Press R to restart",
                  color=(1.0, 1.0, 0.4))

    if current_wave >= len(WAVES) and not game_over:
        draw_text(WINDOW_W // 2 - 100, WINDOW_H // 2,
                  "VICTORY — All waves defeated!",
                  font=GLUT_BITMAP_HELVETICA_18,
                  color=(0.2, 1.0, 0.3))

def draw_crosshair():
    if camera_mode != 1:
        return   

    cx = WINDOW_W // 2
    cy = WINDOW_H // 2

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_W, 0, WINDOW_H)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glColor3f(1.0, 1.0, 1.0)
    glLineWidth(2)

    size = 10

    glBegin(GL_LINES)
    glVertex3f(cx - size, cy, -0.99)
    glVertex3f(cx + size, cy, -0.99)
    glVertex3f(cx, cy - size, -0.99)
    glVertex3f(cx, cy + size, -0.99)
    glEnd()

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def reset_game():
    global base_health, current_wave, wave_started, wave_complete
    global game_over, enemies, spawn_queue, spawn_timer
    global wave_pause_timer, explosions
    global boosts, boost_spawn_timer, base_health_boost_timer, base_health_boost_amount

    boosts = []
    boost_spawn_timer = 300
    base_health_boost_timer = 0
    base_health_boost_amount = 0
    base_health      = base_max_health
    current_wave     = 0
    wave_started     = False
    wave_complete    = False
    game_over        = False
    enemies          = []
    spawn_queue      = []
    spawn_timer      = 0
    wave_pause_timer = 0
    explosions       = []
    reset_player()           

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18, color=(1, 1, 1)):
    glColor3f(*color)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_W, 0, WINDOW_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_sky():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_W, 0, WINDOW_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glBegin(GL_QUADS)
    glColor3f(0.56, 0.71, 0.56)
    glVertex2f(0,        WINDOW_H)
    glVertex2f(WINDOW_W, WINDOW_H)
    glColor3f(0.13, 0.20, 0.10)
    glVertex2f(WINDOW_W, 0)
    glVertex2f(0,        0)
    glEnd()
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_terrain():
    segments = 120

    glBegin(GL_TRIANGLE_STRIP)
    for i in range(segments + 1):
        a = 2 * math.pi * i / segments
        cos_a, sin_a = math.cos(a), math.sin(a)
        glColor3f(0.12, 0.28, 0.08)
        glVertex3f(MAP_RADIUS * cos_a, MAP_RADIUS * sin_a, 0)
        glColor3f(0.38, 0.30, 0.18)
        glVertex3f((MAP_RADIUS + 400) * cos_a, (MAP_RADIUS + 400) * sin_a, -5)
    glEnd()

    step = 100
    r2   = MAP_RADIUS * MAP_RADIUS
    glBegin(GL_QUADS)
    x = -MAP_RADIUS
    while x < MAP_RADIUS:
        y = -MAP_RADIUS
        while y < MAP_RADIUS:
            cx, cy = x + step / 2, y + step / 2
            if cx * cx + cy * cy <= r2:
                tile = int((x / step + y / step)) % 2
                if tile == 0:
                    glColor3f(0.13, 0.38, 0.10)
                else:
                    glColor3f(0.16, 0.44, 0.12)
                glVertex3f(x,        y,        1)
                glVertex3f(x + step, y,        1)
                glVertex3f(x + step, y + step, 1)
                glVertex3f(x,        y + step, 1)
            y += step
        x += step
    glEnd()

    glBegin(GL_TRIANGLE_FAN)
    glColor3f(0.55, 0.55, 0.52)
    glVertex3f(0, 0, 2)
    for i in range(segments + 1):
        a = 2 * math.pi * i / segments
        glVertex3f(220 * math.cos(a), 220 * math.sin(a), 2)
    glEnd()

    wall_r_inner = MAP_RADIUS - 5
    wall_r_outer = MAP_RADIUS + 5
    wall_h       = 80
    glBegin(GL_QUAD_STRIP)
    for i in range(segments + 1):
        a     = 2 * math.pi * i / segments
        cos_a = math.cos(a)
        sin_a = math.sin(a)
        glColor3f(0.30, 0.28, 0.25)
        glVertex3f(wall_r_outer * cos_a, wall_r_outer * sin_a, 0)
        glVertex3f(wall_r_outer * cos_a, wall_r_outer * sin_a, wall_h)
    glEnd()
    glBegin(GL_QUAD_STRIP)
    for i in range(segments + 1):
        a     = 2 * math.pi * i / segments
        cos_a = math.cos(a)
        sin_a = math.sin(a)
        glColor3f(0.22, 0.20, 0.18)
        glVertex3f(wall_r_inner * cos_a, wall_r_inner * sin_a, 0)
        glVertex3f(wall_r_inner * cos_a, wall_r_inner * sin_a, wall_h)
    glEnd()
    glBegin(GL_TRIANGLE_STRIP)
    glColor3f(0.35, 0.32, 0.28)
    for i in range(segments + 1):
        a     = 2 * math.pi * i / segments
        cos_a = math.cos(a)
        sin_a = math.sin(a)
        glVertex3f(wall_r_inner * cos_a, wall_r_inner * sin_a, wall_h)
        glVertex3f(wall_r_outer * cos_a, wall_r_outer * sin_a, wall_h)
    glEnd()

def draw_tower():
    glPushMatrix()

    glColor3f(0.48, 0.48, 0.45)
    glPushMatrix()
    glScalef(1, 1, 0.3)
    draw_disk(230, 40)
    glPopMatrix()

    glColor3f(0.42, 0.44, 0.40)
    gluCylinder(gluNewQuadric(), 120, 130, 350, 30, 20)

    for i in range(8):
        angle = i * 45
        bx    = 128 * math.cos(math.radians(angle))
        by    = 128 * math.sin(math.radians(angle))
        glPushMatrix()
        glTranslatef(bx, by, 120 + i * 20)
        glColor3f(0.30, 0.32, 0.28)
        gluCylinder(gluNewQuadric(), 135, 135, 12, 30, 4)
        glPopMatrix()

    glTranslatef(0, 0, 350)
    glColor3f(0.50, 0.50, 0.48)
    draw_disk(155, 40)

    merlon_count = 16
    for i in range(merlon_count):
        angle = i * (360 / merlon_count)
        mx    = 145 * math.cos(math.radians(angle))
        my    = 145 * math.sin(math.radians(angle))
        glPushMatrix()
        glTranslatef(mx, my, 0)
        glRotatef(angle, 0, 0, 1)
        glColor3f(0.38, 0.38, 0.36)
        glScalef(1, 1, 1.6)
        glutSolidCube(22)
        glPopMatrix()

    glColor3f(0.55, 0.30, 0.10)
    gluCylinder(gluNewQuadric(), 3, 3, 80, 10, 5)
    glTranslatef(0, 0, 80)
    glColor3f(0.0, 0.55, 0.15)
    glBegin(GL_TRIANGLES)
    glVertex3f(0,  0,  0)
    glVertex3f(45, 12, 0)
    glVertex3f(0,  25, 0)
    glEnd()

    glPopMatrix()

def draw_trees():
    for (x, y, scale) in TREE_POSITIONS:
        glPushMatrix()
        glTranslatef(x, y, 1)
        glScalef(scale, scale, scale)
        glColor3f(0.38, 0.22, 0.09)
        gluCylinder(gluNewQuadric(), 10, 8, 80, 10, 5)
        glTranslatef(0, 0, 70)
        glColor3f(0.08, 0.45, 0.08)
        gluCylinder(gluNewQuadric(), 38, 0, 80, 14, 8)
        glTranslatef(0, 0, 45)
        glColor3f(0.06, 0.38, 0.06)
        gluCylinder(gluNewQuadric(), 26, 0, 60, 14, 8)
        glPopMatrix()

def draw_boulders():
    for (x, y, scale) in BOULDER_POSITIONS:
        glPushMatrix()
        glTranslatef(x, y, 1)
        glScalef(scale, scale * 0.70, scale * 0.65)
        glColor3f(0.42, 0.40, 0.38)
        gluSphere(gluNewQuadric(), 35, 14, 10)
        glPopMatrix()

def _draw_single_truck():
    glPushMatrix()
    glColor3f(0.22, 0.30, 0.16)
    glScalef(1.8, 0.9, 0.5)
    glutSolidCube(70)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(55, 0, 30)
    glColor3f(0.25, 0.34, 0.18)
    glScalef(0.8, 0.85, 0.65)
    glutSolidCube(70)
    glPopMatrix()

    for wx, wy in [(-45, 36), (-45, -36), (45, 36), (45, -36)]:
        glPushMatrix()
        glTranslatef(wx, wy, -18)
        glRotatef(90, 1, 0, 0)
        glColor3f(0.12, 0.12, 0.12)
        gluCylinder(gluNewQuadric(), 14, 14, 18, 16, 4)
        glColor3f(0.22, 0.22, 0.22)
        draw_disk(14, 16)
        glPopMatrix()

    glPushMatrix()
    glTranslatef(92, 0, 36)
    glColor3f(0.20, 0.25, 0.32)
    glScalef(0.07, 0.65, 0.50)
    glutSolidCube(70)
    glPopMatrix()

def draw_trucks():
    for (x, y, angle) in TRUCK_POSITIONS:
        glPushMatrix()
        glTranslatef(x, y, 20)
        glRotatef(angle, 0, 0, 1)
        _draw_single_truck()
        glPopMatrix()

def _draw_sandbag_cluster():
    for bx, bz in [(-16, 0), (0, 0), (16, 0)]:
        glPushMatrix()
        glTranslatef(bx, 0, bz)
        glScalef(1.2, 0.6, 0.55)
        glColor3f(0.65, 0.58, 0.38)
        gluSphere(gluNewQuadric(), 14, 10, 8)
        glPopMatrix()
    for bx, bz in [(-8, 14), (8, 14)]:
        glPushMatrix()
        glTranslatef(bx, 0, bz)
        glScalef(1.2, 0.6, 0.55)
        glColor3f(0.60, 0.53, 0.33)
        gluSphere(gluNewQuadric(), 14, 10, 8)
        glPopMatrix()

def draw_sandbags():
    for (x, y, angle) in SANDBAG_POSITIONS:
        glPushMatrix()
        glTranslatef(x, y, 1)
        glRotatef(angle + 90, 0, 0, 1)
        _draw_sandbag_cluster()
        glPopMatrix()

def setup_camera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, WINDOW_W / WINDOW_H, 1.0, 6000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    px, py, pz = _player_world_pos()

    if camera_mode == 0:
        
        camX = camera_distance * math.cos(math.radians(camera_angle))
        camY = camera_distance * math.sin(math.radians(camera_angle))
        camZ = camera_height

        gluLookAt(camX, camY, camZ,
                0, 0, 200,
                0, 0, 1)

    else:
        
        rad = math.radians(player_gun_angle)

        camX = px + math.sin(rad) * (18 * 1.5)
        camY = py + math.cos(rad) * (18 * 1.5)
        camZ = pz + (66 * 1.5)   

        lookX = camX + math.sin(rad) * 200
        lookY = camY + math.cos(rad) * 200

        gluLookAt(camX, camY, camZ,
                lookX, lookY, camZ - 15,  
                0, 0, 1)

def draw_scene():
    draw_terrain()
    draw_trees()
    draw_boulders()
    draw_sandbags()
    draw_trucks()
    draw_tower()
    draw_boosts()
    draw_player()           
    draw_player_bullets()   
    draw_muzzle_particles() 
    draw_enemies()          

def _can_move_to(nx, ny):
    
    if math.hypot(nx, ny) < 160:
        return False
    
    if math.hypot(nx, ny) > MAP_RADIUS - 30:
        return False
    
    for (ox, oy, orad) in OBSTACLE_CIRCLES:
        
        if math.hypot(nx - ox, ny - oy) < (orad + 15):
            return False
    
    for (tx, ty, _) in TRUCK_POSITIONS:
        if math.hypot(nx - tx, ny - ty) < 90: 
            return False   
    
    for (sx, sy, _) in SANDBAG_POSITIONS:
        if math.hypot(nx - sx, ny - sy) < 55:
            return False    
    return True

def keyboard_listener(key, x, y):
    global player_x, player_y, player_angle, player_gun_angle, current_weapon, weapon_switch_anim
    global sprint_active, sprint_timer, sprint_cooldown_timer

    if key == b'r' or key == b'R':
        reset_game()
        return

    if game_over:
        return

    speed = PLAYER_SPRINT_SPEED if sprint_active else PLAYER_MOVE_SPEED
    rad = math.radians(player_gun_angle)

    if key == b'w' or key == b'W':
        new_x = player_x + speed * math.sin(rad)
        new_y = player_y + speed * math.cos(rad)
        if _can_move_to(new_x, new_y):
            player_x, player_y = new_x, new_y
        elif _can_move_to(new_x, player_y):     
            player_x = new_x
        elif _can_move_to(player_x, new_y):     
            player_y = new_y
        player_angle = player_gun_angle 
    elif key == b's' or key == b'S':
        new_x = player_x - speed * math.sin(rad)
        new_y = player_y - speed * math.cos(rad)
        
        if _can_move_to(new_x, new_y):
            player_x, player_y = new_x, new_y
        elif _can_move_to(new_x, player_y):     
            player_x = new_x
        elif _can_move_to(player_x, new_y):     
            player_y = new_y
        player_angle = player_gun_angle

    elif key == b'a' or key == b'A':
        player_gun_angle -= PLAYER_GUN_ROTATE
    elif key == b'd' or key == b'D':
        player_gun_angle += PLAYER_GUN_ROTATE
    
    elif key == b' ':   
        if not sprint_active and sprint_cooldown_timer <= 0:
            sprint_active         = True
            sprint_timer          = SPRINT_DURATION
            sprint_cooldown_timer = SPRINT_COOLDOWN

    elif key == b'q' or key == b'Q':
        if current_weapon == 1:
            _fire_rpg()
        else:
            current_weapon     = 1
            weapon_switch_anim = 20
            _fire_rpg()

    elif key == b'e' or key == b'E':
        current_weapon     = 1 - current_weapon
        weapon_switch_anim = 20

def special_key_listener(key, x, y):
    global camera_angle, camera_height, camera_distance

    if key == GLUT_KEY_LEFT:
        camera_angle -= 5
    elif key == GLUT_KEY_RIGHT:
        camera_angle += 5
    elif key == GLUT_KEY_UP:
        camera_height = max(camera_min_h, camera_height - 30)
    elif key == GLUT_KEY_DOWN:
        camera_height = min(camera_max_h, camera_height + 30)

def mouse_listener(button, state, x, y):
    global camera_mode
    if game_over:
        return
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        if current_weapon == 0:
            _fire_rifle()
        else:
            _fire_rpg()
    elif button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        camera_mode = 1 - camera_mode

def idle():
    update_player()         
    update_enemies()    
    update_boosts()    
    glutPostRedisplay()

def show_screen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, WINDOW_W, WINDOW_H)
    draw_sky()
    setup_camera()
    draw_scene()

    draw_text(10, WINDOW_H - 30,
              "Arrow keys: rotate/tilt camera  |  R: restart",
              color=(1.0, 1.0, 0.6))
    
    draw_text(10, WINDOW_H - 55,
              "W/S: move  A/D: aim  E: switch weapon  Q: RPG  LClick: fire  Space: sprint",
              color=(0.7, 1.0, 0.7))

    draw_enemy_hud()
    draw_player_hud()
    draw_crosshair()
    glutSwapBuffers()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_W, WINDOW_H)
    glutInitWindowPosition(50, 50)
    glutCreateWindow(b"3D Military Base Defense")

    glClearColor(0.10, 0.15, 0.10, 1.0)

    glutDisplayFunc(show_screen)
    glutKeyboardFunc(keyboard_listener)
    glutSpecialFunc(special_key_listener)
    glutMouseFunc(mouse_listener)
    glutIdleFunc(idle)

    glutMainLoop()

if __name__ == "__main__":
    main()