import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from capture_ecran.recordbar import bar_position

SCREEN = (0, 0, 1920, 1080)
SIZE = (520, 54)


def overlaps(a, b):
    return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]


def test_above_the_zone_when_room():
    zone = (500, 400, 640, 360)
    x, y, outside = bar_position(zone, SIZE, SCREEN)
    assert outside and y + SIZE[1] <= zone[1] and not overlaps((x, y, *SIZE), zone)


def test_below_when_zone_touches_top():
    zone = (500, 0, 640, 360)
    x, y, outside = bar_position(zone, SIZE, SCREEN)
    assert outside and y >= zone[1] + zone[3]


def test_side_when_zone_spans_height():
    zone = (700, 0, 400, 1080)
    x, y, outside = bar_position(zone, SIZE, SCREEN)
    assert outside and not overlaps((x, y, *SIZE), zone)


def test_full_screen_has_no_free_room():
    x, y, outside = bar_position((0, 0, 1920, 1080), SIZE, SCREEN)
    assert not outside and 0 <= x <= 1920 - SIZE[0]


def test_secondary_screen_on_the_left():
    screen = (-1920, 0, 3840, 1080)
    x, y, outside = bar_position((-1800, 300, 500, 300), SIZE, screen)
    assert outside and x >= -1920

