#!/usr/bin/env python3
"""
Simple Gamma-Ray Detector Surface Visualization

This is a focused implementation that creates exactly what you requested:
- A 3D cube representing the detector
- Surface subdivided into pixels (square and round)
- Color-coded intensity display for photodetectors
- 20 pixels per row, 5 x-y layers
- Real-time event streaming visualization

This version is simpler and more focused on the surface pixel visualization.
"""

import numpy as np
from vispy import app, scene
from vispy.color import get_colormap
import time

# Configuration
N_PIXELS_PER_ROW = 20
N_LAYERS = 5
CUBE_SIZE = 10.0
PIXEL_SIZE = 0.8
UPDATE_INTERVAL = 0.1
DECAY_RATE = 0.88
EVENT_PROBABILITY = 0.4

class DetectorSurfaceVisualization(scene.SceneCanvas):
    """Simple detector surface visualization with color-coded pixels."""
    
    def __init__(self):
        super().__init__(
            keys='interactive',
            size=(1000, 800),
            show=True,
            title='Gamma-Ray Detector - Surface Pixels',
            bgcolor='#1a1a1a'
        )
        
        # Initialize data
        self.n_pixels = N_PIXELS_PER_ROW
        self.n_layers = N_LAYERS
        self.total_pixels = self.n_pixels * self.n_layers
        
        # Setup 3D scene
        self.view = self.central_widget.add_view()
        self.view.bgcolor = '#222222'
        self.view.camera = scene.TurntableCamera(
            fov=45,
            elevation=30,
            azimuth=45,
            distance=CUBE_SIZE * 3.5,
            center=(0, 0, 0)
        )
        
        # Create colormap for intensity visualization
        self.colormap = get_colormap('plasma')
        
        # Initialize intensity arrays for each face
        self.face_intensities = {
            'front': np.zeros((self.n_layers, self.n_pixels)),   # +X face
            'back': np.zeros((self.n_layers, self.n_pixels)),    # -X face
            'right': np.zeros((self.n_layers, self.n_pixels)),   # +Y face
            'left': np.zeros((self.n_layers, self.n_pixels)),    # -Y face
            'top': np.zeros((self.n_layers, self.n_pixels)),     # +Z face
            'bottom': np.zeros((self.n_layers, self.n_pixels)),  # -Z face
        }
        
        # Create detector components
        self._create_detector_cube()
        self._create_surface_pixels()
        self._create_info_display()
        
        # Start simulation timer
        self.timer = app.Timer(
            interval=UPDATE_INTERVAL,
            connect=self.update_simulation,
            start=True
        )
        
        self.event_count = 0
        print("Surface visualization ready!")
        print("Controls: Mouse to rotate, scroll to zoom, 'q' to quit")
    
    def _create_detector_cube(self):
        """Create the main detector cube."""
        self.cube = scene.visuals.Cube(
            size=CUBE_SIZE,
            color=(0.2, 0.3, 0.5, 0.1),  # Very transparent
            edge_color=(0.7, 0.7, 0.7, 0.6),
            parent=self.view.scene
        )
    
    def _create_surface_pixels(self):
        """Create pixel arrays on each face of the cube."""
        self.pixel_visuals = {}
        half_size = CUBE_SIZE / 2
        
        # Define face configurations: (normal_axis, u_axis, v_axis, position_offset)
        face_configs = {
            'front':  ('x', 'y', 'z', (half_size + 0.05, 0, 0)),
            'back':   ('x', 'y', 'z', (-half_size - 0.05, 0, 0)),
            'right':  ('y', 'x', 'z', (0, half_size + 0.05, 0)),
            'left':   ('y', 'x', 'z', (0, -half_size - 0.05, 0)),
            'top':    ('z', 'x', 'y', (0, 0, half_size + 0.05)),
            'bottom': ('z', 'x', 'y', (0, 0, -half_size - 0.05)),
        }
        
        for face_name, (normal, u_axis, v_axis, offset) in face_configs.items():
            positions, symbols = self._create_face_pixels(offset, u_axis, v_axis)
            
            markers = scene.visuals.Markers(
                pos=positions,
                symbol=symbols,
                size=PIXEL_SIZE * 15,  # Scale for visibility
                edge_width=0.5,
                edge_color='white',
                scaling='scene',
                parent=self.view.scene
            )
            
            self.pixel_visuals[face_name] = markers
    
    def _create_face_pixels(self, offset, u_axis, v_axis):
        """Create pixel positions and symbols for a single face."""
        positions = []
        symbols = []
        
        # Create grid coordinates
        half_size = CUBE_SIZE / 2 * 0.85  # Leave margin
        u_coords = np.linspace(-half_size, half_size, self.n_pixels)
        v_coords = np.linspace(-half_size, half_size, self.n_layers)
        
        for layer_idx, v in enumerate(v_coords):
            for pixel_idx, u in enumerate(u_coords):
                # Create position based on face orientation
                pos = [0, 0, 0]
                
                if u_axis == 'x':
                    pos[0] = u
                elif u_axis == 'y':
                    pos[1] = u
                else:  # u_axis == 'z'
                    pos[2] = u
                
                if v_axis == 'x':
                    pos[0] = v
                elif v_axis == 'y':
                    pos[1] = v
                else:  # v_axis == 'z'
                    pos[2] = v
                
                # Add face offset
                pos[0] += offset[0]
                pos[1] += offset[1]
                pos[2] += offset[2]
                
                positions.append(pos)
                
                # Alternate between square and round pixels
                if (layer_idx + pixel_idx) % 2 == 0:
                    symbols.append('s')  # Square
                else:
                    symbols.append('o')  # Round
        
        return np.array(positions, dtype=np.float32), np.array(symbols, dtype=object)
    
    def _create_info_display(self):
        """Create information display."""
        info_text = """Gamma-Ray Detector
20 pixels/row × 5 layers
Surface pixel intensity display
Real-time event simulation"""
        
        self.info_label = scene.visuals.Text(
            text=info_text,
            pos=(CUBE_SIZE * 0.8, CUBE_SIZE * 0.8, CUBE_SIZE * 0.8),
            color='white',
            font_size=10,
            parent=self.view.scene
        )
        
        # Add coordinate axes
        self.axes = scene.visuals.XYZAxis(
            parent=self.view.scene,
            width=2
        )
    
    def update_simulation(self, event):
        """Update detector simulation with new events."""
        # Decay all intensities
        for face in self.face_intensities:
            self.face_intensities[face] *= DECAY_RATE
        
        # Generate new events
        if np.random.random() < EVENT_PROBABILITY:
            self._simulate_gamma_event()
            self.event_count += 1
        
        # Update pixel colors
        self._update_pixel_colors()
        
        # Update info display periodically
        if self.event_count % 50 == 0:
            self._update_info_display()
    
    def _simulate_gamma_event(self):
        """Simulate a gamma-ray event hitting the detector."""
        # Choose random face(s) to activate
        faces_to_activate = np.random.choice(
            list(self.face_intensities.keys()),
            size=np.random.randint(1, 4),  # 1-3 faces
            replace=False
        )
        
        for face in faces_to_activate:
            # Create localized event on this face
            center_layer = np.random.randint(0, self.n_layers)
            center_pixel = np.random.randint(0, self.n_pixels)
            
            # Event intensity with spatial spread
            event_intensity = np.random.uniform(0.7, 1.0)
            spread_radius = np.random.randint(1, 4)  # pixels
            
            # Apply intensity to neighboring pixels
            for layer_offset in range(-spread_radius, spread_radius + 1):
                for pixel_offset in range(-spread_radius, spread_radius + 1):
                    layer_idx = center_layer + layer_offset
                    pixel_idx = center_pixel + pixel_offset
                    
                    # Check bounds
                    if (0 <= layer_idx < self.n_layers and 
                        0 <= pixel_idx < self.n_pixels):
                        
                        # Distance-based intensity falloff
                        distance = np.sqrt(layer_offset**2 + pixel_offset**2)
                        intensity = event_intensity * np.exp(-distance / 2)
                        
                        # Add to existing intensity (with saturation)
                        current = self.face_intensities[face][layer_idx, pixel_idx]
                        self.face_intensities[face][layer_idx, pixel_idx] = min(1.0, current + intensity)
    
    def _update_pixel_colors(self):
        """Update pixel colors based on current intensities."""
        for face_name, markers in self.pixel_visuals.items():
            intensities = self.face_intensities[face_name].flatten()
            colors = self.colormap.map(intensities)
            markers.set_data(face_color=colors)
    
    def _update_info_display(self):
        """Update information display with current statistics."""
        max_intensity = max(
            np.max(intensities) 
            for intensities in self.face_intensities.values()
        )
        
        info_text = f"""Gamma-Ray Detector
20 pixels/row × 5 layers
Events detected: {self.event_count}
Max intensity: {max_intensity:.2f}
Surface pixel intensity display"""
        
        self.info_label.text = info_text
    
    def on_key_press(self, event):
        """Handle keyboard input."""
        if event.key == 'Escape' or event.key == 'q':
            self.close()
        elif event.key == 'r':
            # Reset camera
            self.view.camera.reset()
        elif event.key == 'c':
            # Clear all intensities
            for face in self.face_intensities:
                self.face_intensities[face].fill(0)
            print("Cleared all detector intensities")
        elif event.key == 's':
            # Save screenshot
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"detector_surface_{timestamp}.png"
            img = self.render()
            from vispy import io
            io.write_png(filename, img)
            print(f"Screenshot saved: {filename}")


def main():
    """Main entry point."""
    print("Gamma-Ray Detector Surface Visualization")
    print("=" * 40)
    print("Features:")
    print("- 3D cube with surface pixels")
    print("- 20 pixels per row, 5 layers")
    print("- Mixed square/round pixel shapes")
    print("- Real-time intensity color coding")
    print("- Event streaming simulation")
    print()
    print("Controls:")
    print("- Mouse: Rotate view")
    print("- Scroll: Zoom")
    print("- 'r': Reset view")
    print("- 'c': Clear intensities")
    print("- 's': Save screenshot")
    print("- 'q': Quit")
    print("=" * 40)
    
    try:
        app.use_app('pyqt5')  # Use PyQt5 backend (available in conda)
        canvas = DetectorSurfaceVisualization()
        app.run()
    except Exception as e:
        print(f"Error: {e}")
        print("\nTrying alternative backend...")
        try:
            app.use_app('pyqt6')  # Fallback to PyQt6
            canvas = DetectorSurfaceVisualization()
            app.run()
        except Exception as e2:
            print(f"Error with PyQt6: {e2}")
            print("\nPlease install required packages:")
            print("conda install vispy numpy pyqt")


if __name__ == '__main__':
    main()
