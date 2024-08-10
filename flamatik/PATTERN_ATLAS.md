# Pattern Atlas

This document intends to organize the patterns somewhat and provide some idea of the different types of patterns that we have. Format of this document will probably shift over time.

This document is not guaranteed to be exhaustive documentation of the patterns, it just serves to help with a mental model of "types" of patterns, which should hopefully be somewhat self-explanatory from the patterns' names.

## Basic patterns

- `start` - turns on solenoids and apertures and leaves them on

- `stop` - turns off everything, over and over. Good for safety.

- `poof` - solenoid pattern. Turn on and off a group (default size 1) of nozzels. `nozzle` , and `group` , and `delay` .

- `unpoof` - solenoid pattern. The opposite of poof - turns everything on, then turns off a `group` of `nozzles`

- `appoof` - aperture pattern. Uses the apertures to supply poofs just like the `poof` pattern - turns on and off a group, but using 0 to 1 in apertures.

- `group` - solenoid pattern. starting with `nozzle` turn on a group of `group` size for `delay` period, then keep walking through the nozzles

- `soliwave` - solinoid pattern. Using a width of `group`, walk through the nozzeles in order, adding and subtracting one every `delay`

- `multiwave` - aperture pattern. Applies a wave of certain width to a group, and walks through the sculpture linearly. May not support parameters yet?

- `pulse` - aperture pattern. Starts off, and turns the sculpture on over `delay` period, then all the way off (sawtooth pulse)

- `fast` - poofs all the faces, in index order

## Test patterns

- There are several patterns that start with "test" (e.g. "pattern_test_equators").
- These are mainly to test some util functions, and usually take the form of iterating across all combinations of the specified grouping.
- These may be artistically interesting, but since the order is always the same, they might not be as good as the `random` patterns.
- Examples:
  - Groupings (sets of multiple geometrically-determined sets of faces/nozzles):
    - `test_stars` poofs all 12 of the "stars" that exist on the triacontahedron, which are the sets of 5 faces that come together in a point, forming a 5-sided pyramid.
    - `test_halos` is similar to `test_stars` except it poofs the 12 "halos", which are rings of 5 faces adjacent to a star, kind of diagonal.
    - `test_equators` is similar to `test_stars` except it poofs the 6 "equators", which are rings of 10 faces that divide the triacontahedron into two "hemispheres".
    - `test_triples` is similar to `test_stars` except it poofs the 20 "triples", which are sets of 3 faces that come together in a point, forming a (very shallow) 3-sided pyramid. An interesting note is that since the 3-sided pyramids are so shallow, these 3 nozzles face almost the same direction, forming more of a "triple poof" in the sameish direction.
  - Index-based (relations of a given face):
    - `test_opposite` goes through the faces in index order and for each one, poofs both the face and the face facing the opposite direction.
    - `test_neighbors` goes through the faces in index order and for each one, poofs the 4 adjacent faces.
    - `test_orthogonals` is like `test_neighbors` but does the 4 faces that are at a right angle to each face.

## Random patterns

- There are several patterns that start with "random" which generally choose a random one of the specified shapes and activate it, either with a slow fade or a poof.
- These generally only do a single random one, so if you want it to repeat, do so using the command line (e.g. `-r 10` for 10 repetitions).
- Examples:
  - Fades:
    - `random_star_fade` does a slow fade-up then fade-down of a randomly-chosen star.
    - `random_star_with_opposites_fade` does a slow fade-up then fade-down of a randomly-chosen star, as well as the star facing the other way.
  - Poofs:
    - `random_star_poof` does a poof of a randomly-chosen star.
    - `random_star_with_opposites_poof` does a poof of a randomly-chosen star.

## Solenoid-friendly patterns

- In case the apertures (servo valves) aren't working, here are some patterns that don't rely on the apertures.
- Generally they just set all apertures to full open then do poofs with solenoids.
- List:
  - `comet`
  - `rings`
  - `random_equator_spin_poof`
  - `random_star_poof`
  - `random_star_with_opposites_poof`
  - `fast`
  - `test_opposite`
  - `test_halos`
  - `test_equators`
  - `test_stars`

## Misc/performance patterns

- `rings` - poofs all faces in rings from bottom to top, doing the ones on the same horizontal ring at the same time.
- `comet` - poofs a random slice of adjacent faces in order, from a randomly chosen equator
