#!/usr/bin/env python3
"""
Advanced Gamma-Ray Scintillating Fiber Detector Visualization

This script models a scientific space instrument that uses scintillating fibers
to detect gamma-ray radiation. The visualization shows:

1. A 3D cube representing the detector volume
2. Multiple X-Y layers of fiber planes (5 layers total)
3. Each layer contains photodetectors at the edges (20 pixels per row)
4. Sequential fiber layers are oriented perpendicular to each other
5. Real-time visualization of gamma-ray events as they stream in
6. Mixed pixel shapes (square and round photodetectors)
7. Color-coded intensity mapping for photodetector responses

The detector geometry:
- 5 X-Y layers stacked in the Z direction
- Each layer has fibers running in alternating X and Y directions
- 20 photodetectors per row on each face
- Events propagate through multiple layers creating 3D tracks

Usage:
    python gamma_ray_detector.py

Controls:
    - Mouse: Rotate view
    - Scroll: Zoom
    - 'q' or ESC: Quit
    - 'r': Reset view
    - 's': Save screenshot
    - 'p': Pause/resume simulation
"""

import numpy as np
from vispy import app, scene, io
from vispy.color import get_colormap
from vispy.geometry import create_cube, create_cylinder
import sys
import time
from pathlib import Path

# Configuration
CONFIG = {
    'n_pixels_per_row': 20,    # Photodetectors per row
    'n_layers': 5,             # Number of fiber layers
    'cube_size': 10.0,         # Detector volume size
    'pixel_size': 0.4,         # Photodetector size
    'fiber_radius': 0.02,      # Scintillating fiber radius
    'update_interval': 0.1,    # Animation update rate (seconds)
    'decay_rate': 0.90,        # Intensity decay per frame
    'event_rate': 0.3,         # Probability of new event per frame
    'max_events_per_frame': 3, # Maximum simultaneous events
    'colormap': 'plasma',      # Color scheme for intensity
    'window_size': (1200, 900), # Display window size
}

