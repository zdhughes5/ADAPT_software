"""
VisPy demo: cubic detector + surface pixels (20 per row, 5 layers).

This revised script uses an efficient, vectorized approach by creating one
Mesh visual for all square pixels and one for all round pixels, rather than
creating a separate visual for each pixel. This is much more performant.

- Semi-transparent cube for context
- On the +X face of the cube, a 20x5 grid of "photodetector pixels"
  * Even (row+col) -> square pixel
  * Odd  (row+col) -> round pixel
- Colors (RGBA) map intensity via a colormap
- A timer simulates events by updating intensities every ~0.5 s

Requirements:
    pip install vispy numpy pyqt6
"""

import sys
from vispy import app, scene, color
import numpy as np

# It's good practice to select the backend at the start.
# If you have multiple Qt bindings, this ensures you use the one you want.
app.use_app('pyqt6')

# ----------------------
# Config
# ----------------------
N_COLS = 20         # pixels per row
N_ROWS = 5          # number of layers
PIX_SIZE = 0.15     # size of each pixel (world units)
CIRCLE_SIDES = 24   # smoothness for round pixels
EPS = 0.05          # offset from cube surface so pixels are visible
UPDATE_MS = 500     # timer period (ms)

# Use a colormap to map scalar intensity values to RGBA colors
cmap = color.get_colormap('viridis')

# ----------------------
# Canvas + 3D scene
# ----------------------
canvas = scene.SceneCanvas(keys='interactive',
                           size=(1100, 800),
                           show=True,
                           title="Scintillating Fiber Gamma-Ray Tracker",
                           bgcolor=(0.1, 0.1, 0.1, 1))
view = canvas.central_widget.add_view()
view.camera = scene.cameras.TurntableCamera(fov=45,
                                            azimuth=45,
                                            elevation=30,
                                            distance=4.0,
                                            up='+y')

# A faint box to suggest the instrument volume (2x2x2 cube centered at origin)
box = scene.visuals.Box(width=2.0, height=2.0, depth=2.0,
                        color=(0.2, 0.2, 0.2, 0.07),
                        edge_color=(0.8, 0.8, 0.8, 0.2),
                        parent=view.scene)

# Orientation helper
axis = scene.visuals.XYZAxis(parent=view.scene)

# ----------------------
# Build the +X face pixel panel
# ----------------------
# Calculate the y and z positions for the center of each pixel
margin_z = 0.1
margin_y = 0.1
z_positions = np.linspace(-1 + margin_z, 1 - margin_z, N_COLS)
y_positions = np.linspace(-1 + margin_y, 1 - margin_y, N_ROWS)

# --- Prepare lists to aggregate geometry for all pixels ---
square_verts, square_faces, square_face_colors = [], [], []
disc_verts, disc_faces, disc_face_colors = [], [], []

# We need to keep track of the number of vertices to correctly index the faces
square_vert_offset = 0
disc_vert_offset = 0

# --- Generate geometry and initial colors ---
intensities = np.random.rand(N_ROWS, N_COLS)

# Store unique colors and an index array for each mesh type
unique_square_colors, square_color_indices = [], []
unique_disc_colors, disc_color_indices = [], []

for r, y in enumerate(y_positions):
    for c, z in enumerate(z_positions):
        intensity = 0.2 + 0.8 * np.random.rand()  # avoid too-dark pixels
        rgba = cmap[intensity].rgba

        if (r + c) % 2 == 0:
            # --- Square Pixel (Quad) ---
            x = 1.0 + EPS
            h = PIX_SIZE * 0.5
            # Define vertices for one square
            verts = np.array([
                [x, y - h, z - h], [x, y + h, z - h],
                [x, y + h, z + h], [x, y - h, z + h],
            ], dtype=np.float32)
            # Define the two triangle faces for the square
            # The indices must be offset by the number of vertices already added
            faces = np.array([[0, 1, 2], [0, 2, 3]], dtype=np.uint32) + square_vert_offset
            
            square_verts.append(verts)
            square_faces.append(faces)
            # Add color and face-to-color mapping
            color_index = len(unique_square_colors)
            unique_square_colors.append(rgba)
            square_color_indices.extend([color_index, color_index]) # Both faces same color
            square_vert_offset += 4 # We added 4 vertices
        else:
            # --- Round Pixel (Disc) ---
            x = 1.0 + EPS
            radius = PIX_SIZE * 0.5
            # Define center and ring vertices for one disc
            center = np.array([[x, y, z]], dtype=np.float32)
            angles = np.linspace(0, 2 * np.pi, CIRCLE_SIDES, endpoint=False)
            ring = np.stack([
                np.full_like(angles, x),
                y + radius * np.cos(angles),
                z + radius * np.sin(angles)
            ], axis=1).astype(np.float32)
            
            verts = np.vstack([center, ring])
            
            # Create faces by connecting the center to adjacent points on the ring
            idxs = [[0, i, i + 1] for i in range(1, CIRCLE_SIDES)]
            idxs.append([0, CIRCLE_SIDES, 1]) # Last face connects back to the start
            faces = np.array(idxs, dtype=np.uint32) + disc_vert_offset

            disc_verts.append(verts)
            disc_faces.append(faces)
            # Add color and face-to-color mapping
            color_index = len(unique_disc_colors)
            unique_disc_colors.append(rgba)
            disc_color_indices.extend([color_index] * len(faces)) # All faces same color
            disc_vert_offset += (1 + CIRCLE_SIDES) # We added a center + ring vertices

