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
    'Pistol': Weapon('Pistol', 40, 15, 12, (200, 200, 200)),
    'Sniper': Weapon('Sniper', 100, 60, 28, (255, 100, 0)),
    'MachineGun': Weapon('MachineGun', 8, 8, 18, (100, 255, 100)),
    'Shotgun': Weapon('Shotgun', 60, 10, 15, (255, 255, 255), 5, 0.4),
    'Flamethrower': Weapon('Flamethrower', 3, 3, 10, (255, 150, 0)),
    'Minigun': Weapon('Minigun', 5, 6, 22, (255, 255, 50))
}

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
            self.data = random.choice(list(WEAPONS.keys()))
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
        speed = random.uniform(4, 8)
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
            self.vx *= 1.02
            self.vy *= 1.02
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
        
        # Weapon
        if self.weapon:
            angle = math.atan2(self.vy, self.vx)
            gun_len = self.radius + 15
            gx = self.x + math.cos(angle) * gun_len
            gy = self.y + math.sin(angle) * gun_len
            pygame.draw.line(surface, (50, 50, 50), (self.x, self.y), (gx, gy), 12)
            pygame.draw.circle(surface, (100, 100, 100), (int(gx), int(gy)), 8)
            
        # Floating Health Bar
        bar_w = self.radius * 2
        bar_h = 8
        bx = self.x - bar_w // 2
        by = self.y - self.radius - 20
        pygame.draw.rect(surface, (40, 40, 40), (bx, by, bar_w, bar_h))
        pygame.draw.rect(surface, self.color, (bx, by, bar_w * (self.hp / self.max_hp), bar_h))

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

# --- Projectile ---
class Projectile:
    def __init__(self, x, y, vx, vy, weapon, owner):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.weapon = weapon
        self.owner = owner
        self.radius = 8 if weapon.name != 'Flamethrower' else 15
        self.life = 120 if weapon.name != 'Flamethrower' else 25
        self.color = weapon.color

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        if self.weapon.name == 'Flamethrower':
            self.radius += 1.5

    def draw(self, surface):
        alpha = min(255, self.life * 15)
        s = pygame.Surface((self.radius*4, self.radius*4), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (int(self.radius*2), int(self.radius*2)), int(self.radius))
        surface.blit(s, (int(self.x - self.radius*2), int(self.y - self.radius*2)))

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
        entities.append(Entity(x, y, 40, colors[i], shape, 150, f"P{i+1}"))

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
                    e1.vx, e1.vy = nx * 6, ny * 6
                    e2.vx, e2.vy = -nx * 6, -ny * 6

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
        title = font_large.render("BATTLE ROYALE", True, (255, 255, 255))
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 200))
        
        # Bottom Player Stats
        ui_x = 80
        for e in entities:
            # Heart-based HP
            pygame.draw.circle(screen, e.color, (ui_x, HEIGHT - 180), 20)
            
            # Hearts
            heart_count = 5
            hp_per_heart = e.max_hp / heart_count
            for i in range(heart_count):
                hx = ui_x - 30 + (i % 3) * 35
                hy = HEIGHT - 140 + (i // 3) * 35
                color = e.color if e.hp > i * hp_per_heart else (40, 40, 40)
                # Simple heart drawing
                pygame.draw.circle(screen, color, (hx - 8, hy), 8)
                pygame.draw.circle(screen, color, (hx + 8, hy), 8)
                pygame.draw.polygon(screen, color, [(hx - 16, hy + 2), (hx + 16, hy + 2), (hx, hy + 20)])
            
            # Weapon name
            txt = font_small.render(e.weapon.name[:3].upper(), True, (200, 200, 200))
            screen.blit(txt, (ui_x - 15, HEIGHT - 70))
            
            ui_x += 180

        watermark = font_small.render("@MrBouncerson", True, (100, 100, 100))
        screen.blit(watermark, (WIDTH//2 - watermark.get_width()//2, HEIGHT - 50))

        pygame.display.flip()
        frame_count += 1
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
