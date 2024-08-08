

ring_to_idx = {
    'lower_star': [0, 1, 2, 3, 4],
    'lower_diagonal': [5, 6, 7, 8, 9],
    'middle_ring': [10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
    'upper_diagonal': [20, 21, 22, 23, 24],
    'upper_star': [25, 26, 27, 28, 29],
}

idx_to_ring = {}
for k in ring_to_idx:
    for i in ring_to_idx[k]:
        idx_to_ring[i] = k