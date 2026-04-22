import pygame
import random
import math
import os

# --- Configurations ---
WIDTH, HEIGHT = 1080, 1920
FPS = 60
ARENA_CENTER = (WIDTH // 2, HEIGHT // 2 + 100)
ARENA_RADIUS = 480
GRID_SIZE = 60

COLORS = {
    'bg': (5, 5, 20),
    'grid': (40, 40, 70),
    'arena_border': (255, 255, 255),
    'text_primary': (255, 255, 255),
    'red': (255, 60, 60),
    'green': (60, 255, 100),
    'blue': (60, 160, 255),
    'yellow': (255, 220, 0),
    'orange': (255, 140, 0),
    'cyan': (0, 255, 255),
    'purple': (200, 80, 255),
    'white': (255, 255, 255),
    'item_bg': (255, 255, 255, 150)
}

# --- Math Helpers ---
def distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def normalize(v):
    mag = math.hypot(v[0], v[1])
    if mag == 0: return (0, 0)
    return (v[0]/mag, v[1]/mag)

# --- Visual Effects ---
class Particle:
    def __init__(self, x, y, color, vx, vy, life, size=5):
        self.x = x
        self.y = y
        self.color = color
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.size = size

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        self.size *= 0.95

    def draw(self, surface):
        alpha = int((self.life / self.max_life) * 255)
        s = pygame.Surface((int(self.size*2), int(self.size*2)), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color[:3], alpha), (int(self.size), int(self.size)), int(self.size))
        surface.blit(s, (int(self.x - self.size), int(self.y - self.size)))

