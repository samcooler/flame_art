

stars = [
    # lower star
    [0, 1, 2, 3, 4],

    # lower diagonal stars
    [0, 5, 10, 19, 9],
    [1, 6, 12, 11, 5],
    [2, 7, 14, 13, 6],
    [3, 8, 16, 15, 7],
    [4, 9, 18, 17, 8],

    # upper diagonal stars
    [20, 25, 21, 11, 10],
    [26, 21, 12, 13, 22],
    [27, 22, 14, 15, 23],
    [28, 23, 16, 17, 24],
    [29, 24, 18, 19, 20],

    # upper star
    [25, 26, 27, 28, 29],
]

ring_to_idx = {
    'lower_star': stars[0],
    'lower_diagonal': [5, 6, 7, 8, 9],
    'middle_ring': [10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
    'upper_diagonal': [20, 21, 22, 23, 24],
    'upper_star': stars[11],
}

idx_to_ring = {}
for k in ring_to_idx:
    for i in ring_to_idx[k]:
        idx_to_ring[i] = k
