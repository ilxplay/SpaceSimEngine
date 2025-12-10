import pygame
from .vectors import Vector2
import math

class Camera:
    """Camera for viewing the simulation at different scales"""
    
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        self.position = Vector2(0, 0)
        
        self.scale = 1e9  # 1 pixel = 1e9 meters
        
        self.min_scale = 1e3   # 1 pixel = 1 km
        self.max_scale = 1e15  # 1 pixel = 1 light-year
        
        self.target_scale = self.scale
        self.zoom_speed = 0.1
        
        self.is_dragging = False
        self.drag_start = Vector2(0, 0)
        self.drag_start_pos = Vector2(0, 0)
        
        self.margin_left = 300
        self.margin_right = 300
        self.margin_top = 50
        self.margin_bottom = 200
    
    def world_to_screen(self, world_pos):
        """Convert world coordinates to screen coordinates"""
        center_x = self.screen_width / 2
        center_y = self.screen_height / 2
        
        # convert
        screen_x = center_x + (world_pos.x - self.position.x) / self.scale
        screen_y = center_y - (world_pos.y - self.position.y) / self.scale  # Y inverted
        
        return Vector2(screen_x, screen_y)
    
    def screen_to_world(self, screen_pos):
        """Convert screen coordinates to world coordinates"""
        center_x = self.screen_width / 2
        center_y = self.screen_height / 2
        
        world_x = self.position.x + (screen_pos.x - center_x) * self.scale
        world_y = self.position.y - (screen_pos.y - center_y) * self.scale  # Y inverted
        
        return Vector2(world_x, world_y)
    
    def zoom(self, factor, mouse_pos=None):
        """Zoom in/out around mouse position"""
        if mouse_pos:
            # get world position under mouse before zoom
            world_pos_before = self.screen_to_world(mouse_pos)
            
            self.target_scale *= factor
            self.target_scale = max(self.min_scale, min(self.max_scale, self.target_scale))
            
            # smooth zoom
            self.scale += (self.target_scale - self.scale) * self.zoom_speed
            
            # get pos after zoom
            world_pos_after = self.screen_to_world(mouse_pos)
            
            # adjust camera posiyion
            self.position = self.position + (world_pos_after - world_pos_before)
        else:
          
            self.target_scale *= factor
            self.target_scale = max(self.min_scale, min(self.max_scale, self.target_scale))
            self.scale += (self.target_scale - self.scale) * self.zoom_speed
    
    def pan(self, dx, dy):
        """Pan the camera"""
        self.position.x -= dx * self.scale
        self.position.y += dy * self.scale  # Y inverted
    
    def center_on(self, world_pos):
        """Center camera on a world position"""
        self.position = world_pos.copy()
    
    def fit_to_bodies(self, bodies, padding=0.1):
        """Adjust camera to fit all bodies in view"""
        if not bodies:
            return
        
        min_x = float('inf')
        max_x = float('-inf')
        min_y = float('inf')
        max_y = float('-inf')
        
        for body in bodies:
            pos = body.position
            radius = body.radius
            min_x = min(min_x, pos.x - radius)
            max_x = max(max_x, pos.x + radius)
            min_y = min(min_y, pos.y - radius)
            max_y = max(max_y, pos.y + radius)
        
        width = max_x - min_x
        height = max_y - min_y
        min_x -= width * padding
        max_x += width * padding
        min_y -= height * padding
        max_y += height * padding
        
        # calculate required scale
        screen_width = self.screen_width - self.margin_left - self.margin_right
        screen_height = self.screen_height - self.margin_top - self.margin_bottom
        
        scale_x = (max_x - min_x) / screen_width if screen_width > 0 else self.scale
        scale_y = (max_y - min_y) / screen_height if screen_height > 0 else self.scale
        
        # use the larger scale to fit everything
        new_scale = max(scale_x, scale_y)
        
        # update camera
        self.scale = new_scale
        self.target_scale = new_scale
        
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        self.center_on(Vector2(center_x, center_y))
    
    def update(self, dt):
        # smooth zoom interpolation
        if abs(self.scale - self.target_scale) > self.scale * 0.001:
            self.scale += (self.target_scale - self.scale) * self.zoom_speed * dt * 60
    
    def handle_event(self, event):
        """Handle camera-related events"""
        if event.type == pygame.MOUSEWHEEL:
            # zoom with mouse wheel
            zoom_factor = 1.1 if event.y > 0 else 0.9
            mouse_pos = Vector2(*pygame.mouse.get_pos())
            self.zoom(zoom_factor, mouse_pos)
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 2:  # middle mouse
                # start dragging
                self.is_dragging = True
                self.drag_start = Vector2(*event.pos)
                self.drag_start_pos = self.position.copy()
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 2:
                # stop dragging
                self.is_dragging = False
                
        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                # pan camera
                current_pos = Vector2(*event.pos)
                delta = current_pos - self.drag_start
                self.position = self.drag_start_pos - delta * self.scale
    
    def get_visible_grid_range(self):
        """Get visible world coordinates range"""
        top_left = self.screen_to_world(Vector2(0, 0))
        bottom_right = self.screen_to_world(Vector2(self.screen_width, self.screen_height))
        
        return {
            'min_x': min(top_left.x, bottom_right.x),
            'max_x': max(top_left.x, bottom_right.x),
            'min_y': min(top_left.y, bottom_right.y),
            'max_y': max(top_left.y, bottom_right.y),
        }