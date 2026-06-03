import sys
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

    def _draw_x_tabs(self, x, y, row, col, is_inverted, style):
        self.in_xtab = True
        d_center = self.normal_gap

        is_tl_large = ((row - 1) // 2 + (col - 1) // 2) % 2 == 0
        is_tr_large = ((row - 1) // 2 + (col + 1) // 2) % 2 == 0
        is_bl_large = ((row + 1) // 2 + (col - 1) // 2) % 2 == 0
        is_br_large = ((row + 1) // 2 + (col + 1) // 2) % 2 == 0

        if is_inverted:
            is_tl_large = not is_tl_large
            is_tr_large = not is_tr_large
            is_bl_large = not is_bl_large
            is_br_large = not is_br_large

        m_tl_x, m_tl_y = self.get_margins(row - 1, col - 1, is_inverted)
        m_tr_x, m_tr_y = self.get_margins(row - 1, col + 1, is_inverted)
        m_bl_x, m_bl_y = self.get_margins(row + 1, col - 1, is_inverted)
        m_br_x, m_br_y = self.get_margins(row + 1, col + 1, is_inverted)

        tl_x = x if is_tl_large else x - m_tl_x
        tl_y = y if is_tl_large else y - m_tl_y

        tr_x = x + self.cell_size if is_tr_large else x + self.cell_size + m_tr_x
        tr_y = y if is_tr_large else y - m_tr_y

        bl_x = x if is_bl_large else x - m_bl_x
        bl_y = y + self.cell_size if is_bl_large else y + self.cell_size + m_bl_y

        br_x = x + self.cell_size if is_br_large else x + self.cell_size + m_br_x
        br_y = y + self.cell_size if is_br_large else y + self.cell_size + m_br_y

        cx = x + self.cell_size / 2
        cy = y + self.cell_size / 2

        # Note the swap of mx, my
        self.draw_solid_line((tl_x, tl_y - m_tl_y), (cx, cy - d_center), style)
        self.draw_solid_line((cx + d_center, cy), (br_x + m_br_x, br_y), style)
        self.draw_solid_line((tl_x - m_tl_x, tl_y), (cx - d_center, cy), style)
        self.draw_solid_line((cx, cy + d_center), (br_x, br_y + m_br_y), style)

        self.draw_solid_line((bl_x - m_bl_x, bl_y), (cx - d_center, cy), style)
        self.draw_solid_line((cx, cy - d_center), (tr_x, tr_y - m_tr_y), style)
        self.draw_solid_line((bl_x, bl_y + m_bl_y), (cx, cy + d_center), style)
        self.draw_solid_line((cx + d_center, cy), (tr_x + m_tr_x, tr_y), style)

        self.in_xtab = False

def do_intersect(p1, p2, p3, p4):
    def ccw(A, B, C):
        return (C[1]-A[1]) * (B[0]-A[0]) - (B[1]-A[1]) * (C[0]-A[0])
    c1 = ccw(p1, p3, p4)
    c2 = ccw(p2, p3, p4)
    c3 = ccw(p1, p2, p3)
    c4 = ccw(p1, p2, p4)
    eps = 1e-5
    if (abs(p1[0]-p3[0])<eps and abs(p1[1]-p3[1])<eps) or (abs(p1[0]-p4[0])<eps and abs(p1[1]-p4[1])<eps) or (abs(p2[0]-p3[0])<eps and abs(p2[1]-p3[1])<eps) or (abs(p2[0]-p4[0])<eps and abs(p2[1]-p4[1])<eps):
        return False
    if c1*c2 < -eps and c3*c4 < -eps:
        return True
    return False

gen2 = TestGrid2(4, 4, 15.0, 1.5, 0.5, 0.5)
gen2.generate(False, True, False, False, False)
cnt = 0
for xl in gen2.xtab_lines:
    for rl in gen2.rect_lines:
        if do_intersect(xl[0], xl[1], rl[0], rl[1]):
            cnt += 1
            print(f"INTERSECT: Xtab {xl} Rect {rl}")
print(cnt)
