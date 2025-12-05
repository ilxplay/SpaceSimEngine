from .constants import G_NEWTONIAN
from utils.vectors import Vector2
import math
import numpy as np

class NewtonianPhysics:
    """Classical Newtonian gravitational physics"""
    
    def __init__(self, gravitational_constant=G_NEWTONIAN):
        self.G = gravitational_constant
        self.enable_collisions = False
        self.softening_length = 1e3  # prevent weird stuff
    
    def calculate_gravity(self, body1, body2):
        """Calculate gravitational force between two bodies"""
        r = body2.position - body1.position
        distance = r.magnitude()
        
        distance_sq = distance**2 + self.softening_length**2
  
        force_magnitude = self.G * body1.mass * body2.mass / distance_sq
        
        force = r.normalize() * force_magnitude
        
        return force, distance
    
    def calculate_orbital_velocity(self, central_mass, distance):
        """Calculate circular orbital velocity at given distance"""
        if distance > 0:
            return math.sqrt(self.G * central_mass / distance)
        return 0
    
    def calculate_all_forces(self, bodies):
        """Calculate net force on each body (N^2 complexity - optimize later)"""
        n = len(bodies)
        forces = [Vector2(0, 0) for _ in range(n)]
        
        for i in range(n):
            for j in range(i + 1, n):
                force, distance = self.calculate_gravity(bodies[i], bodies[j])
                forces[i] = forces[i] + force
                forces[j] = forces[j] - force  # equal and opposite
                
        return forces