class FloatingText:
    def __init__(self, x, y, text, color):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.life = 40
        self.vy = -2

    def update(self):
        self.y += self.vy
        self.life -= 1

    def draw(self, surface, font):
        alpha = int((self.life / 40) * 255)
        ts = font.render(self.text, True, self.color)
        ts.set_alpha(alpha)
        surface.blit(ts, (self.x - ts.get_width()//2, self.y))

class EffectManager:
    def __init__(self):
        self.particles = []
        self.floating_texts = []
        self.shake_amount = 0

    def add_text(self, x, y, text, color):
        self.floating_texts.append(FloatingText(x, y, text, color))

    def add_explosion(self, x, y, color, count=15):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 8)
            self.particles.append(Particle(x, y, color, math.cos(angle)*speed, math.sin(angle)*speed, random.randint(20, 40), random.randint(4, 8)))

    def add_muzzle_flash(self, x, y, color):
        for _ in range(5):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(5, 12)
            self.particles.append(Particle(x, y, color, math.cos(angle)*speed, math.sin(angle)*speed, 10, 4))

    def update(self):
        for p in self.particles[:]:
            p.update()
            if p.life <= 0:
                self.particles.remove(p)
        for t in self.floating_texts[:]:
            t.update()
            if t.life <= 0:
                self.floating_texts.remove(t)
        if self.shake_amount > 0:
            self.shake_amount *= 0.9

    def draw(self, surface, font_small):
        for p in self.particles:
            p.draw(surface)
        for t in self.floating_texts:
            t.draw(surface, font_small)

    def shake(self, amount):
        self.shake_amount = amount

# --- Weapon System ---
class Weapon:
    def __init__(self, name, fire_rate, damage, projectile_speed, color, projectile_count=1, spread=0):
        self.name = name
        self.fire_rate = fire_rate
        self.damage = damage
        self.projectile_speed = projectile_speed
        self.color = color
        self.projectile_count = projectile_count
        self.spread = spread

WEAPONS = {
    'Pistol':  Weapon('Pistol',  45,  15, 12, (180, 180, 200)),
    'AK47':    Weapon('AK47',    12,  10, 16, (255, 200,  60)),
    'M4':      Weapon('M4',       8,   8, 20, (120, 220, 120)),
    'Shotgun': Weapon('Shotgun', 60,  14, 13, (255, 255, 255), 6, 0.38),
    'Minigun': Weapon('Minigun',  4,   5, 22, (255, 255,  50)),
    'RPG':     Weapon('RPG',    180,  90, 9,  (255,  80,  30)),
}

def draw_gun(surface, ex, ey, angle, weapon_name):
    """Draw a stylised gun silhouette at (ex,ey) pointing in `angle` radians."""
    import math
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    # helper: rotate offset (ox,oy) around entity centre and draw rect
    def rot_rect(ox, oy, w, h, color, thickness=0):
        cx = ex + cos_a * ox - sin_a * oy
        cy = ey + sin_a * ox + cos_a * oy
        pts = []
        for dx, dy in [(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)]:
            rx = cos_a*dx - sin_a*dy
            ry = sin_a*dx + cos_a*dy
            pts.append((cx+rx, cy+ry))
        if thickness == 0:
            pygame.draw.polygon(surface, color, pts)
        else:
            pygame.draw.polygon(surface, color, pts, thickness)

    def rot_circle(ox, oy, r, color):
        cx = int(ex + cos_a*ox - sin_a*oy)
        cy = int(ey + sin_a*ox + cos_a*oy)
        pygame.draw.circle(surface, color, (cx, cy), r)

    DARK   = (30, 30, 30)
    GREY   = (90, 90, 90)
    LGREY  = (140, 140, 140)
    BROWN  = (100,  60,  20)
    TAN    = (160, 110,  60)

    if weapon_name == 'Pistol':
        rot_rect(30,  0,  46, 12, GREY)        # body
        rot_rect(46,  0,  14,  8, DARK)        # barrel tip
        rot_rect(18, 10,  20, 18, DARK)        # grip
        rot_circle(44, 0, 5, LGREY)            # muzzle

    elif weapon_name == 'AK47':
        rot_rect(34,  0,  60, 13, GREY)        # receiver
        rot_rect(60,  0,  24,  8, DARK)        # barrel
        rot_rect(10,  0,  30, 10, TAN)         # stock
        rot_rect(30, 14,  18, 22, BROWN)       # curved magazine
        rot_rect(28, 22,  10, 10, BROWN)       # mag bottom curve
        rot_circle(71, 0, 5, DARK)             # muzzle

    elif weapon_name == 'M4':
        rot_rect(34,  0,  62, 12, DARK)        # receiver
        rot_rect(60,  0,  26,  7, GREY)        # barrel
        rot_rect( 8,  0,  28, 10, TAN)         # stock
        rot_rect(60,  -9, 24,  6, DARK)        # top rail
        rot_rect(30, 12,  20, 18, GREY)        # vertical magazine
        rot_circle(72, 0, 4, LGREY)            # muzzle

    elif weapon_name == 'Shotgun':
        rot_rect(30,  3,  58, 10, TAN)         # top barrel
        rot_rect(30, -3,  58, 10, TAN)         # bottom barrel
        rot_rect(58, 0,   16,  22, DARK)       # barrel band
        rot_rect( 5, 0,   30,  14, BROWN)      # stock
        rot_circle(58, 0, 5, GREY)             # muzzle

    elif weapon_name == 'Minigun':
        for k, yo in enumerate([-12, -6, 0, 6, 12]):
            col = LGREY if k % 2 == 0 else GREY
            rot_rect(38, yo, 58, 7, col)       # 5 rotating barrels
        rot_rect(14, 0, 24, 28, DARK)          # motor housing
        rot_circle(66, 0, 8, DARK)             # muzzle ring

    elif weapon_name == 'RPG':
        rot_rect(26,  0, 52, 16, DARK)         # tube body
        rot_rect(52,  0, 24, 22, (80,40,10))   # warhead cone base
        rot_rect(66,  0, 14, 12, (200, 60, 0)) # warhead nose
        rot_rect(-2,  0, 20, 22, GREY)         # shoulder rest
        rot_circle(72, 0, 6, (255, 80, 0))     # nose tip

# --- Item Drops ---
class Item:
    def __init__(self, x, y, item_type):
        self.x = x
        self.y = y
        self.type = item_type # 'weapon', 'health', 'shield'
        self.data = None
        self.radius = 25
        self.pulse = 0
        
        if self.type == 'weapon':
            self.data = random.choice(['AK47', 'M4', 'Shotgun', 'Minigun', 'RPG'])
            self.color = WEAPONS[self.data].color
        elif self.type == 'health':
            self.color = COLORS['red']
        elif self.type == 'shield':
            self.color = COLORS['cyan']

    def update(self):
        self.pulse += 0.1

    def draw(self, surface):
        glow_size = self.radius + math.sin(self.pulse) * 5
        s = pygame.Surface((glow_size*4, glow_size*4), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, 100), (int(glow_size*2), int(glow_size*2)), int(glow_size))
        surface.blit(s, (int(self.x - glow_size*2), int(self.y - glow_size*2)))
        
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, (255, 255, 255), (int(self.x), int(self.y)), self.radius, 3)
        
        # Icon/Text
        font = pygame.font.SysFont('Arial', 20, bold=True)
        text = self.data[0] if self.type == 'weapon' else self.type[0].upper()
        ts = font.render(text, True, (255, 255, 255))
        tr = ts.get_rect(center=(self.x, self.y))
        surface.blit(ts, tr)

