import pygame
import sys
import json
import os
import math
from pygame.locals import *

# Import our modules
from physics.engine import PhysicsEngine
from bodies.celestial_body import SolarSystem
from bodies.celestial_body import Star, Planet
from ui.main_window import CelestialUI
from utils.camera import Camera
from utils.vectors import Vector2

class CelestialSimulation:
    """Main application class"""
    
    def __init__(self, width=1400, height=900):
        pygame.init()
        pygame.display.set_caption("2D Celestial Physics Engine")
        
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        self.width = width
        self.height = height
        self.clock = pygame.time.Clock()
        
        # create physics engine
        self.physics_engine = PhysicsEngine()
        
        self.camera = Camera(width, height)
        
        self.ui = CelestialUI(width, height, self.physics_engine)
        
        self.create_default_system()
        
        self.running = True
        self.show_grid = True
        self.show_coordinates = True
        self.selected_body = None
        self.fps_limit = 60
        
        # performance
        self.last_time = pygame.time.get_ticks()
        self.frame_times = []
    
    def create_default_system(self):
        """Create a default solar system for testing"""
        system = SolarSystem("Our Solar System")
        
        sun = Star("Sun", mass=1.989e30)
        sun.position = Vector2(0, 0)
        sun.fixed_position = True
        system.add_body(sun, set_as_central=True)
        
        earth = Planet("Earth", mass=5.972e24)
        earth.position = Vector2(1.496e11, 0)  # 1 AU
        earth.velocity = Vector2(0, 29780)  # orbital velocity
        earth.color = (100, 150, 255)
        system.add_body(earth)
        
        mars = Planet("Mars", mass=6.39e23)
        mars.position = Vector2(2.279e11, 0)  # 1.524 AU
        mars.velocity = Vector2(0, 24100)
        mars.color = (255, 100, 100)
        system.add_body(mars)
        
        jupiter = Planet("Jupiter", mass=1.898e27)
        jupiter.position = Vector2(7.785e11, 0)  # 5.204 AU
        jupiter.velocity = Vector2(0, 13070)
        jupiter.color = (255, 200, 100)
        system.add_body(jupiter)
        
        self.physics_engine.add_system(system, set_active=True)
        
        self.camera.fit_to_bodies(system.bodies)
    
    def create_solar_system_preset(self):
        """Create our solar system with all planets"""
        system = SolarSystem("Complete Solar System")
        
        sun = Star("Sun", mass=1.989e30)
        sun.position = Vector2(0, 0)
        sun.fixed_position = True
        system.add_body(sun, set_as_central=True)
        
        # approximate orbital parameters
        planets = [
            ("Mercury", 3.301e23, 5.791e10, 47360, (150, 150, 150)),
            ("Venus", 4.867e24, 1.082e11, 35020, (255, 200, 100)),
            ("Earth", 5.972e24, 1.496e11, 29780, (100, 150, 255)),
            ("Mars", 6.39e23, 2.279e11, 24100, (255, 100, 100)),
            ("Jupiter", 1.898e27, 7.785e11, 13070, (255, 200, 100)),
            ("Saturn", 5.683e26, 1.433e12, 9690, (255, 220, 150)),
            ("Uranus", 8.681e25, 2.877e12, 6810, (150, 220, 255)),
            ("Neptune", 1.024e26, 4.503e12, 5430, (100, 150, 255)),
        ]
        
        # add planets with some orbital inclination for realism
        import math
        for i, (name, mass, distance, velocity, color) in enumerate(planets):
            angle = (i / len(planets)) * 2 * math.pi
            
            planet = Planet(name, mass)
            planet.position = Vector2(
                distance * math.cos(angle),
                distance * math.sin(angle) * 0.9  # bit of inclination
            )
            planet.velocity = Vector2(
                -velocity * math.sin(angle) * 0.95,
                velocity * math.cos(angle)
            )
            planet.color = color
            
            # adjust radius based on mass
            planet.radius = 6.371e6 * (mass / 5.972e24) ** (1/3)
            
            system.add_body(planet)
        
        return system
    
    def handle_events(self):
        """Handle all pygame events"""
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            
            elif event.type == VIDEORESIZE:
                self.width, self.height = event.size
                self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                self.camera.screen_width = self.width
                self.camera.screen_height = self.height
                self.ui.screen_width = self.width
                self.ui.screen_height = self.height
            
            elif event.type == KEYDOWN:
                self.handle_keydown(event)
            
            self.ui.handle_events(event)
            self.camera.handle_event(event)
            
            if event.type == MOUSEBUTTONDOWN and event.button == 1:  # left click
                self.handle_body_selection(event.pos)
    
    def handle_keydown(self, event):
        """Handle keyboard input"""
        if event.key == K_SPACE:
            self.physics_engine.is_running = not self.physics_engine.is_running
        
        elif event.key == K_r:
            self.physics_engine.reset_simulation()
        
        elif event.key == K_g:
            self.show_grid = not self.show_grid
        
        elif event.key == K_c:
            self.show_coordinates = not self.show_coordinates
        
        elif event.key == K_f:
            if self.physics_engine.active_system:
                self.camera.fit_to_bodies(self.physics_engine.active_system.bodies)
        
        elif event.key == K_PLUS or event.key == K_EQUALS:
            self.camera.zoom(0.9)
        
        elif event.key == K_MINUS:
            self.camera.zoom(1.1)
        
        elif event.key == K_ESCAPE:
            self.running = False
        
        elif event.key == K_s:
            self.save_system()
        
        elif event.key == K_l:
            self.load_system()
    
    def handle_body_selection(self, mouse_pos):
        """Select a body by clicking on it"""
        if not self.physics_engine.active_system:
            return
        
        world_pos = self.camera.screen_to_world(Vector2(*mouse_pos))
        
        # check each body for click
        for body in self.physics_engine.active_system.bodies:
          
            distance = world_pos.distance(body.position)
            
            
            selection_radius = max(body.radius, 1e9)
            
            if distance < selection_radius:
                self.selected_body = body
                print(f"Selected: {body.name}")
                
                
                self.update_body_editor_with_selection(body)
                break
        else:
            # deselect
            self.selected_body = None
    
    def update_body_editor_with_selection(self, body):
        """Update UI with selected body's properties"""
        if hasattr(self.ui, 'body_name_input'):
            self.ui.body_name_input.set_text(body.name)
        
        if hasattr(self.ui, 'pos_x_input'):
            self.ui.pos_x_input.set_text(f"{body.position.x:.2e}")
        
        if hasattr(self.ui, 'pos_y_input'):
            self.ui.pos_y_input.set_text(f"{body.position.y:.2e}")
        
        if hasattr(self.ui, 'vel_x_input'):
            self.ui.vel_x_input.set_text(f"{body.velocity.x:.2e}")
        
        if hasattr(self.ui, 'vel_y_input'):
            self.ui.vel_y_input.set_text(f"{body.velocity.y:.2e}")
    
    def draw_grid(self, surface):
        """Draw a coordinate grid"""
        if not self.show_grid:
            return
        
        visible = self.camera.get_visible_grid_range()
        
        scale = self.camera.scale
        
        log_scale = max(0, min(20, int(math.log10(scale))))
        spacing = 10 ** (log_scale + 6)
        
        start_x = math.ceil(visible['min_x'] / spacing) * spacing
        start_y = math.ceil(visible['min_y'] / spacing) * spacing
        
        color = (50, 50, 80, 150)
        font = pygame.font.Font(None, 20)
        
        x = start_x
        while x <= visible['max_x']:
            screen_pos = self.camera.world_to_screen(Vector2(x, 0))
            
            top = self.camera.world_to_screen(Vector2(x, visible['max_y']))
            bottom = self.camera.world_to_screen(Vector2(x, visible['min_y']))
            pygame.draw.line(surface, color, top.to_tuple(), bottom.to_tuple(), 1)
            
            if abs(x) > spacing * 0.1:
                text = font.render(f"{x/1e9:.0f}Gm", True, (100, 100, 150))
                surface.blit(text, (screen_pos.x + 5, self.height - 20))
            
            x += spacing
        
        # horizontal lines
        y = start_y
        while y <= visible['max_y']:
            screen_pos = self.camera.world_to_screen(Vector2(0, y))
            
            # draw line
            left = self.camera.world_to_screen(Vector2(visible['min_x'], y))
            right = self.camera.world_to_screen(Vector2(visible['max_x'], y))
            pygame.draw.line(surface, color, left.to_tuple(), right.to_tuple(), 1)
            
            # draw coordinate label
            if abs(y) > spacing * 0.1:
                text = font.render(f"{y/1e9:.0f}Gm", True, (100, 100, 150))
                surface.blit(text, (10, screen_pos.y - 15))
            
            y += spacing
        
        # draw origin axes
        origin = self.camera.world_to_screen(Vector2(0, 0))
        pygame.draw.line(surface, (100, 150, 255), 
                        (origin.x, 0), (origin.x, self.height), 2)
        pygame.draw.line(surface, (100, 150, 255), 
                        (0, origin.y), (self.width, origin.y), 2)
        
        # draw origin marker
        pygame.draw.circle(surface, (255, 255, 255), origin.to_tuple(), 3)
        text = font.render("(0,0)", True, (200, 200, 255))
        surface.blit(text, (origin.x + 5, origin.y + 5))
    
    def draw_coordinate_info(self, surface):
        """Draw coordinate information at mouse position"""
        if not self.show_coordinates:
            return
        
        mouse_pos = Vector2(*pygame.mouse.get_pos())
        world_pos = self.camera.screen_to_world(mouse_pos)
        
        font = pygame.font.Font(None, 24)
        
        # create text
        au_x = world_pos.x / 1.496e11
        au_y = world_pos.y / 1.496e11
        
        lines = [
            f"World: ({world_pos.x:.2e}, {world_pos.y:.2e}) m",
            f"AU: ({au_x:.2f}, {au_y:.2f}) AU",
            f"Scale: 1 px = {self.camera.scale:.2e} m",
        ]
        
        if self.selected_body:
            lines.append(f"Selected: {self.selected_body.name}")
            lines.append(f"Mass: {self.selected_body.mass:.2e} kg")
            lines.append(f"Speed: {self.selected_body.velocity.magnitude():.0f} m/s")
        
        # draw background
        padding = 10
        text_height = len(lines) * 25
        bg_rect = pygame.Rect(10, self.height - text_height - padding - 10, 
                             300, text_height + padding * 2)
        pygame.draw.rect(surface, (0, 0, 0, 180), bg_rect)
        pygame.draw.rect(surface, (50, 50, 100), bg_rect, 2)
        
        # draw text
        for i, line in enumerate(lines):
            text = font.render(line, True, (220, 220, 255))
            surface.blit(text, (20, self.height - text_height - padding + i * 25))
    
    def draw_selection_highlight(self, surface):
      
        if not self.selected_body:
            return
        
        screen_pos = self.camera.world_to_screen(self.selected_body.position)
        radius = max(5, self.camera.scale * self.selected_body.radius)
        
        # draw pulsating circle
        pulse = (pygame.time.get_ticks() % 1000) / 1000
        alpha = int(150 + 100 * math.sin(pulse * 2 * math.pi))
        
        # create a surface for alpha blending
        highlight = pygame.Surface((int(radius*2.5), int(radius*2.5)), pygame.SRCALPHA)
        pygame.draw.circle(highlight, (255, 255, 100, alpha), 
                          (int(radius*1.25), int(radius*1.25)), 
                          int(radius*1.2), 3)
        
        surface.blit(highlight, (screen_pos.x - radius*1.25, screen_pos.y - radius*1.25))
        
        # draw velocity vector
        if self.selected_body.velocity.magnitude() > 0:
            vel = self.selected_body.velocity.normalize() * radius * 2
            end_pos = screen_pos + vel
            pygame.draw.line(surface, (100, 255, 100), 
                            screen_pos.to_tuple(), end_pos.to_tuple(), 2)
            
            # draw arrowhead
            angle = math.atan2(vel.y, vel.x)
            arrow_size = 10
            left_angle = angle + math.pi * 0.8
            right_angle = angle - math.pi * 0.8
            
            left_point = Vector2(
                end_pos.x + arrow_size * math.cos(left_angle),
                end_pos.y + arrow_size * math.sin(left_angle)
            )
            right_point = Vector2(
                end_pos.x + arrow_size * math.cos(right_angle),
                end_pos.y + arrow_size * math.sin(right_angle)
            )
            
            pygame.draw.polygon(surface, (100, 255, 100), 
                              [end_pos.to_tuple(), left_point.to_tuple(), right_point.to_tuple()])
    
    def draw(self):
        # clear screen with space background
        self.screen.fill((5, 5, 15))
        
        # draw stars in background
        self.draw_stars()
        
        # draw grid
        self.draw_grid(self.screen)
        
        # draw all celestial bodies
        if self.physics_engine.active_system:
            for body in self.physics_engine.active_system.bodies:
                body.draw(self.screen, self.camera)
        
        # draw selection highlight
        self.draw_selection_highlight(self.screen)
        
        # draw coordinate info
        self.draw_coordinate_info(self.screen)
        
        # draw UI
        self.ui.draw(self.screen)
        
        # update display
        pygame.display.flip()
    
    def draw_stars(self):
        """Draw starfield in background"""
        # simple starfield - could be optimized
        import random
        
        # get visible area
        visible = self.camera.get_visible_grid_range()
        
        # draw some random stars
        for _ in range(100):
            # use cached positions for performance
            x = random.uniform(visible['min_x'], visible['max_x'])
            y = random.uniform(visible['min_y'], visible['max_y'])
            
            screen_pos = self.camera.world_to_screen(Vector2(x, y))
            
            # only draw if on screen
            if (0 <= screen_pos.x < self.width and 
                0 <= screen_pos.y < self.height):
                
                brightness = random.randint(100, 255)
                radius = random.uniform(0.5, 1.5)
                color = (brightness, brightness, brightness)
                
                pygame.draw.circle(self.screen, color, 
                                 (int(screen_pos.x), int(screen_pos.y)), 
                                 int(radius))
    
    def save_system(self, filename=None):
        """Save current solar system to file"""
        if not self.physics_engine.active_system:
            return
        
        if filename is None:
            import time
            filename = f"saves/{self.physics_engine.active_system.name}_{int(time.time())}.json"
        
        # ensure saves directory exists
        os.makedirs("saves", exist_ok=True)
        
        # convert system to dictionary
        system_dict = self.physics_engine.active_system.to_dict()
        
        # save to file
        with open(filename, 'w') as f:
            json.dump(system_dict, f, indent=2)
        
        print(f"System saved to {filename}")
    
    def load_system(self, filename=None):
        """Load solar system from file"""
        if filename is None:
            filename = "presets/solar_system.json"
        
        try:
            with open(filename, 'r') as f:
                system_dict = json.load(f)
            
            system = SolarSystem.from_dict(system_dict)
            self.physics_engine.add_system(system, set_active=True)
            
            self.camera.fit_to_bodies(system.bodies)
            
            print(f"System loaded from {filename}")
            
        except FileNotFoundError:
            print(f"File not found: {filename}")
        except json.JSONDecodeError:
            print(f"Invalid JSON file: {filename}")
    
    def update(self, dt):
        """Update simulation"""
        self.physics_engine.update(dt)
        
        self.camera.update(dt)
        
        self.ui.update(dt)
        
        stats = self.physics_engine.get_statistics()
        self.ui.update_info_panel(stats)
        
        current_time = pygame.time.get_ticks()
        frame_time = current_time - self.last_time
        self.frame_times.append(frame_time)
        if len(self.frame_times) > 60:
            self.frame_times.pop(0)
        
        self.last_time = current_time
    
    def run(self):
        """Main game loop"""
        print("Celestial Physics Engine Started!")
        print("Controls:")
        print("  SPACE - Pause/Play simulation")
        print("  R - Reset simulation")
        print("  G - Toggle grid")
        print("  C - Toggle coordinates")
        print("  F - Fit view to bodies")
        print("  +/- - Zoom in/out")
        print("  S - Save system")
        print("  L - Load system")
        print("  ESC - Quit")
        
        while self.running:
            dt = self.clock.tick(self.fps_limit) / 1000.0  # convert to seconds
            
            self.handle_events()
            
            self.update(dt)
            
            self.draw()
            
            # show fps in window title
            if pygame.time.get_ticks() % 1000 < dt * 1000:
                avg_fps = 1000 / (sum(self.frame_times) / len(self.frame_times)) if self.frame_times else 0
                pygame.display.set_caption(
                    f"2D Celestial Physics Engine | FPS: {avg_fps:.1f} | "
                    f"Bodies: {len(self.physics_engine.active_system.bodies) if self.physics_engine.active_system else 0}"
                )
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    # create and run the simulation
    simulation = CelestialSimulation()
    simulation.run()