class GammaRayDetector:
    """
    Represents the physical detector with scintillating fibers and photodetectors.
    """
    
    def __init__(self, config):
        self.config = config
        self.n_pixels = config['n_pixels_per_row']
        self.n_layers = config['n_layers']
        self.cube_size = config['cube_size']
        
        # Initialize intensity arrays for each detector face
        self.intensities = {
            'x_positive': np.zeros((self.n_layers, self.n_pixels)),
            'x_negative': np.zeros((self.n_layers, self.n_pixels)),
            'y_positive': np.zeros((self.n_layers, self.n_pixels)),
            'y_negative': np.zeros((self.n_layers, self.n_pixels)),
        }
        
        # Track active events (for creating realistic detector signatures)
        self.active_events = []
        
    def create_pixel_positions(self, face):
        """Generate 3D positions for photodetectors on a specific face."""
        positions = []
        half_size = self.cube_size / 2
        margin = half_size * 0.9  # Leave margin at edges
        
        # Create grid coordinates
        pixel_coords = np.linspace(-margin, margin, self.n_pixels)
        layer_coords = np.linspace(-margin, margin, self.n_layers)
        
        if face == 'x_positive':
            x_pos = half_size + 0.02
            for layer_idx, z in enumerate(layer_coords):
                for pixel_idx, y in enumerate(pixel_coords):
                    positions.append([x_pos, y, z])
                    
        elif face == 'x_negative':
            x_pos = -half_size - 0.02
            for layer_idx, z in enumerate(layer_coords):
                for pixel_idx, y in enumerate(pixel_coords):
                    positions.append([x_pos, y, z])
                    
        elif face == 'y_positive':
            y_pos = half_size + 0.02
            for layer_idx, z in enumerate(layer_coords):
                for pixel_idx, x in enumerate(pixel_coords):
                    positions.append([x, y_pos, z])
                    
        elif face == 'y_negative':
            y_pos = -half_size - 0.02
            for layer_idx, z in enumerate(layer_coords):
                for pixel_idx, x in enumerate(pixel_coords):
                    positions.append([x, y_pos, z])
        
        return np.array(positions, dtype=np.float32)
    
    def create_pixel_symbols(self, face):
        """Create alternating square and round pixel shapes."""
        symbols = []
        for layer_idx in range(self.n_layers):
            for pixel_idx in range(self.n_pixels):
                # Alternate between square and round based on position
                if (layer_idx + pixel_idx) % 2 == 0:
                    symbols.append('s')  # Square
                else:
                    symbols.append('o')  # Round
        return np.array(symbols, dtype=object)
    
    def simulate_gamma_event(self):
        """Simulate a gamma-ray event passing through the detector."""
        if np.random.random() > self.config['event_rate']:
            return
            
        # Generate random entry and exit points
        entry_point = np.random.uniform(-self.cube_size/2, self.cube_size/2, 3)
        direction = np.random.uniform(-1, 1, 3)
        direction = direction / np.linalg.norm(direction)  # Normalize
        
        # Create event with multiple interaction points
        event = {
            'entry_point': entry_point,
            'direction': direction,
            'energy': np.random.exponential(1.0),  # Exponential energy distribution
            'interactions': self._calculate_interactions(entry_point, direction),
            'lifetime': 20,  # Frames to live
        }
        
        self.active_events.append(event)
    
    def _calculate_interactions(self, entry_point, direction):
        """Calculate where the gamma ray interacts with fibers."""
        interactions = []
        current_pos = entry_point.copy()
        remaining_energy = 1.0
        
        # Simulate interactions in each layer
        for layer in range(self.n_layers):
            if remaining_energy < 0.1:
                break
                
            # Calculate interaction probability
            if np.random.random() < 0.7:  # 70% chance of interaction per layer
                # Energy deposited in this layer
                deposited_energy = np.random.exponential(0.3) * remaining_energy
                deposited_energy = min(deposited_energy, remaining_energy)
                
                interactions.append({
                    'layer': layer,
                    'position': current_pos.copy(),
                    'energy': deposited_energy,
                })
                
                remaining_energy -= deposited_energy
            
            # Move to next layer
            current_pos += direction * (self.cube_size / self.n_layers)
        
        return interactions
    
    def update_intensities(self):
        """Update photodetector intensities based on active events."""
        # Apply decay to all intensities
        for face in self.intensities:
            self.intensities[face] *= self.config['decay_rate']
        
        # Process active events
        for event in self.active_events[:]:
            for interaction in event['interactions']:
                self._add_light_to_detectors(interaction)
            
            event['lifetime'] -= 1
            if event['lifetime'] <= 0:
                self.active_events.remove(event)
    
    def _add_light_to_detectors(self, interaction):
        """Add light signal to appropriate photodetectors."""
        layer = interaction['layer']
        position = interaction['position']
        energy = interaction['energy']
        
        # Determine which detectors see this light based on fiber orientation
        # Odd layers have X-oriented fibers, even layers have Y-oriented fibers
        if layer % 2 == 0:  # Y-oriented fibers
            # Light travels to Y faces
            self._add_signal_to_face('y_positive', layer, position, energy)
            self._add_signal_to_face('y_negative', layer, position, energy)
        else:  # X-oriented fibers
            # Light travels to X faces
            self._add_signal_to_face('x_positive', layer, position, energy)
            self._add_signal_to_face('x_negative', layer, position, energy)
    
    def _add_signal_to_face(self, face, layer, position, energy):
        """Add signal to specific face and layer."""
        # Determine which pixel receives the light
        half_size = self.cube_size / 2
        margin = half_size * 0.9
        
        if face.startswith('x'):
            # For X faces, position along Y axis determines pixel
            pixel_coord = position[1]
        else:
            # For Y faces, position along X axis determines pixel
            pixel_coord = position[0]
        
        # Map position to pixel index
        pixel_idx = int((pixel_coord + margin) / (2 * margin) * self.n_pixels)
        pixel_idx = np.clip(pixel_idx, 0, self.n_pixels - 1)
        
        # Add intensity with distance attenuation
        distance_factor = np.exp(-abs(pixel_coord) / (self.cube_size / 4))
        intensity = energy * distance_factor * 0.5
        
        current_intensity = self.intensities[face][layer, pixel_idx]
        self.intensities[face][layer, pixel_idx] = min(1.0, current_intensity + intensity)


