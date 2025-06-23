#!/usr/bin/env python3

import sys
import os

# Add current directory to path
sys.path.insert(0, '/home/zdhughes/ADAPT_software')

# Try importing without starting GUI
try:
    import ADAPT_MW
    print("✓ Successfully imported ADAPT_MW")
    
    # Test the key functions
    total_points = ADAPT_MW.calculate_total_data_points()
    print(f"✓ calculate_total_data_points() returned: {total_points}")
    
    width = ADAPT_MW.get_overall_width()
    print(f"✓ get_overall_width() returned: {width}")
    
    # Test data map generation
    data_map = ADAPT_MW.generateDataMap()
    print(f"✓ generateDataMap() completed successfully")
    
    # Test specific mapping that was causing the error
    layer = 0
    rotate = False
    mapping = data_map[layer][0 if not rotate else 1]['hodo_front']
    print(f"✓ hodo_front mapping for layer {layer} (rotate={rotate}): length={len(mapping)}")
    
    # Test the access pattern that was failing
    num_cols = ADAPT_MW.sensor_config["hodo_front"]["num_cols"]
    num_rows = ADAPT_MW.sensor_config["hodo_front"]["num_rows"]
    print(f"✓ num_cols={num_cols}, num_rows={num_rows}")
    
    max_index = (num_rows - 1) * num_cols + (num_cols - 1)
    print(f"✓ Max index that will be accessed: {max_index}")
    print(f"✓ Mapping length: {len(mapping)}")
    
    if max_index < len(mapping):
        print("✓ SUCCESS: Mapping has sufficient elements to avoid IndexError")
        
        # Test actual access
        for row in range(num_rows):
            for col in range(num_cols):
                idx = row * num_cols + col
                mapped_value = mapping[idx]
                # Only print first few for brevity
                if row == 0 and col < 3:
                    print(f"  row={row}, col={col} -> index={idx} -> mapped={mapped_value}")
        print("✓ All access tests passed!")
    else:
        print(f"✗ FAILURE: Mapping too short, would cause IndexError")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