# --- Create the final Mesh visuals from the aggregated geometry ---
# One visual for all squares
if square_verts:
    all_square_verts = np.vstack(square_verts)
    all_square_faces = np.vstack(square_faces)
    square_pixels_mesh = scene.visuals.Mesh(
        vertices=all_square_verts, faces=all_square_faces,
        face_colors=(np.array(unique_square_colors), np.array(square_color_indices)),
        shading=None, parent=view.scene
    )

# One visual for all discs
if disc_verts:
    all_disc_verts = np.vstack(disc_verts)
    all_disc_faces = np.vstack(disc_faces)
    disc_pixels_mesh = scene.visuals.Mesh(
        vertices=all_disc_verts, faces=all_disc_faces,
        face_colors=(np.array(unique_disc_colors), np.array(disc_color_indices)),
        shading=None, parent=view.scene
    )

# ----------------------
# Event update loop (simulate gamma-ray events)
# ----------------------
def update_event(event=None):
    """
    This function is called by the timer. It generates a new random intensity
    pattern and updates the face colors of the mesh visuals.
    """
    global intensities
    
    # --- Generate a new semi-realistic "track" of high intensity ---
    base = np.zeros((N_ROWS, N_COLS), dtype=np.float32)
    start_col = np.random.randint(0, N_COLS // 3)
    slope = np.random.uniform(-0.2, 0.2)
    for r in range(N_ROWS):
        col = int(np.clip(start_col + slope * r * N_COLS / N_ROWS, 0, N_COLS - 1))
        for dc in [-1, 0, 1]:
            cc = np.clip(col + dc, 0, N_COLS - 1)
            base[r, cc] = 1.0
    # Add some random "salt and pepper" noise hits
    for _ in range(10):
        rr = np.random.randint(0, N_ROWS)
        cc = np.random.randint(0, N_COLS)
        base[rr, cc] = max(base[rr, cc], np.random.uniform(0.3, 0.9))
    
    noise = 0.15 * np.random.rand(N_ROWS, N_COLS)
    intensities = np.clip(base + noise, 0, 1)

    # --- Recalculate colors and update the meshes ---
    new_square_colors = []
    new_disc_colors = []
    
    # Iterate through the grid and assign new colors based on the logic used for creation
    for r in range(N_ROWS):
        for c in range(N_COLS):
            rgba = cmap[intensities[r, c]].rgba
            if (r + c) % 2 == 0:
                # This was a square
                new_square_colors.append(rgba)
            else:
                # This was a disc
                new_disc_colors.append(rgba)
    
    # Update the visuals with the new color arrays
    if square_verts:
        square_pixels_mesh.set_data(face_colors=(np.array(new_square_colors), square_pixels_mesh.mesh_data.face_colors.indexed))
    if disc_verts:
        disc_pixels_mesh.set_data(face_colors=(np.array(new_disc_colors), disc_pixels_mesh.mesh_data.face_colors.indexed))


# Create and start a timer that calls the update function periodically
timer = app.Timer(interval=UPDATE_MS / 1000.0, connect=update_event, start=True)

# Start the VisPy event loop
if __name__ == '__main__':
    print("Starting VisPy application... Close the window to exit.")
    if sys.flags.interactive != 1:
        app.run()
