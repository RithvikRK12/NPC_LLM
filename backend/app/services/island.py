"""Shared authored geography. Coordinates remain floats; only mask lookup uses cells."""
import json
import math
from pathlib import Path

RESOURCES = Path(__file__).resolve().parents[3] / 'frontend/godot/resources'
LAYOUT = json.loads((RESOURCES / 'island_layout.json').read_text())
BEACH = json.loads((RESOURCES / 'shipwreck_beach.json').read_text())
INTERIORS = json.loads((RESOURCES / 'building_interiors.json').read_text())
MAP_VERSION = LAYOUT['map_version']


def land_cell(x, y):
    x, y = x * 32 + 16, y * 32 + 16
    inside = False
    points = LAYOUT['outline']
    for a, b in zip(points, points[1:] + points[:1]):
        # Godot includes points on polygon edges. Match that closed-set rule
        # exactly for cell centers on diagonal coast segments.
        cross = (x-a[0])*(b[1]-a[1]) - (y-a[1])*(b[0]-a[0])
        if cross == 0 and min(a[0], b[0]) <= x <= max(a[0], b[0]) and min(a[1], b[1]) <= y <= max(a[1], b[1]):
            return True
        if (a[1] > y) != (b[1] > y) and x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:
            inside = not inside
    return inside


def exterior_walkable(x, y):
    return all(land_cell(math.floor(xx/32), math.floor(yy/32))
               for xx in (x-12, x+11.999) for yy in (y-8, y+7.999))


def recover(position):
    x, y = position.get('x', 0), position.get('y', 0)
    for room in INTERIORS.values():
        ox, oy = room['origin']
        if ox-512 <= x < ox+512 and oy-384 <= y < oy+384:
            return position  # Local room/scenery recovery stays with WorldLayout.
    if exterior_walkable(x, y):
        return position
    _, at = min(LAYOUT['recovery_markers'].items(),
                key=lambda entry: ((entry[1][0]-x)**2+(entry[1][1]-y)**2, entry[0]))
    return {'x': float(at[0]), 'y': float(at[1])}


def location_at(position):
    """Keep saved conversation context aligned with the authored geographic position."""
    x, y = position['x'], position['y']
    for room_id, room in INTERIORS.items():
        ox, oy = room['origin']
        if ox-512 <= x < ox+512 and oy-384 <= y < oy+384:
            return room_id
    if abs(x) < 1600 and y > BEACH['markers']['InlandRoute'][1]-320:
        return 'shipwreck_beach'
    if x < -340:
        return 'forest_edge'
    if -1408 <= x < 1408 and -1120 <= y < 1120:
        return 'village_square'
    return 'island'
