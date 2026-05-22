import svgwrite
import math
from gcode import GCodeWriter

class VariableGeometryGenerator:
    def __init__(self, cols, rows, cell_size, min_margin, max_margin, bridge_size):
        self.cols = cols
        self.rows = rows
        self.cell_size = cell_size
        self.min_margin = min_margin
        self.max_margin = max_margin
        self.bridge_size = bridge_size
        
        self.canvas_width = cols * cell_size
        self.canvas_height = rows * cell_size
        self.stroke_style = {'stroke': 'white', 'stroke_width': 0.2, 'fill': 'none'}
        self.red_stroke_style = {'stroke': 'red', 'stroke_width': 0.2, 'fill': 'none'}
        self.green_stroke_style = {'stroke': '#00ff00', 'stroke_width': 0.2, 'fill': 'none'}
        
        self.current_dwg = None
        self.current_dwg_active = True
        self.current_gcodes = []

    def get_margin(self, row, col):
        if self.cols <= 1: return self.min_margin
        progress = col / (self.cols - 1)
        return self.min_margin + (self.max_margin - self.min_margin) * progress

    def get_tab_width(self, row, col):
        # Dynamically scale tab width based on margin to prevent intersections.
        # Multiplying by sqrt(2) ensures the tab's offset 'd' exactly equals the local margin.
        return self.get_margin(row, col) * math.sqrt(2)

    def create_drawing(self):
        padding = 50
        vw = self.canvas_width + padding * 2
        vh = self.canvas_height + padding * 2
        return svgwrite.Drawing(
            size=("100%", "100%"),
            viewBox=f"{-padding} {-padding} {vw} {vh}"
        )

    def draw_solid_line(self, p1, p2, style=None):
        if style is None: style = self.stroke_style
        if self.current_dwg and self.current_dwg_active:
            self.current_dwg.add(self.current_dwg.line(start=p1, end=p2, **style))
        for gc in self.current_gcodes:
            gc.add_line(p1, p2)
            
    def draw_polygon(self, points, style=None):
        if style is None: style = self.stroke_style
        if not points: return
        if self.current_dwg and self.current_dwg_active:
            self.current_dwg.add(self.current_dwg.polygon(points=points, **style))
        for gc in self.current_gcodes:
            gc.add_polygon(points)

    def has_xtab(self, r, c):
        return 0 <= r < self.rows and 0 <= c < self.cols

    def draw_square(self, x, y, size, is_large, row, col, style=None):
        if style is None: style = self.stroke_style
        corner_bridges = [
            self.has_xtab(row - 1, col - 1),  
            self.has_xtab(row - 1, col + 1),  
            self.has_xtab(row + 1, col + 1),  
            self.has_xtab(row + 1, col - 1)   
        ]
        
        corners = [(x, y), (x + size, y), (x + size, y + size), (x, y + size)]
        edge_on_perim = [row == 0, col == self.cols - 1, row == self.rows - 1, col == 0]
        
        for i in range(4):
            p1 = corners[i]
            p2 = corners[(i + 1) % 4]
            
            has_start_bridge = corner_bridges[i]
            has_end_bridge = corner_bridges[(i + 1) % 4]
            has_mid_bridge = is_large and not edge_on_perim[i]
            
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            length = math.hypot(dx, dy)
            if length < 1e-5: continue
            
            ux = dx / length
            uy = dy / length
            
            t_start = (self.bridge_size / 2.0) if has_start_bridge else 0.0
            t_end = length - ((self.bridge_size / 2.0) if has_end_bridge else 0.0)
            
            if t_start >= t_end: continue
                
            if has_mid_bridge:
                t_mid_left = (length / 2.0) - (self.bridge_size / 2.0)
                t_mid_right = (length / 2.0) + (self.bridge_size / 2.0)
                
                if t_start < t_mid_left:
                    self.draw_solid_line((p1[0] + ux * t_start, p1[1] + uy * t_start), 
                                         (p1[0] + ux * t_mid_left, p1[1] + uy * t_mid_left), style)
                if t_mid_right < t_end:
                    self.draw_solid_line((p1[0] + ux * t_mid_right, p1[1] + uy * t_mid_right), 
                                         (p1[0] + ux * t_end, p1[1] + uy * t_end), style)
            else:
                self.draw_solid_line((p1[0] + ux * t_start, p1[1] + uy * t_start), 
                                     (p1[0] + ux * t_end, p1[1] + uy * t_end), style)


