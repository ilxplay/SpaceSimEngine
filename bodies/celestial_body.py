import sys
import pathlib
import pygame

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
            
class Star(CelestialBody):
    def __init__(self, name="Star", mass=1.989e30):
        super().__init__(name, "star")
        self.mass = mass
        self.radius = 6.957e8  # solar radius
        self.luminosity = 3.828e26  # watts
        self.temperature = 5778  # kelvin
        self.fixed_position = True
        self.color = (255, 255, 100)  # yellow
        
    def update_properties(self):
        """Update stellar properties based on mass (empirical relations)"""
        self.luminosity = 3.828e26 * (self.mass / 1.989e30) ** 3.5
        
        if self.mass < 1.989e30:
            self.radius = 6.957e8 * (self.mass / 1.989e30) ** 0.8
        else:
            self.radius = 6.957e8 * (self.mass / 1.989e30) ** 0.57

class Planet(CelestialBody):
    def __init__(self, name="Planet", mass=5.972e24):
        super().__init__(name, "planet")
        self.mass = mass
        self.radius = 6.371e6  # earth radius
        self.has_atmosphere = True
        self.atmosphere_thickness = 100000  # meters
        self.surface_gravity = 9.81  # m/s^2
        
    def calculate_surface_gravity(self):
        """Calculate surface gravity"""
        G = 6.67430e-11
        self.surface_gravity = G * self.mass / self.radius**2

class BlackHole(CelestialBody):
    def __init__(self, name="Black Hole", mass=1.989e30):
        super().__init__(name, "black_hole")
        self.mass = mass
        self.schwarzschild_radius = 2 * 6.67430e-11 * mass / (299792458**2)
        self.radius = self.schwarzschild_radius * 3  # visual radius
        self.accretion_disk = True
        self.color = (0, 0, 0)  # black
        self.event_horizon_color = (100, 0, 100)  # purple for accretion disk
        
    def draw(self, surface, camera):
        """Special drawing for black hole with accretion disk"""
        super().draw(surface, camera)
        
        # draw accretion disk
        screen_pos = camera.world_to_screen(self.position)
        disk_radius = camera.scale * self.schwarzschild_radius * 5
        
        # create accretion disk effect
        for i in range(3):
            radius = disk_radius * (i + 1) / 3
            alpha = 100 - i * 30
            color = (*self.event_horizon_color[:3], alpha)
            
            disk_surface = pygame.Surface((int(radius*2), int(radius*2)), pygame.SRCALPHA)
            pygame.draw.circle(disk_surface, color, (int(radius), int(radius)), int(radius), 2)
            surface.blit(disk_surface, (screen_pos.x - radius, screen_pos.y - radius))
            
            
class SolarSystem:
    """Container for multiple celestial bodies"""
    
    def __init__(self, name="Solar System"):
        self.name = name
        self.bodies = []
        self.central_star = None
        self.time = 0.0  # simulation time in seconds
        self.timestep = 3600  # default 1h
        
    def add_body(self, body, set_as_central=False):
        """Add a body to the system"""
        self.bodies.append(body)
        
        if set_as_central or (body.body_type == "star" and not self.central_star):
            self.central_star = body
            body.fixed_position = True
    
    def remove_body(self, body_name):
        """Remove a body by name"""
        for i, body in enumerate(self.bodies):
            if body.name == body_name:
                if body == self.central_star:
                    self.central_star = None
                del self.bodies[i]
                return True
        return False
    
    def get_body(self, name):
        """Get body by name"""
        for body in self.bodies:
            if body.name == name:
                return body
        return None
    
    def calculate_total_energy(self):
        """Calculate total kinetic + potential energy of the system"""
        total_energy = 0
        G = 6.67430e-11
        
        for i, body1 in enumerate(self.bodies):
            # kinetic energy
            v2 = body1.velocity.magnitude() ** 2
            kinetic = 0.5 * body1.mass * v2
            total_energy += kinetic
            
            # potential energy (pairwise)
            for j, body2 in enumerate(self.bodies[i+1:], i+1):
                distance = body1.position.distance(body2.position)
                if distance > 0:
                    potential = -G * body1.mass * body2.mass / distance
                    total_energy += potential
        
        return total_energy
    
    def calculate_center_of_mass(self):
        """Calculate the center of mass of the system"""
        total_mass = 0
        com = Vector2(0, 0)
        
        for body in self.bodies:
            total_mass += body.mass
            com = com + body.position * body.mass
        
        if total_mass > 0:
            com = com / total_mass
        
        return com, total_mass
    
    def to_dict(self):
        """Convert system to dictionary for saving"""
        return {
            'name': self.name,
            'time': self.time,
            'timestep': self.timestep,
            'bodies': [body.to_dict() for body in self.bodies],
            'central_star': self.central_star.name if self.central_star else None,
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create system from dictionary"""
        system = cls(data['name'])
        system.time = data.get('time', 0)
        system.timestep = data.get('timestep', 3600)
        
        bodies_dict = {}
        for body_data in data['bodies']:
            body = CelestialBody.from_dict(body_data)
            system.add_body(body)
            bodies_dict[body.name] = body
        
        # establish parent links
        for body_data in data['bodies']:
            if body_data.get('parent'):
                body = bodies_dict[body_data['name']]
                body.parent = bodies_dict.get(body_data['parent'])
        
        # set central star
        if data.get('central_star'):
            system.central_star = bodies_dict.get(data['central_star'])
        
        return system