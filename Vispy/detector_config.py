#!/usr/bin/env python3
"""
Configuration file for Gamma-Ray Detector Visualization

Modify these parameters to customize the detector geometry and simulation.
"""

# Detector Geometry
DETECTOR_CONFIG = {
    # Basic geometry
    'n_pixels_per_row': 20,        # Number of photodetectors per row
    'n_layers': 5,                 # Number of fiber layers (Z direction)
    'cube_size': 10.0,             # Physical size of detector volume
    
    # Pixel properties
    'pixel_size': 0.8,             # Size of photodetectors
    'pixel_margin': 0.85,          # Fraction of face used for pixels (0.85 = 15% margin)
    
    # Fiber properties
    'fiber_radius': 0.02,          # Radius of scintillating fibers
    'fiber_opacity': 0.3,          # Transparency of fiber visualization
    
    # Physics simulation
    'event_rate': 0.4,             # Probability of new event per frame (0-1)
    'max_events_per_frame': 3,     # Maximum simultaneous events
    'decay_rate': 0.88,            # Intensity decay per frame (0-1)
    'energy_distribution': 'exponential',  # 'exponential' or 'uniform'
    'interaction_probability': 0.7, # Probability of interaction per layer
    
    # Visualization
    'update_interval': 0.1,        # Animation update rate (seconds)
    'colormap': 'plasma',          # Color scheme: 'plasma', 'viridis', 'hot', 'cool'
    'window_size': (1200, 900),    # Display window size (width, height)
    'background_color': '#1a1a1a', # Background color
    
    # Camera settings
    'camera_fov': 45,              # Field of view (degrees)
    'camera_elevation': 30,        # Initial elevation angle
    'camera_azimuth': 45,          # Initial azimuth angle
    'camera_distance_factor': 3.5, # Distance = cube_size * this factor
}

# Face color schemes for different detector faces
FACE_COLORS = {
    'front':  (0.8, 0.2, 0.2, 0.1),  # Red
    'back':   (0.8, 0.2, 0.2, 0.1),  # Red
    'right':  (0.2, 0.8, 0.2, 0.1),  # Green
    'left':   (0.2, 0.8, 0.2, 0.1),  # Green
    'top':    (0.2, 0.2, 0.8, 0.1),  # Blue
    'bottom': (0.2, 0.2, 0.8, 0.1),  # Blue
}

# Fiber orientation by layer (for alternating X-Y fiber directions)
FIBER_ORIENTATIONS = {
    0: 'y',  # Layer 0: Y-oriented fibers
    1: 'x',  # Layer 1: X-oriented fibers
    2: 'y',  # Layer 2: Y-oriented fibers
    3: 'x',  # Layer 3: X-oriented fibers
    4: 'y',  # Layer 4: Y-oriented fibers
}

# Pixel shape patterns
PIXEL_PATTERNS = {
    'alternating': 'alternating',  # Alternate between square and round
    'checkerboard': 'checkerboard', # Checkerboard pattern
    'all_square': 'square',        # All square pixels
    'all_round': 'round',          # All round pixels
    'custom': 'custom',            # Define custom pattern
}

# Selected pixel pattern
SELECTED_PIXEL_PATTERN = 'alternating'

# Custom pixel pattern (if SELECTED_PIXEL_PATTERN = 'custom')
# Define as 2D array where 's' = square, 'o' = round
CUSTOM_PIXEL_PATTERN = [
    ['s', 'o', 's', 'o', 's'],
    ['o', 's', 'o', 's', 'o'],
    ['s', 'o', 's', 'o', 's'],
    ['o', 's', 'o', 's', 'o'],
]

# Keyboard shortcuts
KEYBOARD_CONTROLS = {
    'quit': ['q', 'Escape'],
    'reset_view': ['r'],
    'pause': ['p'],
    'save_screenshot': ['s'],
    'clear_detector': ['c'],
    'toggle_fibers': ['f'],
    'cycle_colormap': ['m'],
    'increase_event_rate': ['+', '='],
    'decrease_event_rate': ['-'],
}

# Available colormaps for cycling
AVAILABLE_COLORMAPS = [
    'plasma',
    'viridis', 
    'hot',
    'cool',
    'magma',
    'inferno',
    'cividis'
]

def get_pixel_symbol(layer_idx, pixel_idx, pattern=None):
    """
    Generate pixel symbol based on selected pattern.
    
    Args:
        layer_idx: Layer index (0 to n_layers-1)
        pixel_idx: Pixel index within layer (0 to n_pixels-1)
        pattern: Pattern type ('alternating', 'checkerboard', etc.)
    
    Returns:
        Symbol character ('s' for square, 'o' for round)
    """
    if pattern is None:
        pattern = SELECTED_PIXEL_PATTERN
    
    if pattern == 'alternating':
        return 's' if (layer_idx + pixel_idx) % 2 == 0 else 'o'
    elif pattern == 'checkerboard':
        return 's' if (layer_idx % 2) == (pixel_idx % 2) else 'o'
    elif pattern == 'square':
        return 's'
    elif pattern == 'round':
        return 'o'
    elif pattern == 'custom':
        if (layer_idx < len(CUSTOM_PIXEL_PATTERN) and 
            pixel_idx < len(CUSTOM_PIXEL_PATTERN[layer_idx])):
            return CUSTOM_PIXEL_PATTERN[layer_idx][pixel_idx]
        else:
            return 'o'  # Default fallback
    else:
        return 'o'  # Default fallback

def validate_config():
    """Validate configuration parameters."""
    config = DETECTOR_CONFIG
    
    # Check required parameters
    assert config['n_pixels_per_row'] > 0, "n_pixels_per_row must be positive"
    assert config['n_layers'] > 0, "n_layers must be positive"
    assert config['cube_size'] > 0, "cube_size must be positive"
    assert 0 < config['decay_rate'] <= 1, "decay_rate must be between 0 and 1"
    assert 0 <= config['event_rate'] <= 1, "event_rate must be between 0 and 1"
    
    print("Configuration validated successfully!")

if __name__ == '__main__':
    # Test configuration
    validate_config()
    print("Detector Configuration:")
    print("-" * 30)
    for key, value in DETECTOR_CONFIG.items():
        print(f"{key}: {value}")
    
    print(f"\nPixel Pattern: {SELECTED_PIXEL_PATTERN}")
    print("Sample pixel symbols:")
    for layer in range(min(3, DETECTOR_CONFIG['n_layers'])):
        symbols = [get_pixel_symbol(layer, pixel) 
                  for pixel in range(min(10, DETECTOR_CONFIG['n_pixels_per_row']))]
        print(f"Layer {layer}: {' '.join(symbols)}")
