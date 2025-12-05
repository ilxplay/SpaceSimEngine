import sys
import pathlib

# When this file is executed directly, Python's import path is the script's
# directory (the `bodies/` folder). Add the project root to `sys.path` so
# sibling packages like `utils` can be imported.
project_root = pathlib.Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.vectors import Vector2
import math
import json

class CelestialBody:
    """Base class for all celestial bodies"""
    
    COLOR_MAP = {
        'star': (255, 255, 100),      # Yellow
        'planet': (100, 150, 255),     # Blue
        'gas_giant': (255, 150, 50),   # Orange
        'moon': (200, 200, 200),       # Gray
        'asteroid': (150, 100, 50),    # Brown
        'comet': (150, 200, 255),      # Light Blue
        'black_hole': (0, 0, 0),       # Black
    }
    
    def __init__(self, name="Unnamed Body", body_type="planet"):
        self.name = name
        self.body_type = body_type
        
        # physical properties
        self.mass = 1.0e24  # kg
        self.radius = 1.0e6  # meters
        self.density = 5514  # kg/m^3 (Earth's density)
        
        # dynamical properties
        self.position = Vector2(0, 0)
        self.velocity = Vector2(0, 0)
        self.acceleration = Vector2(0, 0)
        self.previous_position = Vector2(0, 0)
        
        # visual properties
        self.color = self.COLOR_MAP.get(body_type, (255, 255, 255))
        self.trail_color = (*self.color[:3], 100)  # Semi-transparent
        self.trail_length = 1000
        self.previous_positions = []
        
        # orbital properties
        self.parent = None
        self.semi_major_axis = 0
        self.eccentricity = 0
        self.orbital_period = 0
        self.inclination = 0
        
        # flags
        self.fixed_position = False  # for stars or stationary objects
        self.collidable = True
        self.visible = True
        
        # stats
        self.creation_time = 0
        self.total_energy = 0
        
    def update_radius_from_mass(self):
        """Update radius based on mass and density (assuming sphere)"""
        if self.density > 0:
            volume = self.mass / self.density
            self.radius = (3 * volume / (4 * math.pi)) ** (1/3)
    
    def update_mass_from_radius(self):
        """Update mass based on radius and density"""
        if self.density > 0:
            volume = (4/3) * math.pi * self.radius**3
            self.mass = self.density * volume
    
    def get_orbital_elements(self, central_body):
        """Calculate orbital elements relative to central body"""
        if not central_body:
            return None
            
        r = self.position - central_body.position
        v = self.velocity - central_body.velocity
        
        # Specific angular momentum
        h = Vector2(
            r.x * v.y - r.y * v.x,
            0
        )
        
        mu = 6.67430e-11 * (self.mass + central_body.mass)
        
        #(Eccentricity vector)
        e_vec = ((v.magnitude()**2 - mu/r.magnitude()) * r - 
                 (r.dot(v)) * v) / mu
        
        self.eccentricity = e_vec.magnitude()
        
        #for elliptical orbits
        if self.eccentricity != 1:
            energy = v.magnitude()**2/2 - mu/r.magnitude()
            self.semi_major_axis = -mu/(2*energy)
        
        return {
            'eccentricity': self.eccentricity,
            'semi_major_axis': self.semi_major_axis,
            'angular_momentum': h.magnitude(),
        }
    
    def to_dict(self):
        """Convert body to dictionary for saving"""
        return {
            'name': self.name,
            'body_type': self.body_type,
            'mass': self.mass,
            'radius': self.radius,
            'density': self.density,
            'position': [self.position.x, self.position.y],
            'velocity': [self.velocity.x, self.velocity.y],
            'color': self.color,
            'fixed_position': self.fixed_position,
            'parent': self.parent.name if self.parent else None,
        }
    
    @classmethod
    def from_dict(cls, data, bodies_dict=None):
        """Create body from dictionary"""
        body = cls(data['name'], data['body_type'])
        body.mass = data['mass']
        body.radius = data['radius']
        body.density = data.get('density', 5514)
        body.position = Vector2(*data['position'])
        body.velocity = Vector2(*data['velocity'])
        body.color = tuple(data['color'])
        body.fixed_position = data.get('fixed_position', False)
        
        if bodies_dict and data.get('parent'):
            body.parent = bodies_dict.get(data['parent'])
        
        return body
    
    def draw(self, surface, camera):
        """Draw the body and its trail"""
        if not self.visible:
            return
        # import pygame here to allow importing this module without pygame
        # being installed (useful for headless tests or CLI tools).
        import pygame
            
        # Convert pos to screen cords
        screen_pos = camera.world_to_screen(self.position)
        
        # draw trail
        if len(self.previous_positions) > 1:
            trail_points = []
            for pos in self.previous_positions[-100:]:  # limit trail length
                screen_pos_trail = camera.world_to_screen(pos)
                trail_points.append(screen_pos_trail.to_tuple())
            
            if len(trail_points) > 1:
                pygame.draw.lines(surface, self.trail_color, False, trail_points, 1)
        
        screen_radius = max(2, camera.scale * self.radius)
        
        pygame.draw.circle(surface, self.color, screen_pos.to_tuple(), screen_radius)
        
        # draw name if not too small
        if screen_radius > 5:
            font = pygame.font.Font(None, 20)
            text = font.render(self.name, True, (255, 255, 255))
            surface.blit(text, (screen_pos.x + screen_radius + 5, screen_pos.y - 10))