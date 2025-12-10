import pygame
import pygame_gui
from pygame_gui.elements import UIWindow, UIButton, UILabel, UIHorizontalSlider, UITextEntryLine, UIDropDownMenu
from pygame_gui.core import ObjectID
import numpy as np
import bodies.celestial_body as cb
import utils.vectors as vec

class CelestialUI:
    
    def __init__(self, screen_width, screen_height, physics_engine):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.physics_engine = physics_engine
        
        self.gui_manager = pygame_gui.UIManager((screen_width, screen_height))
        
        self.panels = {}
        self.create_ui_panels()
        
        self.show_physics_panel = True
        self.show_body_editor = True
        self.show_simulation_info = True
        self.current_tool = 'select'  # select, add_body, add_velocity
        
        self.BACKGROUND = (20, 20, 40)
        self.PANEL_BG = (30, 30, 50, 200)
        self.TEXT_COLOR = (220, 220, 255)
        self.HIGHLIGHT_COLOR = (100, 150, 255)
    
    def create_ui_panels(self):
        self.create_simulation_control_panel()
        self.create_physics_settings_panel()
        self.create_body_editor_panel()
        self.create_info_panel()
        self.create_preset_panel()
    
    def create_simulation_control_panel(self):
        panel_width = 250
        panel_height = 150
        panel_x = 10
        panel_y = 10
        
        # create panel background
        self.panels['control'] = UIWindow(
            rect=pygame.Rect(panel_x, panel_y, panel_width, panel_height),
            manager=self.gui_manager,
            window_display_title="Simulation Controls",
            object_id=ObjectID(object_id="@control_panel")
        )
        
        button_y = 30
        button_spacing = 35
        
        # play/pause button
        self.play_button = UIButton(
            relative_rect=pygame.Rect(10, button_y, 100, 30),
            text="Pause" if self.physics_engine.is_running else "Play",
            manager=self.gui_manager,
            container=self.panels['control'],
            object_id=ObjectID(object_id="@play_button")
        )
        
        # reset button
        self.reset_button = UIButton(
            relative_rect=pygame.Rect(120, button_y, 100, 30),
            text="Reset",
            manager=self.gui_manager,
            container=self.panels['control'],
            object_id=ObjectID(object_id="@reset_button")
        )
        
        button_y += button_spacing
        
        # time scale slider
        self.time_scale_label = UILabel(
            relative_rect=pygame.Rect(10, button_y, 100, 25),
            text=f"Time Scale: {self.physics_engine.time_scale:.1f}x",
            manager=self.gui_manager,
            container=self.panels['control']
        )
        
        self.time_scale_slider = UIHorizontalSlider(
            relative_rect=pygame.Rect(120, button_y, 100, 25),
            start_value=self.physics_engine.time_scale,
            value_range=(0.1, 1000.0),
            manager=self.gui_manager,
            container=self.panels['control']
        )
    
    def create_physics_settings_panel(self):
        """Create physics settings panel"""
        panel_width = 300
        panel_height = 250
        panel_x = 10
        panel_y = 170
        
        self.panels['physics'] = UIWindow(
            rect=pygame.Rect(panel_x, panel_y, panel_width, panel_height),
            manager=self.gui_manager,
            window_display_title="Physics Settings",
            object_id=ObjectID(object_id="@physics_panel")
        )
        
        # physics model dropdown
        y_offset = 30
        UILabel(
            relative_rect=pygame.Rect(10, y_offset, 120, 25),
            text="Physics Model:",
            manager=self.gui_manager,
            container=self.panels['physics']
        )
        
        self.physics_dropdown = UIDropDownMenu(
            options_list=['newtonian', 'relativistic'],
            starting_option=self.physics_engine.current_physics,
            relative_rect=pygame.Rect(140, y_offset, 140, 30),
            manager=self.gui_manager,
            container=self.panels['physics']
        )
        
        y_offset += 40
        
        # integrator dropdown
        UILabel(
            relative_rect=pygame.Rect(10, y_offset, 120, 25),
            text="Integrator:",
            manager=self.gui_manager,
            container=self.panels['physics']
        )
        
        self.integrator_dropdown = UIDropDownMenu(
            options_list=['euler', 'verlet', 'rk4'],
            starting_option=self.physics_engine.current_integrator,
            relative_rect=pygame.Rect(140, y_offset, 140, 30),
            manager=self.gui_manager,
            container=self.panels['physics']
        )
        
        y_offset += 40
        
        # gravitational constant slider
        UILabel(
            relative_rect=pygame.Rect(10, y_offset, 120, 25),
            text=f"G: {self.physics_engine.gravitational_constant:.2e}",
            manager=self.gui_manager,
            container=self.panels['physics']
        )
        
        # log scale slider for G (covers many orders of magnitude)
        log_G = np.log10(self.physics_engine.gravitational_constant)
        self.G_slider = UIHorizontalSlider(
            relative_rect=pygame.Rect(140, y_offset, 140, 25),
            start_value=log_G,
            value_range=(-20, -8),  # 10^-20 to 10^-8
            manager=self.gui_manager,
            container=self.panels['physics']
        )
        
        y_offset += 40
        
        # collision toggle
        self.collision_toggle = UIButton(
            relative_rect=pygame.Rect(10, y_offset, 140, 30),
            text="Collisions: OFF",
            manager=self.gui_manager,
            container=self.panels['physics']
        )
        
        # trail toggle
        self.trail_toggle = UIButton(
            relative_rect=pygame.Rect(160, y_offset, 120, 30),
            text="Trails: ON",
            manager=self.gui_manager,
            container=self.panels['physics']
        )
    
    def create_body_editor_panel(self):
        """Create body creation/editing panel"""
        panel_width = 300
        panel_height = 400
        panel_x = self.screen_width - panel_width - 10
        panel_y = 10
        
        self.panels['body_editor'] = UIWindow(
            rect=pygame.Rect(panel_x, panel_y, panel_width, panel_height),
            manager=self.gui_manager,
            window_display_title="Body Editor",
            object_id=ObjectID(object_id="@body_editor")
        )
        
        # body type selection
        y_offset = 30
        self.body_type_dropdown = UIDropDownMenu(
            options_list=['star', 'planet', 'gas_giant', 'moon', 'asteroid', 'black_hole'],
            starting_option='planet',
            relative_rect=pygame.Rect(10, y_offset, 280, 30),
            manager=self.gui_manager,
            container=self.panels['body_editor']
        )
        
        y_offset += 40
        
        # name input
        UILabel(
            relative_rect=pygame.Rect(10, y_offset, 100, 25),
            text="Name:",
            manager=self.gui_manager,
            container=self.panels['body_editor']
        )
        
        self.body_name_input = UITextEntryLine(
            relative_rect=pygame.Rect(120, y_offset, 170, 30),
            manager=self.gui_manager,
            container=self.panels['body_editor']
        )
        self.body_name_input.set_text("New Body")
        
        y_offset += 40
        
        # mass input (log scale)
        UILabel(
            relative_rect=pygame.Rect(10, y_offset, 100, 25),
            text="Mass (kg):",
            manager=self.gui_manager,
            container=self.panels['body_editor']
        )
        
        self.mass_slider = UIHorizontalSlider(
            relative_rect=pygame.Rect(120, y_offset, 170, 25),
            start_value=24,  # 10^24 kg (Earth mass)
            value_range=(10, 35),  # 10^10 to 10^35 kg
            manager=self.gui_manager,
            container=self.panels['body_editor']
        )
        
        self.mass_label = UILabel(
            relative_rect=pygame.Rect(10, y_offset + 25, 280, 25),
            text="1.00e24 kg",
            manager=self.gui_manager,
            container=self.panels['body_editor']
        )
        
        y_offset += 60
        
        # position inputs
        UILabel(
            relative_rect=pygame.Rect(10, y_offset, 280, 25),
            text="Position (m):",
            manager=self.gui_manager,
            container=self.panels['body_editor']
        )
        
        y_offset += 25
        
        # x position
        UILabel(
            relative_rect=pygame.Rect(10, y_offset, 30, 25),
            text="X:",
            manager=self.gui_manager,
            container=self.panels['body_editor']
        )
        
        self.pos_x_input = UITextEntryLine(
            relative_rect=pygame.Rect(40, y_offset, 110, 30),
            manager=self.gui_manager,
            container=self.panels['body_editor']
        )
        self.pos_x_input.set_text("0")
        
        # y position
        UILabel(
            relative_rect=pygame.Rect(160, y_offset, 30, 25),
            text="Y:",
            manager=self.gui_manager,
            container=self.panels['body_editor']
        )
        
        self.pos_y_input = UITextEntryLine(
            relative_rect=pygame.Rect(190, y_offset, 100, 30),
            manager=self.gui_manager,
            container=self.panels['body_editor']
        )
        self.pos_y_input.set_text("0")
        
        y_offset += 40
        
        # velocity inputs
        UILabel(
            relative_rect=pygame.Rect(10, y_offset, 280, 25),
            text="Velocity (m/s):",
            manager=self.gui_manager,
            container=self.panels['body_editor']
        )
        
        y_offset += 25
        
        # x velocity
        UILabel(
            relative_rect=pygame.Rect(10, y_offset, 30, 25),
            text="Vx:",
            manager=self.gui_manager,
            container=self.panels['body_editor']
        )
        
        self.vel_x_input = UITextEntryLine(
            relative_rect=pygame.Rect(40, y_offset, 110, 30),
            manager=self.gui_manager,
            container=self.panels['body_editor']
        )
        self.vel_x_input.set_text("0")
        
        # y velocity
        UILabel(
            relative_rect=pygame.Rect(160, y_offset, 30, 25),
            text="Vy:",
            manager=self.gui_manager,
            container=self.panels['body_editor']
        )
        
        self.vel_y_input = UITextEntryLine(
            relative_rect=pygame.Rect(190, y_offset, 100, 30),
            manager=self.gui_manager,
            container=self.panels['body_editor']
        )
        self.vel_y_input.set_text("0")
        
        y_offset += 40
        
        # create body button
        self.create_body_button = UIButton(
            relative_rect=pygame.Rect(10, y_offset, 280, 40),
            text="Create Body",
            manager=self.gui_manager,
            container=self.panels['body_editor'],
            object_id=ObjectID(object_id="@create_body_button")
        )
        
        # delete selected button
        self.delete_body_button = UIButton(
            relative_rect=pygame.Rect(10, y_offset + 45, 280, 30),
            text="Delete Selected",
            manager=self.gui_manager,
            container=self.panels['body_editor']
        )
    
    def create_info_panel(self):
        """Create simulation information panel"""
        panel_width = 300
        panel_height = 200
        panel_x = self.screen_width - panel_width - 10
        panel_y = self.screen_height - panel_height - 10
        
        self.panels['info'] = UIWindow(
            rect=pygame.Rect(panel_x, panel_y, panel_width, panel_height),
            manager=self.gui_manager,
            window_display_title="Simulation Info",
            object_id=ObjectID(object_id="@info_panel")
        )
        
        # info labels will be updated dynamically
        self.info_labels = {}
        
        y_offset = 30
        labels = [
            ("FPS:", "fps"),
            ("Bodies:", "body_count"),
            ("Time:", "simulation_time"),
            ("Energy:", "total_energy"),
            ("Physics:", "physics_model"),
            ("Integrator:", "integrator"),
        ]
        
        for label_text, key in labels:
            # label
            UILabel(
                relative_rect=pygame.Rect(10, y_offset, 100, 25),
                text=label_text,
                manager=self.gui_manager,
                container=self.panels['info']
            )
            
            # value
            self.info_labels[key] = UILabel(
                relative_rect=pygame.Rect(120, y_offset, 170, 25),
                text="--",
                manager=self.gui_manager,
                container=self.panels['info']
            )
            
            y_offset += 25
    
    def create_preset_panel(self):
        """Create preset solar systems panel"""
        panel_width = 200
        panel_height = 200
        panel_x = 10
        panel_y = self.screen_height - panel_height - 10
        
        self.panels['presets'] = UIWindow(
            rect=pygame.Rect(panel_x, panel_y, panel_width, panel_height),
            manager=self.gui_manager,
            window_display_title="Preset Systems",
            object_id=ObjectID(object_id="@preset_panel")
        )
        
        y_offset = 30
        presets = [
            ("Solar System", "load_solar_system"),
            ("Binary Stars", "load_binary_stars"),
            ("Empty System", "load_empty"),
            ("Galaxy Core", "load_galaxy_core"),
        ]
        
        for preset_name, callback in presets:
            button = UIButton(
                relative_rect=pygame.Rect(10, y_offset, 180, 30),
                text=preset_name,
                manager=self.gui_manager,
                container=self.panels['presets']
            )
            button.callback = callback
            y_offset += 35
    
    def handle_events(self, event):
        """Handle UI events"""
        self.gui_manager.process_events(event)
        
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            self.handle_button_press(event)
        elif event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            self.handle_dropdown_change(event)
        elif event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
            self.handle_slider_change(event)
    
    def handle_button_press(self, event):
        """Handle button press events"""
        if event.ui_element == self.play_button:
            self.physics_engine.is_running = not self.physics_engine.is_running
            self.play_button.set_text("Pause" if self.physics_engine.is_running else "Play")
            
        elif event.ui_element == self.reset_button:
            self.physics_engine.reset_simulation()
            
        elif event.ui_element == self.collision_toggle:
            self.physics_engine.enable_collisions = not self.physics_engine.enable_collisions
            self.collision_toggle.set_text(
                f"Collisions: {'ON' if self.physics_engine.enable_collisions else 'OFF'}"
            )
            
        elif event.ui_element == self.trail_toggle:
            self.physics_engine.enable_trails = not self.physics_engine.enable_trails
            self.trail_toggle.set_text(
                f"Trails: {'ON' if self.physics_engine.enable_trails else 'OFF'}"
            )
            
        elif event.ui_element == self.create_body_button:
            self.create_new_body()
            
        elif event.ui_element == self.delete_body_button:
            # delete selected body (implementation depends on selection system)
            pass
    
    def handle_dropdown_change(self, event):
        """Handle dropdown menu changes"""
        if event.ui_element == self.physics_dropdown:
            self.physics_engine.set_physics_model(event.text)
            
        elif event.ui_element == self.integrator_dropdown:
            self.physics_engine.set_integrator(event.text)
    
    def handle_slider_change(self, event):
        """Handle slider changes"""
        if event.ui_element == self.time_scale_slider:
            self.physics_engine.time_scale = event.value
            self.time_scale_label.set_text(f"Time Scale: {event.value:.1f}x")
            
        elif event.ui_element == self.G_slider:
            # convert from log scale
            new_G = 10 ** event.value
            self.physics_engine.set_gravitational_constant(new_G)
            
            # update label
            for element in self.panels['physics'].elements:
                if isinstance(element, UILabel) and element.text.startswith("G:"):
                    element.set_text(f"G: {new_G:.2e}")
                    
        elif event.ui_element == self.mass_slider:
            mass = 10 ** event.value
            self.mass_label.set_text(f"{mass:.2e} kg")
    
    def create_new_body(self):
        """Create a new celestial body from UI inputs"""
        try:
          
            body_type = self.body_type_dropdown.selected_option
            
            # create appropriate body class
            if body_type == 'star':
                body = cb.Star()
            elif body_type == 'black_hole':
                body = cb.BlackHole()
            elif body_type == 'gas_giant':
                body = cb.CelestialBody(body_type='gas_giant')
            elif body_type == 'moon':
                body = cb.CelestialBody(body_type='moon')
            elif body_type == 'asteroid':
                body = cb.CelestialBody(body_type='asteroid')
            else:
                body = cb.Planet()
            
            # set properties from ui
            body.name = self.body_name_input.get_text()
            
            # mass from slider (log scale)
            mass_power = self.mass_slider.get_current_value()
            body.mass = 10 ** mass_power
            
            pos_x = float(self.pos_x_input.get_text())
            pos_y = float(self.pos_y_input.get_text())
            body.position = vec.Vector2(pos_x, pos_y)
            
            vel_x = float(self.vel_x_input.get_text())
            vel_y = float(self.vel_y_input.get_text())
            body.velocity = vec.Vector2(vel_x, vel_y)
            
            if self.physics_engine.active_system:
                self.physics_engine.active_system.add_body(body)
                print(f"Created body: {body.name}")
            
        except ValueError as e:
            print(f"Error creating body: {e}")
    
    def update_info_panel(self, stats):
        """Update the information panel with current statistics"""
        if 'fps' in self.info_labels:
            self.info_labels['fps'].set_text(f"{stats.get('fps', 0):.1f}")
        
        if 'body_count' in self.info_labels:
            self.info_labels['body_count'].set_text(str(stats.get('body_count', 0)))
        
        if 'simulation_time' in self.info_labels:
            years = stats.get('simulation_time_years', 0)
            self.info_labels['simulation_time'].set_text(f"{years:.2f} years")
        
        if 'total_energy' in self.info_labels:
            energy = stats.get('total_energy', 0)
            self.info_labels['total_energy'].set_text(f"{energy:.2e} J")
        
        if 'physics_model' in self.info_labels:
            self.info_labels['physics_model'].set_text(stats.get('physics_model', '--'))
        
        if 'integrator' in self.info_labels:
            self.info_labels['integrator'].set_text(stats.get('integrator', '--'))
    
    def update(self, dt):
        """Update UI"""
        self.gui_manager.update(dt)
    
    def draw(self, surface):
        """Draw UI"""
        self.gui_manager.draw_ui(surface)