class VariableTabbedGrid(VariableGeometryGenerator):
    def generate(self, show_base, show_top, show_red, show_grid, gcode_settings, generate_gcode=True):
        self.current_dwg = self.create_drawing()
        
        # 1. 10x10 Grid (Visual only, no GCode)
        if show_grid:
            self.current_dwg_active = True
            self.current_gcodes = []
            self._draw_10x10_grid()

        gcodes_out = {}

        # 2. Museum Board Base (White Layer)
        if generate_gcode:
            gc_base = GCodeWriter(**gcode_settings['museum'])
            gc_base.set_layer("Museum Board Base")
            self.current_gcodes = [gc_base]
        else:
            self.current_gcodes = []
        self.current_dwg_active = show_base
        self._draw_grid_layer(is_inverted=False, style=self.stroke_style)
        self._draw_boundary_gaps(is_inverted=False, style=self.stroke_style)
        if generate_gcode:
            gcodes_out['base'] = gc_base.get_gcode()

        # 3. Museum Board Top (Green Layer)
        if generate_gcode:
            gc_top = GCodeWriter(**gcode_settings['museum'])
            gc_top.set_layer("Museum Board Top")
            self.current_gcodes = [gc_top]
        else:
            self.current_gcodes = []
        self.current_dwg_active = show_top
        self._draw_grid_layer(is_inverted=True, style=self.green_stroke_style)
        self._draw_boundary_gaps(is_inverted=True, style=self.green_stroke_style)
        if generate_gcode:
            gcodes_out['top'] = gc_top.get_gcode()

        # 4. Shrinky Dink & Tape Sheets (Red Layer outputs to BOTH gc_shrinky and gc_tape simultaneously)
        if generate_gcode:
            gc_shrinky = GCodeWriter(**gcode_settings['shrinky'])
            gc_shrinky.set_layer("Shrinky Dink")
            gc_tape = GCodeWriter(**gcode_settings['tape'])
            gc_tape.set_layer("Tape Sheets")
            self.current_gcodes = [gc_shrinky, gc_tape]
        else:
            self.current_gcodes = []
        self.current_dwg_active = show_red
        self._draw_red_layer()
        if generate_gcode:
            gcodes_out['shrinky'] = gc_shrinky.get_gcode()
            gcodes_out['tape'] = gc_tape.get_gcode()

        # Finalize
        svg_str = self.current_dwg.tostring()
        self.current_dwg = None
        self.current_gcodes = []
        return svg_str, gcodes_out

    def _draw_10x10_grid(self):
        grid_style = {'stroke': '#444444', 'stroke_width': 0.1, 'fill': 'none', 'stroke-dasharray': '2,2'}
        for x in range(0, int(self.canvas_width) + 1, 10):
            self.current_dwg.add(self.current_dwg.line(start=(x, 0), end=(x, self.canvas_height), **grid_style))
        for y in range(0, int(self.canvas_height) + 1, 10):
            self.current_dwg.add(self.current_dwg.line(start=(0, y), end=(self.canvas_width, y), **grid_style))

    def _draw_grid_layer(self, is_inverted, style):
        for row in range(self.rows):
            for col in range(self.cols):
                x = col * self.cell_size
                y = row * self.cell_size
                
                m = self.get_margin(row, col)

                if row % 2 == 0 and col % 2 == 0:
                    is_large_square = (row // 2 + col // 2) % 2 == 0
                    if is_inverted: is_large_square = not is_large_square

                    if is_large_square:
                        self.draw_square(x, y, self.cell_size, True, row, col, style)
                    else:
                        size = self.cell_size - (2 * m)
                        self.draw_square(x + m, y + m, size, False, row, col, style)

                elif row % 2 == 0 and col % 2 != 0:
                    m_left = self.get_margin(row, col - 1)
                    m_right = self.get_margin(row, col + 1)
                    y1_L, y2_L = y + m_left, y + self.cell_size - m_left
                    y1_R, y2_R = y + m_right, y + self.cell_size - m_right

                    left_is_large = (row // 2 + (col - 1) // 2) % 2 == 0
                    if is_inverted: left_is_large = not left_is_large

                    if left_is_large:
                        end_x = x + self.cell_size - m_right
                        self.draw_solid_line((x, y1_L), (end_x, y1_R), style)
                        self.draw_solid_line((end_x, y1_R), (end_x, y2_R), style)
                        self.draw_solid_line((end_x, y2_R), (x, y2_L), style)
                    else:
                        start_x, end_x = x + m_left, x + self.cell_size
                        self.draw_solid_line((start_x, y1_L), (end_x, y1_R), style)
                        self.draw_solid_line((start_x, y1_L), (start_x, y2_L), style)
                        self.draw_solid_line((start_x, y2_L), (end_x, y2_R), style)

                elif row % 2 != 0 and col % 2 == 0:
                    m_top = self.get_margin(row - 1, col)
                    m_bottom = self.get_margin(row + 1, col)
                    x1_T, x2_T = x + m_top, x + self.cell_size - m_top
                    x1_B, x2_B = x + m_bottom, x + self.cell_size - m_bottom

                    top_is_large = ((row - 1) // 2 + col // 2) % 2 == 0
                    if is_inverted: top_is_large = not top_is_large

                    if top_is_large:
                        end_y = y + self.cell_size - m_bottom
                        self.draw_solid_line((x1_T, y), (x1_B, end_y), style)
                        self.draw_solid_line((x2_T, y), (x2_B, end_y), style)
                        self.draw_solid_line((x1_B, end_y), (x2_B, end_y), style)
                    else:
                        start_y, end_y = y + m_top, y + self.cell_size
                        self.draw_solid_line((x1_T, start_y), (x1_B, end_y), style)
                        self.draw_solid_line((x2_T, start_y), (x2_B, end_y), style)
                        self.draw_solid_line((x1_T, start_y), (x2_T, start_y), style)

                elif row % 2 != 0 and col % 2 != 0:
                    self._draw_x_tabs(x, y, row, col, is_inverted, style)

    def _draw_x_tabs(self, x, y, row, col, is_inverted, style):
        local_tab_width = self.get_tab_width(row, col)
        d = local_tab_width / math.sqrt(2)

        is_tl_large = ((row - 1) // 2 + (col - 1) // 2) % 2 == 0
        is_tr_large = ((row - 1) // 2 + (col + 1) // 2) % 2 == 0
        is_bl_large = ((row + 1) // 2 + (col - 1) // 2) % 2 == 0
        is_br_large = ((row + 1) // 2 + (col + 1) // 2) % 2 == 0

        if is_inverted:
            is_tl_large = not is_tl_large
            is_tr_large = not is_tr_large
            is_bl_large = not is_bl_large
            is_br_large = not is_br_large

        m_tl = self.get_margin(row - 1, col - 1)
        m_tr = self.get_margin(row - 1, col + 1)
        m_bl = self.get_margin(row + 1, col - 1)
        m_br = self.get_margin(row + 1, col + 1)

        tl_x = x if is_tl_large else x - m_tl
        tl_y = y if is_tl_large else y - m_tl

        tr_x = x + self.cell_size if is_tr_large else x + self.cell_size + m_tr
        tr_y = y if is_tr_large else y - m_tr

        bl_x = x if is_bl_large else x - m_bl
        bl_y = y + self.cell_size if is_bl_large else y + self.cell_size + m_bl

        br_x = x + self.cell_size if is_br_large else x + self.cell_size + m_br
        br_y = y + self.cell_size if is_br_large else y + self.cell_size + m_br

        cx = x + self.cell_size / 2
        cy = y + self.cell_size / 2

        self.draw_solid_line((tl_x, tl_y - d), (cx, cy - d), style)
        self.draw_solid_line((cx + d, cy), (br_x + d, br_y), style)
        self.draw_solid_line((tl_x - d, tl_y), (cx - d, cy), style)
        self.draw_solid_line((cx, cy + d), (br_x, br_y + d), style)

        self.draw_solid_line((bl_x - d, bl_y), (cx - d, cy), style)
        self.draw_solid_line((cx, cy - d), (tr_x, tr_y - d), style)
        self.draw_solid_line((bl_x, bl_y + d), (cx, cy + d), style)
        self.draw_solid_line((cx + d, cy), (tr_x + d, tr_y), style)

    def _draw_boundary_gaps(self, is_inverted, style):
        # Top boundary
        row, y = 0, 0
        for col in range(self.cols - 1):
            x, next_x = col * self.cell_size, (col + 1) * self.cell_size
            if col % 2 == 0:
                is_large = (row // 2 + col // 2) % 2 == 0
                if is_inverted: is_large = not is_large
                m = self.get_margin(row, col)
                TR = (x + self.cell_size, y) if is_large else (x + self.cell_size - m, y + m)
                
                m_left = self.get_margin(row, col)
                left_is_large = is_large
                TL_next = (next_x, y + m_left) if left_is_large else (next_x + m_left, y + m_left)
                self.draw_solid_line(TR, TL_next, style)
            else:
                m_right = self.get_margin(row, col + 1)
                right_is_large = (row // 2 + (col + 1) // 2) % 2 == 0
                if is_inverted: right_is_large = not right_is_large
                TR = (x + self.cell_size, y + m_right) if right_is_large else (x + self.cell_size - m_right, y + m_right)
                
                is_large_next = right_is_large
                TL_next = (next_x, y) if is_large_next else (next_x + m_right, y + m_right)
                self.draw_solid_line(TR, TL_next, style)

        # Bottom boundary
        row = self.rows - 1
        y_bottom = row * self.cell_size + self.cell_size
        for col in range(self.cols - 1):
            x, next_x = col * self.cell_size, (col + 1) * self.cell_size
            if col % 2 == 0:
                is_large = (row // 2 + col // 2) % 2 == 0
                if is_inverted: is_large = not is_large
                m = self.get_margin(row, col)
                BR = (x + self.cell_size, y_bottom) if is_large else (x + self.cell_size - m, y_bottom - m)
                
                m_left = self.get_margin(row, col)
                left_is_large = is_large
                BL_next = (next_x, y_bottom - m_left) if left_is_large else (next_x + m_left, y_bottom - m_left)
                self.draw_solid_line(BR, BL_next, style)
            else:
                m_right = self.get_margin(row, col + 1)
                right_is_large = (row // 2 + (col + 1) // 2) % 2 == 0
                if is_inverted: right_is_large = not right_is_large
                BR = (x + self.cell_size, y_bottom - m_right) if right_is_large else (x + self.cell_size - m_right, y_bottom - m_right)
                
                is_large_next = right_is_large
                BL_next = (next_x, y_bottom) if is_large_next else (next_x + m_right, y_bottom - m_right)
                self.draw_solid_line(BR, BL_next, style)

        # Left boundary
        col, x = 0, 0
        for row in range(self.rows - 1):
            y, next_y = row * self.cell_size, (row + 1) * self.cell_size
            if row % 2 == 0:
                is_large = (row // 2 + col // 2) % 2 == 0
                if is_inverted: is_large = not is_large
                m = self.get_margin(row, col)
                BL = (x, y + self.cell_size) if is_large else (x + m, y + self.cell_size - m)
                
                m_top = self.get_margin(row, col)
                top_is_large = is_large
                TL_next = (x + m_top, next_y) if top_is_large else (x + m_top, next_y + m_top)
                self.draw_solid_line(BL, TL_next, style)
            else:
                m_bottom = self.get_margin(row + 1, col)
                bottom_is_large = ((row + 1) // 2 + col // 2) % 2 == 0
                if is_inverted: bottom_is_large = not bottom_is_large
                BL = (x + m_bottom, y + self.cell_size) if bottom_is_large else (x + m_bottom, y + self.cell_size - m_bottom)
                
                is_large_next = bottom_is_large
                TL_next = (x, next_y) if is_large_next else (x + m_bottom, next_y + m_bottom)
                self.draw_solid_line(BL, TL_next, style)

        # Right boundary
        col = self.cols - 1
        x_right = col * self.cell_size + self.cell_size
        for row in range(self.rows - 1):
            y, next_y = row * self.cell_size, (row + 1) * self.cell_size
            if row % 2 == 0:
                is_large = (row // 2 + col // 2) % 2 == 0
                if is_inverted: is_large = not is_large
                m = self.get_margin(row, col)
                BR = (x_right, y + self.cell_size) if is_large else (x_right - m, y + self.cell_size - m)
                
                m_top = self.get_margin(row, col)
                top_is_large = is_large
                TR_next = (x_right - m_top, next_y) if top_is_large else (x_right - m_top, next_y + m_top)
                self.draw_solid_line(BR, TR_next, style)
            else:
                m_bottom = self.get_margin(row + 1, col)
                bottom_is_large = ((row + 1) // 2 + col // 2) % 2 == 0
                if is_inverted: bottom_is_large = not bottom_is_large
                BR = (x_right - m_bottom, y + self.cell_size) if bottom_is_large else (x_right - m_bottom, y + self.cell_size - m_bottom)
                
                is_large_next = bottom_is_large
                TR_next = (x_right, next_y) if is_large_next else (x_right - m_bottom, next_y + m_bottom)
                self.draw_solid_line(BR, TR_next, style)

    def _line_intersection(self, p1, p2, p3, p4):
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3
        x4, y4 = p4
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denom) < 1e-8: return (x1, y1)
        px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denom
        py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denom
        return (px, py)

    def _draw_red_layer(self):
        points = []
        # Top
        row, y = 0, 0
        for col in range(self.cols):
            x = col * self.cell_size
            if col % 2 == 0:
                m = self.get_margin(row, col)
                points.extend([(x + m, y + m), (x + self.cell_size - m, y + m)])
            else:
                m_left, m_right = self.get_margin(row, col - 1), self.get_margin(row, col + 1)
                points.extend([(x + m_left, y + m_left), (x + self.cell_size - m_right, y + m_right)])

        # Right
        col = self.cols - 1
        x_right = col * self.cell_size + self.cell_size
        for row in range(self.rows):
            y = row * self.cell_size
            if row % 2 == 0:
                m = self.get_margin(row, col)
                points.extend([(x_right - m, y + m), (x_right - m, y + self.cell_size - m)])
            else:
                m_top, m_bottom = self.get_margin(row - 1, col), self.get_margin(row + 1, col)
                points.extend([(x_right - m_top, y + m_top), (x_right - m_bottom, y + self.cell_size - m_bottom)])

        # Bottom
        row = self.rows - 1
        y_bottom = row * self.cell_size + self.cell_size
        for col in range(self.cols - 1, -1, -1):
            x = col * self.cell_size
            if col % 2 == 0:
                m = self.get_margin(row, col)
                points.extend([(x + self.cell_size - m, y_bottom - m), (x + m, y_bottom - m)])
            else:
                m_left, m_right = self.get_margin(row, col - 1), self.get_margin(row, col + 1)
                points.extend([(x + self.cell_size - m_right, y_bottom - m_right), (x + m_left, y_bottom - m_left)])

        # Left
        col, x = 0, 0
        for row in range(self.rows - 1, -1, -1):
            y = row * self.cell_size
            if row % 2 == 0:
                m = self.get_margin(row, col)
                points.extend([(x + m, y + self.cell_size - m), (x + m, y + m)])
            else:
                m_top, m_bottom = self.get_margin(row - 1, col), self.get_margin(row + 1, col)
                points.extend([(x + m_bottom, y + self.cell_size - m_bottom), (x + m_top, y + m_top)])

        self.draw_polygon(points, self.red_stroke_style)

        for row in range(self.rows):
            for col in range(self.cols):
                if row % 2 != 0 and col % 2 != 0:
                    self._draw_red_cutout(col * self.cell_size, row * self.cell_size, row, col)

    def _draw_red_cutout(self, x, y, row, col):
        is_tl_large = ((row - 1) // 2 + (col - 1) // 2) % 2 == 0
        is_tr_large = ((row - 1) // 2 + (col + 1) // 2) % 2 == 0
        is_bl_large = ((row + 1) // 2 + (col - 1) // 2) % 2 == 0
        is_br_large = ((row + 1) // 2 + (col + 1) // 2) % 2 == 0

        m_tl = self.get_margin(row - 1, col - 1)
        m_tr = self.get_margin(row - 1, col + 1)
        m_bl = self.get_margin(row + 1, col - 1)
        m_br = self.get_margin(row + 1, col + 1)

        P_T1 = (x, y - m_tl) if is_tl_large else (x + m_tl, y - m_tl)
        P_T2 = (x + self.cell_size - m_tr, y - m_tr) if is_tl_large else (x + self.cell_size, y - m_tr)
        
        P_B1 = (x, y + self.cell_size + m_bl) if is_bl_large else (x + m_bl, y + self.cell_size + m_bl)
        P_B2 = (x + self.cell_size - m_br, y + self.cell_size + m_br) if is_bl_large else (x + self.cell_size, y + self.cell_size + m_br)
        
        P_L1 = (x - m_tl, y) if is_tl_large else (x - m_tl, y + m_tl)
        P_L2 = (x - m_bl, y + self.cell_size - m_bl) if is_tl_large else (x - m_bl, y + self.cell_size)
        
        P_R1 = (x + self.cell_size + m_tr, y) if is_tr_large else (x + self.cell_size + m_tr, y + m_tr)
        P_R2 = (x + self.cell_size + m_br, y + self.cell_size - m_br) if is_tr_large else (x + self.cell_size + m_br, y + self.cell_size)

        v_tl = self._line_intersection(P_T1, P_T2, P_L1, P_L2)
        v_tr = self._line_intersection(P_T1, P_T2, P_R1, P_R2)
        v_bl = self._line_intersection(P_B1, P_B2, P_L1, P_L2)
        v_br = self._line_intersection(P_B1, P_B2, P_R1, P_R2)

        self.draw_polygon([v_tl, v_tr, v_br, v_bl], self.red_stroke_style)
