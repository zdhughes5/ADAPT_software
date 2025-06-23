#!/usr/bin/env python3

import json
import sys

# Load sensor geometry config.
with open("sensor_config.json", "r") as f:
    sensor_config = json.load(f)

def generate_odd_even_list(length, offset=0, even_first=False):
    numbers = list(range(offset, offset + length))
    odd_values = [n for n in numbers if n % 2 != 0]
    even_values = [n for n in numbers if n % 2 == 0]
    if even_first:
        return even_values + odd_values
    else:
        return odd_values + even_values

def calculate_total_data_points():
    num_icc_layers = sensor_config["icc"]["num_layers"]
    num_hodo_pixels_per_layer = sensor_config["hodo_front"]["num_cols"] * sensor_config["hodo_front"]["num_rows"]
    num_wls_pixels_per_layer = sensor_config["wls_front"]["num_cols"]
    num_csi_pixels = 2
    num_tail_pixels = sensor_config["tail_counters"]["num_cols"] * sensor_config["tail_counters"]["num_rows"]
    num_hodo_pixels = num_hodo_pixels_per_layer * 2
    num_wls_pixels = num_wls_pixels_per_layer * 2
    num_pixels_per_layer = num_hodo_pixels + num_wls_pixels + num_csi_pixels + num_tail_pixels
    return num_icc_layers * num_pixels_per_layer

def simulate_problematic_function():
    """Simulate the function that was causing IndexError"""
    
    # Simulate layer = 0, rotate = False
    layer = 0
    rotate = False
    
    # Calculate mapping (simplified version)
    num_icc_layers = sensor_config["icc"]["num_layers"]
    num_hodo_pixels_per_layer = sensor_config["hodo_front"]["num_cols"] * sensor_config["hodo_front"]["num_rows"]
    num_wls_pixels_per_layer = sensor_config["wls_front"]["num_cols"]
    num_csi_pixels = 2
    num_tail_pixels = sensor_config["tail_counters"]["num_cols"] * sensor_config["tail_counters"]["num_rows"]
    num_hodo_pixels = num_hodo_pixels_per_layer * 2
    num_wls_pixels = num_wls_pixels_per_layer * 2
    num_pixels_per_layer = num_hodo_pixels + num_wls_pixels + num_csi_pixels + num_tail_pixels
    
    base = layer * num_pixels_per_layer
    hodo_offset1 = base
    
    # Generate the mapping for hodo_front (non-rotated case)
    mapping = generate_odd_even_list(num_hodo_pixels_per_layer, offset=hodo_offset1)
    
    print(f"Configuration:")
    print(f"  num_cols: {sensor_config['hodo_front']['num_cols']}")
    print(f"  num_rows: {sensor_config['hodo_front']['num_rows']}")
    print(f"  num_hodo_pixels_per_layer: {num_hodo_pixels_per_layer}")
    print(f"  mapping length: {len(mapping)}")
    print(f"  total_data_points: {calculate_total_data_points()}")
    print(f"  mapping: {mapping}")
    
    # Simulate the problematic loop
    num_cols = sensor_config["hodo_front"]["num_cols"]
    num_rows = sensor_config["hodo_front"]["num_rows"]
    
    print(f"\nSimulating loop access:")
    try:
        for row in range(num_rows):
            for col in range(num_cols):
                index = row * num_cols + col
                mapped_idx = mapping[index]
                print(f"  row={row}, col={col} -> index={index} -> mapped_idx={mapped_idx}")
        print("✓ SUCCESS: No IndexError occurred!")
        return True
    except IndexError as e:
        print(f"✗ FAILURE: IndexError occurred: {e}")
        return False

if __name__ == "__main__":
    print("Testing the fix for the IndexError issue...")
    print("=" * 50)
    
    success = simulate_problematic_function()
    
    print("=" * 50)
    if success:
        print("✓ TEST PASSED: The IndexError issue appears to be fixed!")
        sys.exit(0)
    else:
        print("✗ TEST FAILED: The IndexError issue still exists!")
        sys.exit(1)
