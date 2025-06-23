#!/usr/bin/env python3

import json

# Load sensor geometry config.
with open("sensor_config.json", "r") as f:
    sensor_config = json.load(f)

def calculate_total_data_points():
    """Calculate total data points needed based on sensor configuration"""
    num_icc_layers = sensor_config["icc"]["num_layers"]
    num_hodo_pixels_per_layer = sensor_config["hodo_front"]["num_cols"] * sensor_config["hodo_front"]["num_rows"]
    num_wls_pixels_per_layer = sensor_config["wls_front"]["num_cols"]
    num_csi_pixels = 2
    num_tail_pixels = sensor_config["tail_counters"]["num_cols"] * sensor_config["tail_counters"]["num_rows"]
    num_hodo_pixels = num_hodo_pixels_per_layer * 2
    num_wls_pixels = num_wls_pixels_per_layer * 2
    num_pixels_per_layer = num_hodo_pixels + num_wls_pixels + num_csi_pixels + num_tail_pixels
    
    print(f"num_icc_layers: {num_icc_layers}")
    print(f"num_hodo_pixels_per_layer: {num_hodo_pixels_per_layer}")
    print(f"num_wls_pixels_per_layer: {num_wls_pixels_per_layer}")
    print(f"num_csi_pixels: {num_csi_pixels}")
    print(f"num_tail_pixels: {num_tail_pixels}")
    print(f"num_pixels_per_layer: {num_pixels_per_layer}")
    print(f"total: {num_icc_layers * num_pixels_per_layer}")
    
    return num_icc_layers * num_pixels_per_layer

def generate_odd_even_list(length, offset=0, even_first=False):
    numbers = list(range(offset, offset + length))
    odd_values = [n for n in numbers if n % 2 != 0]
    even_values = [n for n in numbers if n % 2 == 0]
    if even_first:
        return even_values + odd_values
    else:
        return odd_values + even_values

def test_hodo_front_mapping():
    print("\n=== Testing hodo_front mapping ===")
    
    # Test with original config (14 cols)
    num_hodo_pixels_per_layer = 14 * 2  # 28
    offset = 0
    mapping = generate_odd_even_list(num_hodo_pixels_per_layer, offset=offset)
    
    print(f"Mapping length: {len(mapping)}")
    print(f"Expected pixels: {14 * 2}")
    print(f"Mapping: {mapping}")
    
    # Test indexing
    num_cols = 14
    num_rows = 2
    try:
        for row in range(num_rows):
            for col in range(num_cols):
                idx = row * num_cols + col
                print(f"Row {row}, Col {col} -> index {idx} -> mapped to {mapping[idx]}")
    except IndexError as e:
        print(f"IndexError: {e}")

if __name__ == "__main__":
    calculate_total_data_points()
    test_hodo_front_mapping()
