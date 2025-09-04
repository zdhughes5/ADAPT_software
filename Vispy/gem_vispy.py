# -*- coding: utf-8 -*-
"""
3D Visualization of a Scientific Space Instrument using VisPy.

This script models a gamma-ray detector as a 3D cube. On one face of the
cube, photodetectors are represented as pixels. The script simulates
discrete gamma-ray events by lighting up random pixels and having their
intensity decay over time.

Key Features:
- A 3D cube representing the instrument body.
- A grid of 'pixels' fixed to the +X face representing photodetectors.
- Alternating square and round pixel shapes.
- Real-time animation of simulated detector events with intensity decay.
- Interactive 3D camera (turntable) for exploring the model.
- A dark theme for clear visibility of the brightly colored pixels.

Changes from previous version:
- Pixels are now rendered as part of the 3D scene (scaling='scene'), so they
  correctly rotate with the cube instead of always facing the camera.
- The simulation logic has been improved to show discrete "hits" with a
  gradual decay, making the animation more realistic and visually clear.
- Fixed a ValueError by setting colormap interpolation to 'zero', avoiding a
  broadcasting error in the underlying VisPy library.
"""
import numpy as np
from vispy import app, scene
from vispy.color import get_colormap

# --- Configuration Constants ---
N_PIXELS_PER_ROW = 20  # Number of photodetector pixels in one row
N_LAYERS = 5           # Number of layers (rows of pixels on the face)
TOTAL_PIXELS = N_PIXELS_PER_ROW * N_LAYERS
CUBE_SIZE = 10         # The side length of the main instrument cube
# Pixel size is now in scene units, not screen pixels.
# We calculate it to be slightly smaller than the grid spacing.
PIXEL_SCENE_SIZE = (CUBE_SIZE * 0.9) / N_PIXELS_PER_ROW
UPDATE_INTERVAL = 0.05 # Seconds between data updates (increased frequency)
COLORMAP = 'hot'   # Switched to 'hot' for a better "glowing" effect

# --- Main Visualization Class ---

class InstrumentCanvas(scene.SceneCanvas):
    """
    A VisPy Canvas for displaying the 3D instrument model.
    """
    def __init__(self):
        # Initialize the canvas with a dark background and a title
        scene.SceneCanvas.__init__(self,
                                   keys='interactive',
                                   size=(800, 700),
                                   show=True,
                                   title='Gamma-Ray Instrument Visualization')
        self.unfreeze()

        # Create a ViewBox to hold the 3D scene.
        self.view = self.central_widget.add_view()
        self.view.bgcolor = '#212121'  # Dark grey background for contrast

        # Set up a 3D camera. 'turntable' allows rotation with the mouse.
        self.view.camera = scene.TurntableCamera(fov=45,
                                                 elevation=30,
                                                 azimuth=-45,
                                                 distance=CUBE_SIZE * 3,
                                                 center=(0, 0, 0))

        # Add a visual for the main instrument body (a semi-transparent cube)
        self.instrument_cube = scene.visuals.Cube(
            size=CUBE_SIZE,
            color=(0.5, 0.5, 0.8, 0.2), # RGBA: semi-transparent light blue
            edge_color='white',
            parent=self.view.scene
        )

        # Prepare data for the photodetector pixels
        self.pixel_positions = self._create_pixel_positions()
        self.pixel_symbols = self._create_pixel_symbols()
        self.cmap = get_colormap(COLORMAP)
        # Fix for ValueError: change interpolation method to avoid broadcasting error
        self.cmap.interpolation = 'zero'
        
        # This array will hold the current intensity of each pixel and will be
        # updated by the simulation.
        self.intensities = np.zeros(TOTAL_PIXELS, dtype=np.float32)

        # Add a Markers visual to represent the pixels
        self.pixels = scene.visuals.Markers(
            pos=self.pixel_positions,
            symbol=self.pixel_symbols,
            size=PIXEL_SCENE_SIZE,
            edge_width=0,
            scaling='scene',  # <-- KEY CHANGE: Makes pixels part of the 3D scene
            parent=self.view.scene
        )

        # Add axes to provide a frame of reference
        self.axes = scene.visuals.XYZAxis(parent=self.view.scene)

        # Set up a timer to call the update_data method periodically
        self.timer = app.Timer(UPDATE_INTERVAL, connect=self.update_data, start=True)

        self.freeze()

    def _create_pixel_positions(self):
        """
        Generates the 3D coordinates for each pixel on the +X face of the cube.
        """
        # The +X face is at x = CUBE_SIZE / 2
        # We add a small offset to prevent z-fighting (visual glitches)
        x_pos = CUBE_SIZE / 2 + 0.01 # Reduced offset

        # Create a grid of y and z coordinates for the pixels
        # We scale by 0.9 to leave a small margin around the edge of the face
        face_half_size = CUBE_SIZE / 2 * 0.9
        y_coords = np.linspace(-face_half_size, face_half_size, N_PIXELS_PER_ROW)
        z_coords = np.linspace(-face_half_size, face_half_size, N_LAYERS)
        
        # Use meshgrid to create all combinations of y and z
        yy, zz = np.meshgrid(y_coords, z_coords)

        # Create the final (N, 3) position array
        positions = np.zeros((TOTAL_PIXELS, 3), dtype=np.float32)
        positions[:, 0] = x_pos
        positions[:, 1] = yy.ravel()
        positions[:, 2] = zz.ravel()
        
        return positions

    def _create_pixel_symbols(self):
        """
        Generates an array of symbols for the pixels, alternating
        between square and round.
        """
        symbols = np.full(TOTAL_PIXELS, 'o', dtype=object) # Default to round ('o' or 'disc')
        symbols[::2] = 's' # Set every other pixel to square ('s')
        return symbols

    def update_data(self, event):
        """
        This method is called by the timer. It simulates new data by creating
        random "hits" and letting all pixel intensities decay over time.
        """
        # 1. Apply a decay factor to all existing intensities.
        # This makes the lit pixels fade out over time.
        self.intensities *= 0.85

        # 2. Simulate a small number of new gamma-ray hits.
        num_hits = np.random.randint(0, 4) # 0 to 3 new hits per frame
        if num_hits > 0:
            # Pick random pixel indices to apply the new hits
            hit_indices = np.random.randint(0, TOTAL_PIXELS, size=num_hits)
            # Set the intensity of these pixels to the maximum (1.0)
            self.intensities[hit_indices] = 1.0

        # 3. Map the updated intensity values (0-1) to RGBA colors
        colors = self.cmap.map(self.intensities)

        # 4. Update the 'face_color' property of the Markers visual
        self.pixels.set_data(face_color=colors)

    def on_key_press(self, event):
        """Close the application when 'q' or 'escape' is pressed."""
        if event.key == 'Escape' or event.key == 'q':
            self.close()


if __name__ == '__main__':
    # Create an instance of our canvas
    canvas = InstrumentCanvas()
    
    # Print instructions to the console
    print("--------------------------------------------------")
    print("Interactive 3D Instrument Visualization")
    print(" - Left-click and drag to rotate the camera.")
    print(" - Right-click and drag to zoom.")
    print(" - Press 'q' or 'Escape' to close the window.")
    print("--------------------------------------------------")
    
    # Start the VisPy application event loop
    app.run()
