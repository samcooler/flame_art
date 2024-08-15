# This file contains math helper functions useful to many patterns, such as the directional vector
# for each nozzle on the star, and functions to help deal with them.

nozzle_vectors = [
    ( -0.0,         0.76942086,  1.2449492  ),
    ( -0.7317627,   0.23776406,  1.2449491  ),
    ( -0.45225424, -0.62247455,  1.2449491  ),
    (  0.45225424, -0.6224746,   1.2449491  ),
    (  0.7317627,   0.23776406,  1.2449491  ),
    ( -0.73176277,  1.007185,    0.769421   ),
    ( -1.184017,   -0.3847105,   0.76942086 ),
    ( -0.0,        -1.2449492,   0.76942086 ),
    (  1.1840171,  -0.3847105,   0.76942086 ),
    (  0.7317627,   1.007185,    0.7694209  ),
    ( -0.45225424,  1.3918955,  -0.0        ),
    ( -1.184017,    0.8602387,  -0.0        ),
    ( -1.4635255,   0.0,        -0.0        ),
    ( -1.184017,   -0.8602387,  -0.0        ),
    ( -0.45225424, -1.3918955,  -0.0        ),
    (  0.45225424, -1.3918954,  -0.0        ),
    (  1.184017,   -0.86023873, -0.0        ),
    (  1.4635255,   0.0,        -0.0        ),
    (  1.184017,    0.86023873, -0.0        ),
    (  0.45225424,  1.3918954,  -0.0        ),
    ( -0.0,         1.2449492,  -0.76942086 ),
    ( -1.184017,    0.38471046, -0.76942086 ),
    ( -0.73176277, -1.007185,   -0.769421   ),
    (  0.7317627,  -1.007185,   -0.7694209  ),
    (  1.184017,    0.38471046, -0.76942086 ),
    ( -0.45225424,  0.62247455, -1.2449491  ),
    ( -0.73176277, -0.23776406, -1.2449491  ),
    ( -0.0,        -0.76942086, -1.2449492  ),
    (  0.73176277, -0.23776412, -1.2449492  ),
    (  0.45225424,  0.6224746,  -1.2449491  ),
]

# Dot product impl, feel free to replace this with a library since I'm not familiar with what's out
# there in Python.
def dot(a: tuple[float, float, float], b: tuple[float, float, float]):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]

# Brute-force algorithm to find closest nozzle to a given vector, comparing direction using dot product.
# Note that you can either pass the full nozzle_vectors list to get the closest nozzle out of all of them, or a subset of the list if you want.
#
# Examples (using arrays from face_groupings):
#
# Get the closest nozzle out of all:
# closest_nozzle(v, all_nozzles)
#
# Get the closest nozzle out of the horizontal equator:
# closest_nozzle(v, equators[0])
#
# Get the closest nozzle out of the horizontal equator and the upper facing star:
# closest_nozzle(v, equators[0] + stars[5])
def closest_nozzle(vec: tuple[float, float, float], nozzles: list[int]) -> int:
    closest_nozzle_index = 0
    closest_nozzle_dot_product = dot(vec, nozzle_vectors[nozzles[0]])
    for i in range(1, len(nozzles)):
        d = dot(vec, nozzle_vectors[nozzles[i]])
        if d > closest_nozzle_dot_product:
            closest_nozzle_index = i
            closest_nozzle_dot_product = d
    return nozzles[closest_nozzle_index]
