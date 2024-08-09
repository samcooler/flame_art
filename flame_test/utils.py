

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

triples = [
    [0, 1, 5],
    [1, 2, 6],
    [2, 3, 7],
    [3, 4, 8],
    [4, 0, 9],

    [5, 10, 11],
    [6, 12, 13],
    [7, 14, 15],
    [8, 16, 17],
    [9, 18, 19],

    [20, 19, 10],
    [21, 11, 12],
    [22, 13, 14],
    [23, 15, 16],
    [24, 17, 18],

    [20, 25, 29],
    [21, 26, 25],
    [22, 27, 26],
    [23, 28, 27],
    [24, 29, 28],
]

# A set of neighboring faces for each face. E.g. the neighbors of face 9 are at index 9 in this array.
neighbors = [
    [4, 1, 9, 5],
    [0, 2, 5, 6],
    [1, 3, 6, 7],
    [2, 4, 7, 8],
    [3, 0, 8, 9],

    [0, 10, 1, 11],
    [1, 12, 2, 13],
    [2, 14, 3, 15],
    [3, 16, 4, 17],
    [4, 18, 0, 19],

    [19, 5, 20, 11],
    [5, 12, 10, 21],
    [11, 6, 21, 13],
    [6, 14, 12, 22],
    [13, 7, 22, 15],
    [7, 16, 14, 23],
    [15, 8, 23, 17],
    [8, 18, 16, 24],
    [17, 9, 24, 19],
    [9, 10, 18, 20],

    [19, 29, 10, 25],
    [11, 25, 12, 26],
    [13, 26, 14, 27],
    [15, 27, 16, 28],
    [17, 28, 18, 29],

    [20, 21, 29, 26],
    [21, 22, 25, 27],
    [22, 23, 26, 28],
    [23, 24, 27, 29],
    [24, 20, 28, 25],
]

# The reverse face from the index. E.g. the index of the opposite of face 9 is at index 9 in this array.
opposite = [
    27, 28, 29, 25, 26,
    23, 24, 20, 21, 22,
    15, 16, 17, 18, 19,
    10, 11, 12, 13, 14,
    7,  8,  9,  5,  6,
    3,  4,  0,  1,  2,
]

halos = [
    # adjacent to lower star
    [5, 6, 7, 8, 9],

    # adjacent to lower diagonal stars
    [4, 1, 11, 20, 18],
    [0, 2, 13, 21, 10],
    [1, 3, 15, 22, 12],
    [2, 4, 17, 23, 14],
    [3, 0, 19, 24, 16],

    # adjacent to upper diagonal stars
    [29, 26, 12, 5, 19],
    [25, 27, 14, 6, 11],
    [26, 28, 16, 7, 13],
    [27, 29, 18, 8, 15],
    [28, 25, 10, 9, 17],

    # adjacent to upper star
    [20, 21, 22, 23, 24],
]

equators = [
    # horizontal equator
    [10, 11, 12, 13, 14, 15, 16, 17, 18, 19],

    # five diagonal equators
    [3, 8, 17, 24, 29, 25, 21, 12, 6, 2],
    [4, 9, 19, 20, 25, 26, 22, 14, 7, 3],
    [0, 5, 11, 21, 26, 27, 23, 16, 8, 4],
    [1, 6, 13, 22, 27, 28, 24, 18, 9, 0],
    [2, 7, 15, 23, 28, 29, 20, 10, 5, 1],
]

ring_to_idx = {
    'lower_star': stars[0],
    'lower_diagonal': [5, 6, 7, 8, 9],
    'middle_ring': equators[0],
    'upper_diagonal': [20, 21, 22, 23, 24],
    'upper_star': stars[11],
}

idx_to_ring = {}
for k in ring_to_idx:
    for i in ring_to_idx[k]:
        idx_to_ring[i] = k
