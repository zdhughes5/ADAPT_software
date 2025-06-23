#!/usr/bin/env python3

import sys
import json

# Load sensor geometry config.
with open("sensor_config.json", "r") as f:
    sensor_config = json.load(f)

if sensor_config['hodo_front']['num_rows'] != 2:
    sys.exit("Error: hodo_front num_rows must be 2 for this code to work.")

def generate_odd_even_list(length, offset=0, even_first=False):
    numbers = list(range(offset, offset + length))
    odd_values = [n for n in numbers if n % 2 != 0]
    even_values = [n for n in numbers if n % 2 == 0]
    if even_first:
        return even_values + odd_values
    else:
        return odd_values + even_values

def generate_creation_order(num_pixels_per_row, offset=0, top_first=False):
    row1 = list(range(offset, offset + num_pixels_per_row))
    row2 = list(range(offset + num_pixels_per_row, offset + 2 * num_pixels_per_row))
    if top_first:
        return [val for pair in zip(row1, row2) for val in pair]
    else:
        return [val for pair in zip(row2, row1) for val in pair]

def generateDataMap():
    num_icc_layers = sensor_config["icc"]["num_layers"]
    num_hodo_pixels_per_layer = sensor_config["hodo_front"]["num_cols"] * sensor_config["hodo_front"]["num_rows"]
    num_wls_pixels_per_layer = sensor_config["wls_front"]["num_cols"]
    num_csi_pixels = 2
    num_tail_pixels = sensor_config["tail_counters"]["num_cols"] * sensor_config["tail_counters"]["num_rows"]
    num_hodo_pixels = num_hodo_pixels_per_layer * 2
    num_wls_pixels = num_wls_pixels_per_layer * 2
    num_pixels_per_layer = num_hodo_pixels + num_wls_pixels + num_csi_pixels + num_tail_pixels
    data_map = {}
    
    print(f"num_hodo_pixels_per_layer: {num_hodo_pixels_per_layer}")
    print(f"num_pixels_per_layer: {num_pixels_per_layer}")
    
    for layer in range(num_icc_layers):
        data_map[layer] = {}
        base = layer * num_pixels_per_layer
        hodo_offset1 = base
        hodo_offset2 = hodo_offset1 + num_hodo_pixels_per_layer
        wls_offset1 = hodo_offset2 + num_hodo_pixels_per_layer
        csi_offset = wls_offset1 + num_wls_pixels_per_layer
        wls_offset2 = csi_offset + num_csi_pixels
        tail_offset = wls_offset2 + num_wls_pixels_per_layer
        ending_offset = tail_offset + num_tail_pixels

        for rotated in range(2):
            data_map[layer][rotated] = {}
            if rotated == 0:
                mapping = generate_odd_even_list(num_hodo_pixels_per_layer, offset=hodo_offset1)
                data_map[layer][rotated]['hodo_front'] = mapping
                print(f"Non-rotated hodo_front mapping for layer {layer}: length={len(mapping)}, values={mapping[:10]}...")
            else:
                mapping = generate_creation_order(sensor_config["hodo_front"]["num_cols"], offset=hodo_offset2, top_first=False)
                data_map[layer][rotated]['hodo_front'] = mapping
                print(f"Rotated hodo_front mapping for layer {layer}: length={len(mapping)}, values={mapping[:10]}...")

    return data_map

def test_mapping_access():
    print("=== Testing mapping access ===")
    data_map = generateDataMap()
    
    num_cols = sensor_config["hodo_front"]["num_cols"]
    num_rows = sensor_config["hodo_front"]["num_rows"]
    
    print(f"Testing with num_cols={num_cols}, num_rows={num_rows}")
    
    for layer in range(1):  # Test first layer only
        for rotate in [False, True]:
            rotated_idx = 1 if rotate else 0
            mapping = data_map[layer][rotated_idx]['hodo_front']
            print(f"Layer {layer}, rotate={rotate}: mapping length={len(mapping)}")
            
            max_index_needed = (num_rows - 1) * num_cols + (num_cols - 1)
            print(f"Max index that will be accessed: {max_index_needed}")
            
            if max_index_needed >= len(mapping):
                print(f"ERROR: Will try to access index {max_index_needed} but mapping only has {len(mapping)} elements")
                return False
            else:
                print("✓ Mapping has sufficient elements")
    
    return True

if __name__ == "__main__":
    try:
        result = test_mapping_access()
        if result:
            print("\n✓ All mapping tests passed!")
        else:
            print("\n✗ Mapping tests failed!")
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()
