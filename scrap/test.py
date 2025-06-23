def generate_creation_order(num_pixels_per_row, offset=0, top_first=False):
    """
    Returns pixel indices in top-row-first-then-bottom order,
    assuming 'pixel number' order is bottom0, top0, bottom1, top1, etc.
    """
    row1 = list(range(offset, offset + num_pixels_per_row))
    row2 = list(range(offset + num_pixels_per_row, offset + 2 * num_pixels_per_row))
    if top_first:
        return [val for pair in zip(row1, row2) for val in pair]
    else:
        return [val for pair in zip(row2, row1) for val in pair]

num_icc_layers = 4
num_hodo_pixels_per_layer = 14 * 2
num_wls_pixels_per_layer = 20
num_csi_pixels = 2
num_tail_pixels = 6
num_hodo_pixels = num_hodo_pixels_per_layer * 2
num_wls_pixels = num_wls_pixels_per_layer * 2
num_pixels_per_layer = num_hodo_pixels + num_wls_pixels + num_csi_pixels + num_tail_pixels
data_map = {}
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
    print(hodo_offset1, hodo_offset2, wls_offset1, csi_offset, wls_offset2, tail_offset)

    for rotated in range(2): #0 = not rotated, 1 = rotated
        data_map[layer][rotated] = {}
        if rotated == 0:
            data_map[layer][rotated]['hodo_front'] = generate_creation_order(14, offset=hodo_offset1, top_first=False)
            data_map[layer][rotated]['hodo_side'] = generate_creation_order(14, offset=hodo_offset2, top_first=True)[-2:] # TODO: check if flipped and correct
            data_map[layer][rotated]['wls_side'] = list(range(wls_offset1, csi_offset))[-1]
            data_map[layer][rotated]['csi'] = [list(range(csi_offset, wls_offset2))[0]] # list of two and select first for non-rotated orientation
            data_map[layer][rotated]['wls_front'] = [list(range(wls_offset2, tail_offset))]
            data_map[layer][rotated]['tail'] = list(range(tail_offset, ending_offset))
        else:
            data_map[layer][rotated]['hodo_side'] = generate_creation_order(14, offset=hodo_offset1, top_first=True)[:2] # TODO: check if flipped and correct
            data_map[layer][rotated]['hodo_front'] = generate_creation_order(14, offset=hodo_offset2, top_first=False)
            data_map[layer][rotated]['wls_front'] = list(range(wls_offset1, csi_offset))
            data_map[layer][rotated]['csi'] = [list(range(csi_offset, wls_offset2))[1]] # list of two and select second for rotated orientation
            data_map[layer][rotated]['wls_side'] = [list(range(wls_offset2, tail_offset))[0]]
            data_map[layer][rotated]['tail'] = list(range(tail_offset, ending_offset))
data_map[0][0]
data_map[0][1]

def analyze_data_map(data_map):
    """
    Analyze the data_map to find the maximum value and check if all numbers
    between 0 and the maximum value appear at least once.
    """
    all_values = []

    # Recursive function to collect all values from the nested dictionary
    def collect_values(d):
        for key, value in d.items():
            if isinstance(value, dict):
                collect_values(value)
            elif isinstance(value, list):
                all_values.extend(value)
            elif isinstance(value, int):
                all_values.append(value)

    # Collect all values from the data_map
    collect_values(data_map)

    # Find the maximum value
    max_value = max(all_values)

    # Check if all numbers between 0 and max_value appear at least once
    missing_values = set(range(max_value + 1)) - set(all_values)

    return max_value, missing_values

# Example usage
max_value, missing_values = analyze_data_map(data_map)
print("Maximum value:", max_value)
if missing_values:
    print("Missing values:", sorted(missing_values))
else:
    print("All numbers between 0 and", max_value, "are present.")


# Example usage
num_pixels_per_row = 14

# Get the pixel number indices in creation order
pixel_number_indices = generate_creation_order(num_pixels_per_row, top_first=False, offset=100)[-2:]
print("Pixel number indices in creation order:", pixel_number_indices)