# --- Entity Class ---
class Entity:
    def __init__(self, x, y, radius, color, shape_type='circle', hp=100, name="Player"):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.shape_type = shape_type
        self.max_hp = hp
        self.hp = hp
        self.name = name
        
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 4)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        
        self.weapon = WEAPONS['Pistol']
        self.shoot_cooldown = 0
        self.shield = 0
        self.emotion = 'neutral'
        self.glow_timer = 0
        
    def move(self):
        self.x += self.vx
        self.y += self.vy
        
        dist_to_center = distance((self.x, self.y), ARENA_CENTER)
        if dist_to_center + self.radius > ARENA_RADIUS:
            nx, ny = normalize((self.x - ARENA_CENTER[0], self.y - ARENA_CENTER[1]))
            overlap = dist_to_center + self.radius - ARENA_RADIUS
            self.x -= nx * overlap
            self.y -= ny * overlap
            dot = self.vx * nx + self.vy * ny
            self.vx -= 2 * dot * nx
            self.vy -= 2 * dot * ny
            self.vx *= 1.01
            self.vy *= 1.01
            speed = math.hypot(self.vx, self.vy)
            if speed > 8:
                self.vx = (self.vx / speed) * 8
                self.vy = (self.vy / speed) * 8
            self.glow_timer = 5

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.shield > 0:
            self.shield -= 1
            
        if self.hp < self.max_hp * 0.4:
            self.emotion = 'sad'
        else:
            self.emotion = 'neutral'

    def draw(self, surface):
        # Shield
        if self.shield > 0:
            s = pygame.Surface((self.radius*3, self.radius*3), pygame.SRCALPHA)
            pygame.draw.circle(s, (0, 255, 255, 100), (int(self.radius*1.5), int(self.radius*1.5)), int(self.radius*1.3), 5)
            surface.blit(s, (int(self.x - self.radius*1.5), int(self.y - self.radius*1.5)))

        # Body
        body_color = self.color
        if self.glow_timer > 0:
            body_color = (255, 255, 255)
            self.glow_timer -= 1
            
        if self.shape_type == 'circle':
            pygame.draw.circle(surface, body_color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(surface, (255, 255, 255), (int(self.x), int(self.y)), self.radius, 4)
        else:
            rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius*2, self.radius*2)
            pygame.draw.rect(surface, body_color, rect)
            pygame.draw.rect(surface, (255, 255, 255), rect, 4)
            
        # Face
        self.draw_face(surface)
        
        # Weapon — draw real gun shape
        if self.weapon:
            target_angle = math.atan2(self.vy, self.vx)
            draw_gun(surface, self.x, self.y, target_angle, self.weapon.name)
            


    def draw_face(self, surface):
        x, y = self.x, self.y
        r = self.radius
        eye_size = r // 4
        eye_off = r // 2.5
        
        # Eyes
        pygame.draw.circle(surface, (255, 255, 255), (int(x - eye_off), int(y - r//4)), eye_size)
        pygame.draw.circle(surface, (255, 255, 255), (int(x + eye_off), int(y - r//4)), eye_size)
        pygame.draw.circle(surface, (0, 0, 0), (int(x - eye_off), int(y - r//4)), eye_size // 2)
        pygame.draw.circle(surface, (0, 0, 0), (int(x + eye_off), int(y - r//4)), eye_size // 2)
        
        # Mouth
        if self.emotion == 'neutral':
            pygame.draw.arc(surface, (0, 0, 0), (x - r//2, y + r//8, r, r//3), math.pi, 2*math.pi, 3)
        else:
            pygame.draw.arc(surface, (0, 0, 0), (x - r//2, y + r//3, r, r//3), 0, math.pi, 3)

class Projectile:
    def __init__(self, x, y, vx, vy, weapon, owner):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.weapon = weapon
        self.owner = owner
        self.color = weapon.color
        # Size and life per weapon
        if weapon.name == 'RPG':
            self.radius = 10
            self.life   = 200
        elif weapon.name == 'Shotgun':
            self.radius = 5
            self.life   = 40
        elif weapon.name == 'Minigun':
            self.radius = 4
            self.life   = 80
        else:
            self.radius = 7
            self.life   = 120
        self.trail = []   # list of (x, y) for trail rendering

    def update(self):
        self.trail.append((self.x, self.y))
        if len(self.trail) > 12:
            self.trail.pop(0)
        self.x += self.vx
        self.y += self.vy
        self.life -= 1

    def draw(self, surface):
        wname = self.weapon.name

        if wname == 'RPG':
            # Smoke trail
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int((i / len(self.trail)) * 160)
                r = 12 - i
                if r < 1: continue
                s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                pygame.draw.circle(s, (180, 100, 50, alpha), (r, r), r)
                surface.blit(s, (int(tx - r), int(ty - r)))
            # Rocket body
            angle = math.atan2(self.vy, self.vx)
            cos_a, sin_a = math.cos(angle), math.sin(angle)
            cx, cy = self.x, self.y
            def rp(ox, oy):
                return (cx + cos_a*ox - sin_a*oy, cy + sin_a*ox + cos_a*oy)
            pygame.draw.polygon(surface, (200, 80, 0), [rp(16,0), rp(-8, 7), rp(-8,-7)])
            pygame.draw.circle(surface, (255, 220, 50), (int(cx), int(cy)), 5)

        elif wname in ('AK47', 'M4'):
            # Tracer — glowing yellow-orange dot with short trail
            for i, (tx, ty) in enumerate(self.trail[-6:]):
                alpha = int((i / 6) * 180)
                s = pygame.Surface((8, 8), pygame.SRCALPHA)
                pygame.draw.circle(s, (*self.color, alpha), (4, 4), 4)
                surface.blit(s, (int(tx - 4), int(ty - 4)))
            alpha = min(255, self.life * 10)
            s = pygame.Surface((14, 14), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (7, 7), 7)
            surface.blit(s, (int(self.x - 7), int(self.y - 7)))

        elif wname == 'Shotgun':
            # Small white pellet
            alpha = min(255, self.life * 20)
            s = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 255, 255, alpha), (5, 5), 5)
            surface.blit(s, (int(self.x - 5), int(self.y - 5)))

        elif wname == 'Minigun':
            # Tiny bright spark
            alpha = min(255, self.life * 15)
            s = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 255, 100, alpha), (5, 5), 5)
            surface.blit(s, (int(self.x - 5), int(self.y - 5)))

        else:  # Pistol
            alpha = min(255, self.life * 15)
            s = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (self.radius, self.radius), self.radius)
            surface.blit(s, (int(self.x - self.radius), int(self.y - self.radius)))

# --- Main App ---
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Arena Battle Royale")
    clock = pygame.time.Clock()
    
    font_large = pygame.font.SysFont('Impact', 80)
    font_small = pygame.font.SysFont('Arial', 30, bold=True)
    
    effects = EffectManager()
    entities = []
    
    # Spawn Players
    colors = [COLORS['red'], COLORS['green'], COLORS['blue'], COLORS['yellow'], COLORS['orange'], COLORS['purple']]
    for i in range(6):
        angle = (i / 6) * 2 * math.pi
        r = ARENA_RADIUS - 100
        x = ARENA_CENTER[0] + math.cos(angle) * r
        y = ARENA_CENTER[1] + math.sin(angle) * r
        shape = 'square' if i % 2 == 0 else 'circle'
        entities.append(Entity(x, y, 60, colors[i], shape, 150, f"P{i+1}"))

    items = []
    projectiles = []
    frame_count = 0
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # --- Item Spawner ---
        if frame_count % 120 == 0 and len(items) < 5:
            angle = random.uniform(0, 2*math.pi)
            r = random.uniform(0, ARENA_RADIUS - 50)
            items.append(Item(ARENA_CENTER[0] + math.cos(angle)*r, ARENA_CENTER[1] + math.sin(angle)*r, 
                              random.choice(['weapon', 'health', 'shield'])))

        # --- Update ---
        effects.update()
        for it in items: it.update()
        
        for e in entities:
            e.move()
            
            # Auto Shooting
            if e.shoot_cooldown <= 0:
                # Find nearest enemy
                target = None
                min_d = 2000
                for other in entities:
                    if other != e:
                        d = distance((e.x, e.y), (other.x, other.y))
                        if d < min_d:
                            min_d = d
                            target = other
                
                if target:
                    e.shoot_cooldown = e.weapon.fire_rate
                    base_angle = math.atan2(target.y - e.y, target.x - e.x)
                    
                    for _ in range(e.weapon.projectile_count):
                        angle = base_angle + random.uniform(-e.weapon.spread, e.weapon.spread)
                        vx = math.cos(angle) * e.weapon.projectile_speed
                        vy = math.sin(angle) * e.weapon.projectile_speed
                        projectiles.append(Projectile(e.x, e.y, vx, vy, e.weapon, e))
                    
                    effects.add_muzzle_flash(e.x + math.cos(base_angle)*e.radius, e.y + math.sin(base_angle)*e.radius, e.weapon.color)

            # Item Pickup
            for it in items[:]:
                if distance((e.x, e.y), (it.x, it.y)) < e.radius + it.radius:
                    if it.type == 'weapon': e.weapon = WEAPONS[it.data]
                    elif it.type == 'health': e.hp = min(e.max_hp, e.hp + 50)
                    elif it.type == 'shield': e.shield = 300 # 5 seconds
                    items.remove(it)
                    effects.add_explosion(it.x, it.y, it.color, 10)

        # Projectiles update
        for p in projectiles[:]:
            p.update()
            if p.life <= 0 or distance((p.x, p.y), ARENA_CENTER) > ARENA_RADIUS:
                if p in projectiles: projectiles.remove(p)
                continue
            for e in entities:
                if e != p.owner and distance((p.x, p.y), (e.x, e.y)) < e.radius + p.radius:
                    damage = p.weapon.damage
                    if e.shield > 0: damage *= 0.2
                    e.hp -= damage
                    
                    # Screen shake and explosion
                    effects.shake(damage * 0.5)
                    effects.add_explosion(p.x, p.y, p.color, int(damage // 2))
                    if damage > 20:
                        effects.add_text(p.x, p.y - 20, "BOOM!", (255, 255, 0))
                    elif damage > 10:
                        effects.add_text(p.x, p.y - 20, "HIT!", (255, 255, 255))
                    
                    if p in projectiles: projectiles.remove(p)
                    break

        # Entity collisions
        for i in range(len(entities)):
            for j in range(i + 1, len(entities)):
                e1, e2 = entities[i], entities[j]
                if distance((e1.x, e1.y), (e2.x, e2.y)) < e1.radius + e2.radius:
                    # Bump damage
                    e1.hp -= 0.2
                    e2.hp -= 0.2
                    nx, ny = normalize((e1.x - e2.x, e1.y - e2.y))
                    e1.vx, e1.vy = nx * 4, ny * 4
                    e2.vx, e2.vy = -nx * 4, -ny * 4

        entities = [e for e in entities if e.hp > 0]
        if len(entities) <= 1:
            if frame_count > 600: running = False

        # --- Draw ---
        # Shake implementation
        ox = random.uniform(-effects.shake_amount, effects.shake_amount)
        oy = random.uniform(-effects.shake_amount, effects.shake_amount)
        
        screen.fill(COLORS['bg'])
        
        # Grid with offset
        for x in range(0, WIDTH + GRID_SIZE, GRID_SIZE):
            pygame.draw.line(screen, COLORS['grid'], (x + ox % GRID_SIZE, 0), (x + ox % GRID_SIZE, HEIGHT), 2)
        for y in range(0, HEIGHT + GRID_SIZE, GRID_SIZE):
            pygame.draw.line(screen, COLORS['grid'], (0, y + oy % GRID_SIZE), (WIDTH, y + oy % GRID_SIZE), 2)
            
        # Arena Border
        pygame.draw.circle(screen, COLORS['arena_border'], (int(ARENA_CENTER[0] + ox), int(ARENA_CENTER[1] + oy)), ARENA_RADIUS, 10)
        
        # Items
        for it in items: it.draw(screen)
        # Projectiles
        for p in projectiles: p.draw(screen)
        # Entities
        for e in entities: e.draw(screen)
        # Effects
        effects.draw(screen, font_small)
        
        # --- UI ---
        # Title
        title = font_large.render("BATTLE ROYALE", True, (255, 255, 255))
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 30))

        # Top Health Bars — one row per entity
        bar_margin_left = 60
        bar_w = 700
        bar_h = 28
        icon_r = 24
        row_gap = 80
        ui_top = 130
        for idx, e in enumerate(entities):
            row_y = ui_top + idx * row_gap

            # Icon (circle/square)
            pygame.draw.circle(screen, e.color, (bar_margin_left, row_y + bar_h // 2), icon_r)
            pygame.draw.circle(screen, (255, 255, 255), (bar_margin_left, row_y + bar_h // 2), icon_r, 3)

            # Background bar
            bx = bar_margin_left + icon_r + 16
            pygame.draw.rect(screen, (30, 30, 30), (bx, row_y, bar_w, bar_h), border_radius=6)
            # HP fill
            fill_w = max(0, int(bar_w * (e.hp / e.max_hp)))
            pygame.draw.rect(screen, e.color, (bx, row_y, fill_w, bar_h), border_radius=6)
            # Outline
            pygame.draw.rect(screen, (180, 180, 180), (bx, row_y, bar_w, bar_h), 2, border_radius=6)

            # Weapon label
            wlabel = font_small.render(e.weapon.name, True, (220, 220, 220))
            screen.blit(wlabel, (bx + bar_w + 12, row_y + (bar_h - wlabel.get_height()) // 2))

        watermark = font_small.render("@MrBouncerson", True, (100, 100, 100))
        screen.blit(watermark, (WIDTH//2 - watermark.get_width()//2, HEIGHT - 50))

        pygame.display.flip()
        frame_count += 1
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
