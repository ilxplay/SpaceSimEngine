from utils.vectors import Vector2
import numpy as np

class Integrator:
    """Base class for numerical integration methods"""
    
    def integrate(self, body, net_force, dt):
        raise NotImplementedError

class EulerIntegrator(Integrator):
    """Simple Euler integration (fast but less accurate)"""
    
    def integrate(self, body, net_force, dt):
        # update acceleration
        body.acceleration = net_force / body.mass
        
        # update velocity
        body.velocity = body.velocity + body.acceleration * dt
        
        # update position
        body.position = body.position + body.velocity * dt
        
        # store previous state for trails
        body.previous_positions.append(body.position.copy())
        if len(body.previous_positions) > body.trail_length:
            body.previous_positions.pop(0)

class VerletIntegrator(Integrator):
    """Verlet integration (more stable for orbital mechanics)"""
    
    def integrate(self, body, net_force, dt):
        # store previous position
        old_position = body.position.copy()
        
        # calculate new position
        acceleration = net_force / body.mass
        new_position = body.position * 2 - body.previous_position + acceleration * dt**2
        
        # update velocity (for display purposes)
        body.velocity = (new_position - body.previous_position) / (2 * dt)
        
        # update positions
        body.previous_position = old_position
        body.position = new_position
        body.acceleration = acceleration
        
        # store trail
        body.previous_positions.append(body.position.copy())
        if len(body.previous_positions) > body.trail_length:
            body.previous_positions.pop(0)

class RK4Integrator(Integrator):
    """4th Order Runge-Kutta integration (high accuracy)""" 
    
    def integrate(self, body, net_force, dt):
      
        k1_v = net_force / body.mass * dt
        k1_p = body.velocity * dt
        
        mid_force = net_force 
        
        k2_v = mid_force / body.mass * dt
        k2_p = (body.velocity + k1_v/2) * dt
        
        # position and velocity are updated using weighted average of slopes
        body.velocity = body.velocity + (k1_v + 2*k2_v) / 3
        body.position = body.position + (k1_p + 2*k2_p) / 3
        body.acceleration = net_force / body.mass
        
        body.previous_positions.append(body.position.copy())
        if len(body.previous_positions) > body.trail_length:
            body.previous_positions.pop(0)