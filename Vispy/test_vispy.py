#!/usr/bin/env python3
"""
Test script to verify VisPy installation and basic functionality.
"""

import sys
import numpy as np

print("Testing VisPy installation...")
print("=" * 40)

try:
    import vispy
    print(f"✓ VisPy version: {vispy.__version__}")
except ImportError as e:
    print(f"✗ VisPy import failed: {e}")
    sys.exit(1)

try:
    import numpy as np
    print(f"✓ NumPy version: {np.__version__}")
except ImportError as e:
    print(f"✗ NumPy import failed: {e}")
    sys.exit(1)

# Test VisPy backends
print("\nTesting VisPy backends:")
from vispy import app

backends = ['pyqt5', 'pyqt6', 'pyside2', 'pyside6', 'glfw', 'sdl2']
available_backends = []

for backend in backends:
    try:
        app.use_app(backend)
        print(f"✓ {backend} backend available")
        available_backends.append(backend)
    except Exception:
        print(f"✗ {backend} backend not available")

if not available_backends:
    print("✗ No VisPy backends available!")
    sys.exit(1)

# Test basic VisPy functionality
print(f"\nTesting basic VisPy functionality with {available_backends[0]}...")
try:
    app.use_app(available_backends[0])
    from vispy import scene
    from vispy.color import get_colormap
    
    # Test colormap
    cmap = get_colormap('plasma')
    test_data = np.random.random(10)
    colors = cmap.map(test_data)
    print(f"✓ Colormap test passed - generated {len(colors)} colors")
    
    # Test scene creation (without showing)
    canvas = scene.SceneCanvas(
        keys='interactive',
        size=(800, 600),
        show=False,  # Don't show the window
        title='Test Canvas'
    )
    view = canvas.central_widget.add_view()
    print("✓ Scene canvas creation test passed")
    
    # Test cube creation
    cube = scene.visuals.Cube(
        size=5.0,
        color=(0.5, 0.5, 0.8, 0.2),
        parent=view.scene
    )
    print("✓ Cube visual creation test passed")
    
    # Test markers creation
    positions = np.random.random((20, 3)) * 10 - 5  # 20 random 3D points
    markers = scene.visuals.Markers(
        pos=positions,
        symbol='o',
        size=10,
        parent=view.scene
    )
    print("✓ Markers visual creation test passed")
    
    canvas.close()
    print("✓ All tests passed!")
    
except Exception as e:
    print(f"✗ VisPy functionality test failed: {e}")
    sys.exit(1)

print("\n" + "=" * 40)
print("VisPy is ready for gamma-ray detector visualization!")
print(f"Recommended backend: {available_backends[0]}")
print("=" * 40)
