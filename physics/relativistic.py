from .constants import G_RELATIVITY, SPEED_OF_LIGHT
from utils.vectors import Vector2
from physics.newtonian import NewtonianPhysics
import math

class RelativisticPhysics(NewtonianPhysics):
    
    def __init__(self, gravitational_constant=G_RELATIVITY):
        super().__init__(gravitational_constant)
        self.c = SPEED_OF_LIGHT
        self.c_squared = self.c ** 2
        self.enable_time_dilation = True
        self.enable_frame_dragging = False
    
    def calculate_gravity(self, body1, body2):
        """Calculate gravitational force with relativistic corrections"""
        newtonian_force, distance = super().calculate_gravity(body1, body2)
        
        if distance == 0:
            return Vector2(0, 0), 0
        
        v_rel = body2.velocity - body1.velocity
        v_mag = v_rel.magnitude()
        
        schwarzschild_radius = 2 * self.G * body1.mass / self.c_squared
        
        beta = v_mag / self.c
        gamma = 1 / math.sqrt(1 - beta**2) if beta < 1 else 1e10
        
        if self.enable_time_dilation and distance > schwarzschild_radius:
            time_dilation = 1 / math.sqrt(1 - schwarzschild_radius / distance)
            correction = 1 + (gamma - 1) * 0.5 + (time_dilation - 1) * 0.1
            corrected_force = newtonian_force * correction
        else:
            corrected_force = newtonian_force
        
        return corrected_force, distance
    
    def calculate_orbital_precession(self, body, central_mass, semi_major_axis, eccentricity):
        """Calculate relativistic precession per orbit""" #for example mercury
        if eccentricity >= 1:
            return 0
        
        numerator = 24 * math.pi**3 * semi_major_axis**2
        denominator = self.c_squared * (1 - eccentricity**2)
        precession = numerator / denominator
        
        return precession  # radians per orbit