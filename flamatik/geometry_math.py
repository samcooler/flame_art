# This file contains math helper functions useful to many patterns, such as the directional vector
# for each nozzle on the star, and functions to help deal with them.

nozzle_vectors = [
    (0.0, -1.2449492, 0.76942086),
    (0.7317627, -1.2449491, 0.23776406),
    (0.45225424, -1.2449491, -0.62247455),
    (-0.45225424, -1.2449491, -0.6224746),
    (-0.7317627, -1.2449491, 0.23776406),
    (0.73176277, -0.769421, 1.007185),
    (1.184017, -0.76942086, -0.3847105),
    (0.0, -0.76942086, -1.2449492),
    (-1.1840171, -0.76942086, -0.3847105),
    (-0.7317627, -0.7694209, 1.007185),
    (0.45225424, 0.0, 1.3918955),
    (1.184017, 0.0, 0.8602387),
    (1.4635255, 0.0, 0.0),
    (1.184017, 0.0, -0.8602387),
    (0.45225424, 0.0, -1.3918955),
    (-0.45225424, 0.0, -1.3918954),
    (-1.184017, 0.0, -0.86023873),
    (-1.4635255, 0.0, 0.0),
    (-1.184017, 0.0, 0.86023873),
    (-0.45225424, 0.0, 1.3918954),
    (0.0, 0.76942086, 1.2449492),
    (1.184017, 0.76942086, 0.38471046),
    (0.73176277, 0.769421, -1.007185),
    (-0.7317627, 0.7694209, -1.007185),
    (-1.184017, 0.76942086, 0.38471046),
    (0.45225424, 1.2449491, 0.62247455),
    (0.73176277, 1.2449491, -0.23776406),
    (0.0, 1.2449492, -0.76942086),
    (-0.73176277, 1.2449492, -0.23776412),
    (-0.45225424, 1.2449491, 0.6224746),
]

# Dot product impl, feel free to replace this with a library since I'm not familiar with what's out
# there in Python.
def dot(a: tuple[float, float, float], b: tuple[float, float, float]):
    a[0] * b[0] + a[1] * b[1] + a[2] * b[2]

# Brute-force algorithm to find closest nozzle to a given vector, comparing direction using dot product.
# Note that you can either pass the full nozzle_vectors list to get the closest nozzle out of all of them, or a subset of the list if you want.
#
# Examples:
#
# Get the closest nozzle out of all:
# closest_nozzle(v, nozzle_vectors)
#
# Get the closest nozzle out of the horizontal equator:
# closest_nozzle(v, map(lambda i:nozzle_vectors[i], equators[0]))
#
# Get the closest nozzle out of the horizontal equator and the upper facing star:
# closest_nozzle(v, map(lambda i:nozzle_vectors[i], equators[0] + stars[5]))
def closest_nozzle(vec: tuple[float, float, float], nozzles: list[tuple[float, float, float]]) -> int:
    closest_nozzle_index = 0
    closest_nozzle_dot_product = dot(vec, nozzles[0])
    for i in range(1, len(nozzles)):
        d = dot(vec,  nozzles[i])
        if d > closest_nozzle_dot_product:
            closest_nozzle_index = i
            closest_nozzle_dot_product = d
    return closest_nozzle_index
