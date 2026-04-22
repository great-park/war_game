import pygame
import cv2
import numpy as np
import random
import math
import os

# --- Configurations ---
WIDTH, HEIGHT = 1080, 1920
FPS = 60
ARENA_CENTER = (WIDTH // 2, HEIGHT // 2)
ARENA_RADIUS = 500

COLORS = {
    'bg': (30, 30, 30),
    'arena': (200, 200, 200),
    'health_bg': (100, 100, 100),
    'health_fg': (50, 200, 50),
    'sword': (200, 50, 50),
    'gun': (50, 50, 200),
    'bomb': (50, 50, 50),
    'bullet': (255, 255, 0)
}

ITEM_TYPES = ['sword', 'gun', 'bomb']

# --- Math Helpers ---
def distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def normalize(v):
    mag = math.hypot(v[0], v[1])
    if mag == 0: return (0, 0)
    return (v[0]/mag, v[1]/mag)

# --- Classes ---
class Ball:
    def __init__(self, x, y, radius, color):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        
        # Random initial velocity
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(5, 10)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        
        self.max_hp = 100
        self.hp = 100
        self.item = None
        self.shoot_cooldown = 0
        
    def move(self):
        self.x += self.vx
        self.y += self.vy
        
        # Arena collision
        dist_to_center = distance((self.x, self.y), ARENA_CENTER)
        if dist_to_center + self.radius > ARENA_RADIUS:
            # Normal vector from center to ball
            nx, ny = normalize((self.x - ARENA_CENTER[0], self.y - ARENA_CENTER[1]))
            # Move ball back inside
            overlap = dist_to_center + self.radius - ARENA_RADIUS
            self.x -= nx * overlap
            self.y -= ny * overlap
            # Reflect velocity: v = v - 2(v.n)n
            dot = self.vx * nx + self.vy * ny
            self.vx -= 2 * dot * nx
            self.vy -= 2 * dot * ny

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def draw(self, surface):
        # Draw ball
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        # Draw item indicator if any
        if self.item == 'sword':
            pygame.draw.circle(surface, COLORS['sword'], (int(self.x), int(self.y)), self.radius + 5, 3)
        elif self.item == 'gun':
            pygame.draw.circle(surface, COLORS['gun'], (int(self.x), int(self.y)), self.radius + 5, 3)
        elif self.item == 'bomb':
            pygame.draw.circle(surface, COLORS['bomb'], (int(self.x), int(self.y)), self.radius + 5, 3)
            
        # Draw health bar
        bar_width = self.radius * 2
        bar_height = 8
        bar_x = self.x - bar_width / 2
        bar_y = self.y - self.radius - 15
        
        pygame.draw.rect(surface, COLORS['health_bg'], (bar_x, bar_y, bar_width, bar_height))
        hp_ratio = max(0, self.hp / self.max_hp)
        pygame.draw.rect(surface, COLORS['health_fg'], (bar_x, bar_y, bar_width * hp_ratio, bar_height))

class ItemDrop:
    def __init__(self, x, y, item_type):
        self.x = x
        self.y = y
        self.type = item_type
        self.radius = 15

    def draw(self, surface):
        pygame.draw.circle(surface, COLORS[self.type], (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, (255, 255, 255), (int(self.x), int(self.y)), self.radius, 2)

class Projectile:
    def __init__(self, x, y, vx, vy, owner):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.owner = owner
        self.radius = 5
        self.life = 120

    def move(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1

    def draw(self, surface):
        pygame.draw.circle(surface, COLORS['bullet'], (int(self.x), int(self.y)), self.radius)

class Effect:
    def __init__(self, x, y, radius_max, color):
        self.x = x
        self.y = y
        self.radius = 0
        self.radius_max = radius_max
        self.color = color
        self.life = 30

    def move(self):
        self.radius += (self.radius_max - self.radius) * 0.2
        self.life -= 1

    def draw(self, surface):
        alpha = max(0, int((self.life / 30) * 255))
        s = pygame.Surface((self.radius_max*2, self.radius_max*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (self.radius_max, self.radius_max), int(self.radius))
        surface.blit(s, (self.x - self.radius_max, self.y - self.radius_max))

# --- Main Logic ---
def main():
    pygame.init()
    pygame.font.init()
    font = pygame.font.SysFont('Arial', 48, bold=True)
    
    # We can use a hidden display for rendering without popping up a window, 
    # but some systems prefer a real display. We'll make it visible but we capture it.
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Shorts Battle")
    
    # Setup OpenCV Video Writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('output.mp4', fourcc, FPS, (WIDTH, HEIGHT))
    
    balls = []
    colors_list = [(255,100,100), (100,255,100), (100,100,255), (255,255,100), (255,100,255)]
    
    # Spawn balls
    for i in range(5):
        angle = random.uniform(0, 2 * math.pi)
        r = random.uniform(0, ARENA_RADIUS - 50)
        x = ARENA_CENTER[0] + math.cos(angle) * r
        y = ARENA_CENTER[1] + math.sin(angle) * r
        balls.append(Ball(x, y, 40, colors_list[i % len(colors_list)]))
        
    items = []
    projectiles = []
    effects = []
    
    clock = pygame.time.Clock()
    running = True
    frame_count = 0
    winner_text = ""
    winner_timer = 0
    
    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
        # Game Logic
        if winner_text == "":
            # Item Spawner
            if frame_count % 180 == 0 and len(items) < 3:
                angle = random.uniform(0, 2 * math.pi)
                r = random.uniform(0, ARENA_RADIUS - 50)
                x = ARENA_CENTER[0] + math.cos(angle) * r
                y = ARENA_CENTER[1] + math.sin(angle) * r
                items.append(ItemDrop(x, y, random.choice(ITEM_TYPES)))
                
            # Update Effects
            for e in effects[:]:
                e.move()
                if e.life <= 0:
                    effects.remove(e)

            # Update projectiles
            for p in projectiles[:]:
                p.move()
                if p.life <= 0 or distance((p.x, p.y), ARENA_CENTER) > ARENA_RADIUS:
                    if p in projectiles: projectiles.remove(p)
                    continue
                # Check hit
                for b in balls:
                    if b != p.owner and distance((p.x, p.y), (b.x, b.y)) < b.radius + p.radius:
                        b.hp -= 15
                        effects.append(Effect(p.x, p.y, 20, (255, 255, 200)))
                        if p in projectiles: projectiles.remove(p)
                        break
                        
            # Move balls and check collisions
            for i in range(len(balls)):
                balls[i].move()
                
                # Shoot gun
                if balls[i].item == 'gun' and balls[i].shoot_cooldown <= 0:
                    balls[i].shoot_cooldown = 30
                    # Shoot at nearest
                    target = None
                    min_dist = float('inf')
                    for j in range(len(balls)):
                        if i != j:
                            d = distance((balls[i].x, balls[i].y), (balls[j].x, balls[j].y))
                            if d < min_dist:
                                min_dist = d
                                target = balls[j]
                    if target:
                        dx, dy = normalize((target.x - balls[i].x, target.y - balls[i].y))
                        projectiles.append(Projectile(balls[i].x, balls[i].y, dx*15, dy*15, balls[i]))
                
                # Check ball-ball collisions
                for j in range(i + 1, len(balls)):
                    b1 = balls[i]
                    b2 = balls[j]
                    dist = distance((b1.x, b1.y), (b2.x, b2.y))
                    min_dist = b1.radius + b2.radius
                    if dist < min_dist:
                        # Resolve overlap
                        overlap = min_dist - dist
                        nx, ny = normalize((b1.x - b2.x, b1.y - b2.y))
                        b1.x += nx * overlap / 2
                        b1.y += ny * overlap / 2
                        b2.x -= nx * overlap / 2
                        b2.y -= ny * overlap / 2
                        
                        # Elastic collision (velocity swap along normal)
                        p = 2 * (b1.vx * nx + b1.vy * ny - b2.vx * nx - b2.vy * ny) / 2
                        b1.vx -= p * nx
                        b1.vy -= p * ny
                        b2.vx += p * nx
                        b2.vy += p * ny
                        
                        # Apply damage based on items
                        dmg1, dmg2 = 5, 5
                        if b1.item == 'sword': dmg2 += 15
                        if b2.item == 'sword': dmg1 += 15
                        
                        if b1.item == 'bomb':
                            effects.append(Effect(b1.x, b1.y, 100, (255, 100, 0)))
                            dmg2 += 30
                            b1.item = None # use bomb
                        if b2.item == 'bomb':
                            effects.append(Effect(b2.x, b2.y, 100, (255, 100, 0)))
                            dmg1 += 30
                            b2.item = None
                            
                        b1.hp -= dmg1
                        b2.hp -= dmg2

                # Check ball-item collision
                for it in items[:]:
                    if distance((balls[i].x, balls[i].y), (it.x, it.y)) < balls[i].radius + it.radius:
                        balls[i].item = it.type
                        items.remove(it)

            # Remove dead balls
            balls = [b for b in balls if b.hp > 0]
            
            # Winner check
            if len(balls) <= 1:
                if len(balls) == 1:
                    winner_text = "WINNER!"
                else:
                    winner_text = "DRAW!"
                winner_timer = 180 # 3 seconds

        else:
            # End sequence
            winner_timer -= 1
            if winner_timer <= 0:
                running = False
                
        # Draw
        screen.fill(COLORS['bg'])
        pygame.draw.circle(screen, COLORS['arena'], ARENA_CENTER, ARENA_RADIUS, 5)
        
        for e in effects: e.draw(screen)
        for it in items: it.draw(screen)
        for p in projectiles: p.draw(screen)
        for b in balls: b.draw(screen)
        
        if winner_text != "":
            ts = font.render(winner_text, True, (255, 255, 255))
            tr = ts.get_rect(center=(WIDTH//2, HEIGHT//2))
            screen.blit(ts, tr)
            
        pygame.display.flip()
        
        # Write to video
        frame = pygame.surfarray.array3d(screen)
        frame = np.transpose(frame, (1, 0, 2)) # (w, h, 3) to (h, w, 3)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        out.write(frame)
        
        frame_count += 1
        clock.tick(FPS)
        
    out.release()
    pygame.quit()

if __name__ == "__main__":
    main()
