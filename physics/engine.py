import pygame
import numpy as np
from .newtonian import NewtonianPhysics
from .relativistic import RelativisticPhysics
from .integrators import EulerIntegrator, VerletIntegrator, RK4Integrator
from utils.vectors import Vector2
import time

class PhysicsEngine:
    """Main physics engine coordinating all components"""
    
    def __init__(self):
        self.physics_models = {
            'newtonian': NewtonianPhysics(),
            'relativistic': RelativisticPhysics()
        }
        self.current_physics = 'newtonian'
        
        # integration methods
        self.integrators = {
            'euler': EulerIntegrator(),
            'verlet': VerletIntegrator(),
            'rk4': RK4Integrator()
        }
        self.current_integrator = 'verlet'
        
        # simulation state
        self.systems = []
        self.active_system = None
        self.is_running = False
        self.is_paused = False
        
        # performance tracking
        self.frame_count = 0
        self.start_time = time.time()
        self.avg_fps = 0
        
        # simulation parameters
        self.time_scale = 1.0  # real-time factor
        self.gravitational_constant = 6.67430e-11
        self.enable_collisions = False
        self.enable_trails = True
        self.max_bodies = 1000
        
        # statistics
        self.total_energy = 0
        self.angular_momentum = Vector2(0, 0)
        self.computation_time = 0
        
    def set_physics_model(self, model_name):
        """Switch between physics models"""
        if model_name in self.physics_models:
            self.current_physics = model_name
            print(f"Switched to {model_name} physics")
            
            # update gravitational constant
            self.physics_models[model_name].G = self.gravitational_constant
    
    def set_integrator(self, integrator_name):
        """Switch integration method"""
        if integrator_name in self.integrators:
            self.current_integrator = integrator_name
            print(f"Switched to {integrator_name} integration")
    
    def set_gravitational_constant(self, G):
        """Modify gravitational constant"""
        self.gravitational_constant = G
        for model in self.physics_models.values():
            model.G = G
    
    def add_system(self, system, set_active=True):
        """Add a solar system to the engine"""
        self.systems.append(system)
        if set_active or not self.active_system:
            self.active_system = system
    
    def update(self, dt):
        """Update simulation by one timestep"""
        if not self.active_system or not self.is_running or self.is_paused:
            return
        
        start_time = time.perf_counter()
        
        # apply time scaling
        scaled_dt = dt * self.time_scale * self.active_system.timestep
        
        # get current physics model and integrator
        physics_model = self.physics_models[self.current_physics]
        integrator = self.integrators[self.current_integrator]
        
        # calculate forces for all bodies
        bodies = self.active_system.bodies
        forces = physics_model.calculate_all_forces(bodies)
        
        # update each body
        for i, body in enumerate(bodies):
            if not body.fixed_position:
                integrator.integrate(body, forces[i], scaled_dt)
        
        # update simulation time
        self.active_system.time += scaled_dt
        
        # update statistics
        self.computation_time = time.perf_counter() - start_time
        self.total_energy = self.active_system.calculate_total_energy()
        
        # performance tracking
        self.frame_count += 1
        if self.frame_count % 60 == 0:
            elapsed = time.time() - self.start_time
            self.avg_fps = self.frame_count / elapsed if elapsed > 0 else 0
    
    def create_orbit(self, central_body, orbiting_body, distance, eccentricity=0, clockwise=True):
        """Set up an orbiting body with correct initial velocity"""
        if distance <= 0:
            return
        
        # position the orbiting body at the correct distance
        angle = np.random.random() * 2 * np.pi
        orbiting_body.position = central_body.position + Vector2(
            distance * np.cos(angle),
            distance * np.sin(angle)
        )
        
        # calculate orbital velocity for circular or elliptical orbit
        G = self.gravitational_constant
        total_mass = central_body.mass + orbiting_body.mass
        
        if eccentricity == 0:  # circular orbit
            orbital_speed = np.sqrt(G * total_mass / distance)
        else:  # elliptical orbit
            
            semi_major_axis = distance / (1 + eccentricity)
            orbital_speed = np.sqrt(G * total_mass * (2/distance - 1/semi_major_axis))
        
        # velocity direction (perpendicular to position vector)
        direction = Vector2(-np.sin(angle), np.cos(angle))
        if not clockwise:
            direction = direction * -1
        
        orbiting_body.velocity = central_body.velocity + direction * orbital_speed
        orbiting_body.parent = central_body
    
    def reset_simulation(self):
        """Reset the active simulation"""
        if self.active_system:
            self.active_system.time = 0
            for body in self.active_system.bodies:
                body.previous_positions.clear()
    
    def get_statistics(self):
        """Get simulation statistics"""
        return {
            'fps': self.avg_fps,
            'computation_time_ms': self.computation_time * 1000,
            'total_energy': self.total_energy,
            'body_count': len(self.active_system.bodies) if self.active_system else 0,
            'simulation_time_years': (self.active_system.time / 31557600) if self.active_system else 0,
            'physics_model': self.current_physics,
            'integrator': self.current_integrator,
        }