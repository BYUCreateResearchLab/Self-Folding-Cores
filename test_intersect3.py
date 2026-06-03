import sys
import os
sys.path.append('app')
from geometry import VariableTabbedGrid

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

def do_intersect(p1, p2, p3, p4):
    def ccw(A, B, C):
        return (C[1]-A[1]) * (B[0]-A[0]) - (B[1]-A[1]) * (C[0]-A[0])
    
    # strictly intersecting
    c1 = ccw(p1, p3, p4)
    c2 = ccw(p2, p3, p4)
    c3 = ccw(p1, p2, p3)
    c4 = ccw(p1, p2, p4)
    
    # Check if endpoints are shared
    eps = 1e-5
    if (abs(p1[0]-p3[0])<eps and abs(p1[1]-p3[1])<eps) or (abs(p1[0]-p4[0])<eps and abs(p1[1]-p4[1])<eps) or (abs(p2[0]-p3[0])<eps and abs(p2[1]-p3[1])<eps) or (abs(p2[0]-p4[0])<eps and abs(p2[1]-p4[1])<eps):
        return False
        
    if c1*c2 < -eps and c3*c4 < -eps:
        return True
    return False

gen2 = TestGrid2(4, 4, 15.0, 1.5, 0.5, 0.5)
gen2.generate(False, True, False, False, False)

for xl in gen2.xtab_lines:
    for rl in gen2.rect_lines:
        if do_intersect(xl[0], xl[1], rl[0], rl[1]):
            print(f"REAL INTERSECTION: Xtab {xl} Rect {rl}")
