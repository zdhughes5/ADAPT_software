#!/usr/bin/env python3

import json

# Load sensor geometry config.
with open("sensor_config.json", "r") as f:
    sensor_config = json.load(f)

print(f"Config loaded: hodo_front has {sensor_config['hodo_front']['num_cols']} cols")

def generate_odd_even_list(length, offset=0, even_first=False):
    numbers = list(range(offset, offset + length))
    odd_values = [n for n in numbers if n % 2 != 0]
    even_values = [n for n in numbers if n % 2 == 0]
    if even_first:
        return even_values + odd_values
    else:
        return odd_values + even_values

# Calculate what the mapping should be
num_hodo_pixels_per_layer = sensor_config["hodo_front"]["num_cols"] * sensor_config["hodo_front"]["num_rows"]
print(f"num_hodo_pixels_per_layer: {num_hodo_pixels_per_layer}")

# Generate the mapping
mapping = generate_odd_even_list(num_hodo_pixels_per_layer, offset=0)
print(f"Mapping length: {len(mapping)}")
print(f"Mapping: {mapping}")

# Test accessing the mapping
num_cols = sensor_config["hodo_front"]["num_cols"]
num_rows = sensor_config["hodo_front"]["num_rows"]

print(f"\nTesting access pattern:")
print(f"num_cols: {num_cols}, num_rows: {num_rows}")

max_index = 0
for row in range(num_rows):
    for col in range(num_cols):
        index = row * num_cols + col
        max_index = max(max_index, index)
        try:
            mapped_value = mapping[index]
            print(f"  row={row}, col={col} -> index={index} -> mapping[{index}]={mapped_value}")
        except IndexError as e:
            print(f"  ERROR: row={row}, col={col} -> index={index} -> IndexError: {e}")
            break

print(f"\nMax index accessed: {max_index}")
print(f"Mapping length: {len(mapping)}")
print(f"Should work: {max_index < len(mapping)}")