class DetectorVisualization(scene.SceneCanvas):
    """
    VisPy-based 3D visualization of the gamma-ray detector.
    """
    
    def __init__(self, config):
        super().__init__(
            keys='interactive',
            size=config['window_size'],
            show=True,
            title='Scintillating Fiber Gamma-Ray Detector',
            bgcolor='#1e1e1e'
        )
        
        self.config = config
        self.detector = GammaRayDetector(config)
        self.paused = False
        
        # Set up 3D scene
        self.view = self.central_widget.add_view()
        self.view.bgcolor = '#2a2a2a'
        self.view.camera = scene.TurntableCamera(
            fov=50,
            elevation=25,
            azimuth=45,
            distance=config['cube_size'] * 4,
            center=(0, 0, 0)
        )
        
        # Create colormap
        self.colormap = get_colormap(config['colormap'])
        
        # Create 3D objects
        self._create_detector_cube()
        self._create_fiber_structure()
        self._create_photodetectors()
        self._create_axes()
        
        # Set up animation timer
        self.timer = app.Timer(
            interval=config['update_interval'],
            connect=self.update_simulation,
            start=True
        )
        
        print("Detector visualization initialized")
        print("Controls: Mouse to rotate, scroll to zoom, 'q' to quit, 'p' to pause")
    
    def _create_detector_cube(self):
        """Create the main detector volume."""
        self.detector_cube = scene.visuals.Cube(
            size=self.config['cube_size'],
            color=(0.3, 0.3, 0.6, 0.15),  # Semi-transparent blue
            edge_color=(0.8, 0.8, 0.8, 0.8),
            parent=self.view.scene
        )
    
    def _create_fiber_structure(self):
        """Create visual representation of fiber layers."""
        self.fiber_visuals = []
        half_size = self.config['cube_size'] / 2
        layer_spacing = self.config['cube_size'] / self.config['n_layers']
        
        for layer in range(self.config['n_layers']):
            z_pos = -half_size + (layer + 0.5) * layer_spacing
            
            # Create fiber grid for this layer
            if layer % 2 == 0:  # Y-oriented fibers
                color = (0.8, 0.4, 0.4, 0.3)  # Red
                self._create_fiber_grid(z_pos, 'y', color)
            else:  # X-oriented fibers
                color = (0.4, 0.8, 0.4, 0.3)  # Green
                self._create_fiber_grid(z_pos, 'x', color)
    
    def _create_fiber_grid(self, z_pos, orientation, color):
        """Create a grid of fibers at a specific Z position."""
        half_size = self.config['cube_size'] / 2
        n_fibers = self.config['n_pixels_per_row']
        fiber_positions = np.linspace(-half_size * 0.9, half_size * 0.9, n_fibers)
        
        for pos in fiber_positions:
            if orientation == 'x':
                # Fiber runs along X axis
                start = np.array([-half_size, pos, z_pos])
                end = np.array([half_size, pos, z_pos])
            else:
                # Fiber runs along Y axis
                start = np.array([pos, -half_size, z_pos])
                end = np.array([pos, half_size, z_pos])
            
            line = scene.visuals.Line(
                pos=np.array([start, end]),
                color=color,
                width=2,
                parent=self.view.scene
            )
            self.fiber_visuals.append(line)
    
    def _create_photodetectors(self):
        """Create photodetector arrays on detector faces."""
        self.detector_visuals = {}
        
        faces = ['x_positive', 'x_negative', 'y_positive', 'y_negative']
        
        for face in faces:
            positions = self.detector.create_pixel_positions(face)
            symbols = self.detector.create_pixel_symbols(face)
            
            # Create markers for this face
            markers = scene.visuals.Markers(
                pos=positions,
                symbol=symbols,
                size=self.config['pixel_size'] * 20,  # Scale for visibility
                edge_width=1,
                edge_color='white',
                scaling='scene',
                parent=self.view.scene
            )
            
            self.detector_visuals[face] = markers
    
    def _create_axes(self):
        """Add coordinate axes for reference."""
        self.axes = scene.visuals.XYZAxis(
            parent=self.view.scene,
            width=3
        )
        
        # Add text labels
        axis_labels = scene.visuals.Text(
            text="Scintillating Fiber Detector\nRed: Y-fibers, Green: X-fibers",
            pos=(self.config['cube_size'] * 0.7, self.config['cube_size'] * 0.7, self.config['cube_size'] * 0.7),
            color='white',
            font_size=12,
            parent=self.view.scene
        )
    
    def update_simulation(self, event):
        """Update the detector simulation and visualization."""
        if self.paused:
            return
            
        # Simulate new gamma-ray events
        self.detector.simulate_gamma_event()
        
        # Update detector intensities
        self.detector.update_intensities()
        
        # Update visual colors
        self._update_detector_colors()
    
    def _update_detector_colors(self):
        """Update photodetector colors based on current intensities."""
        for face, markers in self.detector_visuals.items():
            intensities = self.detector.intensities[face].flatten()
            colors = self.colormap.map(intensities)
            markers.set_data(face_color=colors)
    
    def on_key_press(self, event):
        """Handle keyboard input."""
        if event.key == 'Escape' or event.key == 'q':
            self.close()
        elif event.key == 'r':
            # Reset camera view
            self.view.camera.reset()
        elif event.key == 'p':
            # Pause/resume simulation
            self.paused = not self.paused
            print(f"Simulation {'paused' if self.paused else 'resumed'}")
        elif event.key == 's':
            # Save screenshot
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"detector_screenshot_{timestamp}.png"
            img = self.render()
            io.write_png(filename, img)
            print(f"Screenshot saved as {filename}")


def main():
    """Main entry point."""
    print("Starting Gamma-Ray Detector Visualization...")
    print("=" * 50)
    print("Controls:")
    print("  Mouse: Rotate view")
    print("  Scroll: Zoom in/out")
    print("  'r': Reset view")
    print("  'p': Pause/resume simulation")
    print("  's': Save screenshot")
    print("  'q' or ESC: Quit")
    print("=" * 50)
    
    # Check if required packages are available
    try:
        visualization = DetectorVisualization(CONFIG)
        app.run()
    except ImportError as e:
        print(f"Error: Missing required package - {e}")
        print("Please install required packages:")
        print("  pip install vispy numpy pyqt6")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting visualization: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
