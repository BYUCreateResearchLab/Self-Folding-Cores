import sys
import os
sys.path.append('app')
from geometry import VariableTabbedGrid
import math

class TestGrid(VariableTabbedGrid):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lines = []

    def draw_solid_line(self, p1, p2, style=None):
        self.lines.append((p1, p2, style))

def intersect(l1, l2):
    p1, p2 = l1[0], l1[1]
    p3, p4 = l2[0], l2[1]
    # check line segment intersection
    def ccw(A, B, C):
        return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])
    
    # check if strictly intersecting
    if ccw(p1,p3,p4) != ccw(p2,p3,p4) and ccw(p1,p2,p3) != ccw(p1,p2,p4):
        return True
    return False

generator = TestGrid(4, 4, 15.0, 1.5, 0.5, 0.5)
# just get the lines for top layer
generator.generate(False, True, False, False, False)

xtab_lines = [l for l in generator.lines if l[2] == generator.green_stroke_style]
# Actually, all lines are green stroke style in top layer.
# Let's filter by checking if they are xtab lines.
# xtab lines are drawn in _draw_x_tabs. We can just intercept _draw_x_tabs
class TestGrid2(VariableTabbedGrid):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.xtab_lines = []
        self.rect_lines = []
        self.in_xtab = False

    def draw_solid_line(self, p1, p2, style=None):
        if self.in_xtab:
            self.xtab_lines.append((p1, p2))
        else:
            self.rect_lines.append((p1, p2))

    def _draw_x_tabs(self, *args, **kwargs):
        self.in_xtab = True
        super()._draw_x_tabs(*args, **kwargs)
        self.in_xtab = False

gen2 = TestGrid2(4, 4, 15.0, 1.5, 0.5, 0.5)
gen2.generate(False, True, False, False, False)

intersections = []
for xl in gen2.xtab_lines:
    for rl in gen2.rect_lines:
        if intersect(xl, rl):
            intersections.append((xl, rl))

if intersections:
    print(f"Found {len(intersections)} intersections!")
    for xl, rl in intersections:
        print(f"Xtab line {xl} intersects Rect line {rl}")
else:
    print("No intersections found.")
