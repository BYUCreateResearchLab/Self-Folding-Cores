import svgwrite
import math

class VariableGeometryGenerator:
    def __init__(self, cols, rows, cell_size, normal_gap, alt_gap, bridge_size):
        self.cols = cols
        self.rows = rows
        self.cell_size = cell_size
        self.normal_gap = normal_gap
        self.alt_gap = alt_gap
        self.bridge_size = bridge_size
        
        self.canvas_width = cols * cell_size
        self.canvas_height = rows * cell_size
        self.stroke_style = {'stroke': 'black', 'stroke_width': 0.2, 'fill': 'none'}
        self.red_stroke_style = {'stroke': 'red', 'stroke_width': 0.2, 'fill': 'none'}
        self.green_stroke_style = {'stroke': '#00ff00', 'stroke_width': 0.2, 'fill': 'none'}
        self.sheet_style = {'stroke': 'blue', 'stroke_width': 0.4, 'fill': 'none'}
        
        self.offset_x = 0
        self.offset_y = 0
        self.current_dwg = None

    def get_margins(self, row, col, is_inverted=False, is_red_layer=False):
        if is_red_layer:
            return self.normal_gap, self.normal_gap
        if not is_inverted:
            return self.normal_gap, self.normal_gap
            
        # For x-tabs (odd row and odd col), maintain the normal gap width
        if row % 2 != 0 and col % 2 != 0:
            return self.normal_gap, self.normal_gap
            
        is_large_square = (row // 2 + col // 2) % 2 == 0
        if is_inverted:
            is_large_square = not is_large_square
            
        if not is_large_square:
            return self.alt_gap, self.normal_gap
        else:
            return self.normal_gap, self.normal_gap

    def create_drawing(self, show_sheet=False, sheet_w=279, sheet_h=216):
        padding = 50
        if show_sheet:
            vw = sheet_w + padding * 2
            vh = sheet_h + padding * 2
            # Set the viewbox to center around the sheet
            vx = -padding
            vy = -padding
        else:
            vw = self.canvas_width + padding * 2
            vh = self.canvas_height + padding * 2
            vx = -padding
            vy = -padding
            
        return svgwrite.Drawing(
            size=("100%", "100%"),
            viewBox=f"{vx} {vy} {vw} {vh}"
        )

    def _translate_point(self, point):
        return (point[0] + self.offset_x, point[1] + self.offset_y)

    def _translate_points(self, points):
        return [self._translate_point(point) for point in points]

    def draw_solid_line(self, p1, p2, style=None):
        if style is None: style = self.stroke_style
        if self.current_dwg:
            self.current_dwg.add(self.current_dwg.line(start=self._translate_point(p1), end=self._translate_point(p2), **style))
            
    def draw_polygon(self, points, style=None):
        if style is None: style = self.stroke_style
        if not points: return
        if self.current_dwg:
            self.current_dwg.add(self.current_dwg.polygon(points=self._translate_points(points), **style))

    def has_xtab(self, r, c):
        return 0 <= r < self.rows and 0 <= c < self.cols

    def draw_rectangle(self, x, y, w, h, is_large, row, col, style=None):
        if style is None: style = self.stroke_style
        corner_bridges = [
            self.has_xtab(row - 1, col - 1),  
            self.has_xtab(row - 1, col + 1),  
            self.has_xtab(row + 1, col + 1),  
            self.has_xtab(row + 1, col - 1)   
        ]
        
        corners = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
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
    def generate(self, show_base, show_top, show_red, show_grid, show_sheet=False):
        sheet_w, sheet_h = 279, 216
        if show_sheet:
            self.offset_x = (sheet_w - self.canvas_width) / 2.0
            self.offset_y = (sheet_h - self.canvas_height) / 2.0
        else:
            self.offset_x = 0
            self.offset_y = 0

        self.current_dwg = self.create_drawing(show_sheet, sheet_w, sheet_h)

        if show_sheet:
            # Draw the sheet boundary (already translated internally if we used draw_rectangle, 
            # but we can just use dwg.rect directly since it's the bounding box)
            self.current_dwg.add(
                self.current_dwg.rect(
                    insert=(0, 0),
                    size=(sheet_w, sheet_h),
                    **self.sheet_style
                )
            )
        
        # 1. 10x10 Grid (Visual only)
        if show_grid:
            self._draw_10x10_grid()

        # 2. Museum Board Base (White Layer)
        if show_base:
            self._draw_grid_layer(is_inverted=False, style=self.stroke_style)
            self._draw_boundary_gaps(is_inverted=False, style=self.stroke_style)

        # 3. Museum Board Top (Green Layer)
        if show_top:
            self._draw_grid_layer(is_inverted=True, style=self.green_stroke_style)
            self._draw_boundary_gaps(is_inverted=True, style=self.green_stroke_style)

        # 4. Shrinky Dink & Tape Sheets (Red Layer)
        if show_red:
            self._draw_red_layer()

        # Finalize
        svg_str = self.current_dwg.tostring()
        self.current_dwg = None
        return svg_str

    def _draw_10x10_grid(self):
        grid_style = {'stroke': '#444444', 'stroke_width': 0.1, 'fill': 'none', 'stroke-dasharray': '2,2'}
        for x in range(0, int(self.canvas_width) + 1, 10):
            self.current_dwg.add(
                self.current_dwg.line(
                    start=self._translate_point((x, 0)),
                    end=self._translate_point((x, self.canvas_height)),
                    **grid_style
                )
            )
        for y in range(0, int(self.canvas_height) + 1, 10):
            self.current_dwg.add(
                self.current_dwg.line(
                    start=self._translate_point((0, y)),
                    end=self._translate_point((self.canvas_width, y)),
                    **grid_style
                )
            )

    def _draw_grid_layer(self, is_inverted, style):
        for row in range(self.rows):
            for col in range(self.cols):
                x = col * self.cell_size
                y = row * self.cell_size
                
                mx, my = self.get_margins(row, col, is_inverted)

                if row % 2 == 0 and col % 2 == 0:
                    is_large_square = (row // 2 + col // 2) % 2 == 0
                    if is_inverted: is_large_square = not is_large_square

                    if is_large_square:
                        self.draw_rectangle(x, y, self.cell_size, self.cell_size, True, row, col, style)
                    else:
                        w = self.cell_size - (2 * mx)
                        h = self.cell_size - (2 * my)
                        self.draw_rectangle(x + mx, y + my, w, h, False, row, col, style)

                elif row % 2 == 0 and col % 2 != 0:
                    m_left_x, m_left_y = self.get_margins(row, col - 1, is_inverted)
                    m_right_x, m_right_y = self.get_margins(row, col + 1, is_inverted)
                    y1_L, y2_L = y + m_left_y, y + self.cell_size - m_left_y
                    y1_R, y2_R = y + m_right_y, y + self.cell_size - m_right_y

                    left_is_large = (row // 2 + (col - 1) // 2) % 2 == 0
                    if is_inverted: left_is_large = not left_is_large

                    if left_is_large:
                        end_x = x + self.cell_size - m_right_x
                        self.draw_solid_line((x, y1_L), (end_x, y1_R), style)
                        self.draw_solid_line((end_x, y1_R), (end_x, y2_R), style)
                        self.draw_solid_line((end_x, y2_R), (x, y2_L), style)
                    else:
                        start_x, end_x = x + m_left_x, x + self.cell_size
                        self.draw_solid_line((start_x, y1_L), (end_x, y1_R), style)
                        self.draw_solid_line((start_x, y1_L), (start_x, y2_L), style)
                        self.draw_solid_line((start_x, y2_L), (end_x, y2_R), style)

                elif row % 2 != 0 and col % 2 == 0:
                    m_top_x, m_top_y = self.get_margins(row - 1, col, is_inverted)
                    m_bottom_x, m_bottom_y = self.get_margins(row + 1, col, is_inverted)
                    x1_T, x2_T = x + m_top_x, x + self.cell_size - m_top_x
                    x1_B, x2_B = x + m_bottom_x, x + self.cell_size - m_bottom_x

                    top_is_large = ((row - 1) // 2 + col // 2) % 2 == 0
                    if is_inverted: top_is_large = not top_is_large

                    if top_is_large:
                        end_y = y + self.cell_size - m_bottom_y
                        self.draw_solid_line((x1_T, y), (x1_B, end_y), style)
                        self.draw_solid_line((x2_T, y), (x2_B, end_y), style)
                        self.draw_solid_line((x1_B, end_y), (x2_B, end_y), style)
                    else:
                        start_y, end_y = y + m_top_y, y + self.cell_size
                        self.draw_solid_line((x1_T, start_y), (x1_B, end_y), style)
                        self.draw_solid_line((x2_T, start_y), (x2_B, end_y), style)
                        self.draw_solid_line((x1_T, start_y), (x2_T, start_y), style)

                elif row % 2 != 0 and col % 2 != 0:
                    self._draw_x_tabs(x, y, row, col, is_inverted, style)

    def _draw_x_tabs(self, x, y, row, col, is_inverted, style):
        d = self.normal_gap

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
                mx, my = self.get_margins(row, col, is_inverted)
                TR = (x + self.cell_size, y) if is_large else (x + self.cell_size - mx, y + my)
                
                left_is_large = is_large
                TL_next = (next_x, y + my) if left_is_large else (next_x + mx, y + my)
                self.draw_solid_line(TR, TL_next, style)
            else:
                mx, my = self.get_margins(row, col + 1, is_inverted)
                right_is_large = (row // 2 + (col + 1) // 2) % 2 == 0
                if is_inverted: right_is_large = not right_is_large
                TR = (x + self.cell_size, y + my) if right_is_large else (x + self.cell_size - mx, y + my)
                
                is_large_next = right_is_large
                TL_next = (next_x, y) if is_large_next else (next_x + mx, y + my)
                self.draw_solid_line(TR, TL_next, style)

        # Bottom boundary
        row = self.rows - 1
        y_bottom = row * self.cell_size + self.cell_size
        for col in range(self.cols - 1):
            x, next_x = col * self.cell_size, (col + 1) * self.cell_size
            if col % 2 == 0:
                is_large = (row // 2 + col // 2) % 2 == 0
                if is_inverted: is_large = not is_large
                mx, my = self.get_margins(row, col, is_inverted)
                BR = (x + self.cell_size, y_bottom) if is_large else (x + self.cell_size - mx, y_bottom - my)
                
                left_is_large = is_large
                BL_next = (next_x, y_bottom - my) if left_is_large else (next_x + mx, y_bottom - my)
                self.draw_solid_line(BR, BL_next, style)
            else:
                mx, my = self.get_margins(row, col + 1, is_inverted)
                right_is_large = (row // 2 + (col + 1) // 2) % 2 == 0
                if is_inverted: right_is_large = not right_is_large
                BR = (x + self.cell_size, y_bottom - my) if right_is_large else (x + self.cell_size - mx, y_bottom - my)
                
                is_large_next = right_is_large
                BL_next = (next_x, y_bottom) if is_large_next else (next_x + mx, y_bottom - my)
                self.draw_solid_line(BR, BL_next, style)

        # Left boundary
        col, x = 0, 0
        for row in range(self.rows - 1):
            y, next_y = row * self.cell_size, (row + 1) * self.cell_size
            if row % 2 == 0:
                is_large = (row // 2 + col // 2) % 2 == 0
                if is_inverted: is_large = not is_large
                mx, my = self.get_margins(row, col, is_inverted)
                BL = (x, y + self.cell_size) if is_large else (x + mx, y + self.cell_size - my)
                
                top_is_large = is_large
                TL_next = (x + mx, next_y) if top_is_large else (x + mx, next_y + my)
                self.draw_solid_line(BL, TL_next, style)
            else:
                mx, my = self.get_margins(row + 1, col, is_inverted)
                bottom_is_large = ((row + 1) // 2 + col // 2) % 2 == 0
                if is_inverted: bottom_is_large = not bottom_is_large
                BL = (x + mx, y + self.cell_size) if bottom_is_large else (x + mx, y + self.cell_size - my)
                
                is_large_next = bottom_is_large
                TL_next = (x, next_y) if is_large_next else (x + mx, next_y + my)
                self.draw_solid_line(BL, TL_next, style)

        # Right boundary
        col = self.cols - 1
        x_right = col * self.cell_size + self.cell_size
        for row in range(self.rows - 1):
            y, next_y = row * self.cell_size, (row + 1) * self.cell_size
            if row % 2 == 0:
                is_large = (row // 2 + col // 2) % 2 == 0
                if is_inverted: is_large = not is_large
                mx, my = self.get_margins(row, col, is_inverted)
                BR = (x_right, y + self.cell_size) if is_large else (x_right - mx, y + self.cell_size - my)
                
                top_is_large = is_large
                TR_next = (x_right - mx, next_y) if top_is_large else (x_right - mx, next_y + my)
                self.draw_solid_line(BR, TR_next, style)
            else:
                mx, my = self.get_margins(row + 1, col, is_inverted)
                bottom_is_large = ((row + 1) // 2 + col // 2) % 2 == 0
                if is_inverted: bottom_is_large = not bottom_is_large
                BR = (x_right - mx, y + self.cell_size) if bottom_is_large else (x_right - mx, y + self.cell_size - my)
                
                is_large_next = bottom_is_large
                TR_next = (x_right, next_y) if is_large_next else (x_right - mx, next_y + my)
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
        is_red_layer = True
        # Top
        row, y = 0, 0
        for col in range(self.cols):
            x = col * self.cell_size
            if col % 2 == 0:
                mx, my = self.get_margins(row, col, is_red_layer=is_red_layer)
                points.extend([(x + mx, y + my), (x + self.cell_size - mx, y + my)])
            else:
                m_left_x, m_left_y = self.get_margins(row, col - 1, is_red_layer=is_red_layer)
                m_right_x, m_right_y = self.get_margins(row, col + 1, is_red_layer=is_red_layer)
                points.extend([(x + m_left_x, y + m_left_y), (x + self.cell_size - m_right_x, y + m_right_y)])

        # Right
        col = self.cols - 1
        x_right = col * self.cell_size + self.cell_size
        for row in range(self.rows):
            y = row * self.cell_size
            if row % 2 == 0:
                mx, my = self.get_margins(row, col, is_red_layer=is_red_layer)
                points.extend([(x_right - mx, y + my), (x_right - mx, y + self.cell_size - my)])
            else:
                m_top_x, m_top_y = self.get_margins(row - 1, col, is_red_layer=is_red_layer)
                m_bottom_x, m_bottom_y = self.get_margins(row + 1, col, is_red_layer=is_red_layer)
                points.extend([(x_right - m_top_x, y + m_top_y), (x_right - m_bottom_x, y + self.cell_size - m_bottom_y)])

        # Bottom
        row = self.rows - 1
        y_bottom = row * self.cell_size + self.cell_size
        for col in range(self.cols - 1, -1, -1):
            x = col * self.cell_size
            if col % 2 == 0:
                mx, my = self.get_margins(row, col, is_red_layer=is_red_layer)
                points.extend([(x + self.cell_size - mx, y_bottom - my), (x + mx, y_bottom - my)])
            else:
                m_left_x, m_left_y = self.get_margins(row, col - 1, is_red_layer=is_red_layer)
                m_right_x, m_right_y = self.get_margins(row, col + 1, is_red_layer=is_red_layer)
                points.extend([(x + self.cell_size - m_right_x, y_bottom - m_right_y), (x + m_left_x, y_bottom - m_left_y)])

        # Left
        col, x = 0, 0
        for row in range(self.rows - 1, -1, -1):
            y = row * self.cell_size
            if row % 2 == 0:
                mx, my = self.get_margins(row, col, is_red_layer=is_red_layer)
                points.extend([(x + mx, y + self.cell_size - my), (x + mx, y + my)])
            else:
                m_top_x, m_top_y = self.get_margins(row - 1, col, is_red_layer=is_red_layer)
                m_bottom_x, m_bottom_y = self.get_margins(row + 1, col, is_red_layer=is_red_layer)
                points.extend([(x + m_bottom_x, y + self.cell_size - m_bottom_y), (x + m_top_x, y + m_top_y)])

        self.draw_polygon(points, self.red_stroke_style)

        for row in range(self.rows):
            for col in range(self.cols):
                if row % 2 != 0 and col % 2 != 0:
                    self._draw_red_cutout(col * self.cell_size, row * self.cell_size, row, col, is_red_layer)

    def _draw_red_cutout(self, x, y, row, col, is_red_layer):
        is_tl_large = ((row - 1) // 2 + (col - 1) // 2) % 2 == 0
        is_tr_large = ((row - 1) // 2 + (col + 1) // 2) % 2 == 0
        is_bl_large = ((row + 1) // 2 + (col - 1) // 2) % 2 == 0
        is_br_large = ((row + 1) // 2 + (col + 1) // 2) % 2 == 0

        m_tl_x, m_tl_y = self.get_margins(row - 1, col - 1, is_red_layer=is_red_layer)
        m_tr_x, m_tr_y = self.get_margins(row - 1, col + 1, is_red_layer=is_red_layer)
        m_bl_x, m_bl_y = self.get_margins(row + 1, col - 1, is_red_layer=is_red_layer)
        m_br_x, m_br_y = self.get_margins(row + 1, col + 1, is_red_layer=is_red_layer)

        P_T1 = (x, y - m_tl_y) if is_tl_large else (x + m_tl_x, y - m_tl_y)
        P_T2 = (x + self.cell_size - m_tr_x, y - m_tr_y) if is_tl_large else (x + self.cell_size, y - m_tr_y)
        
        P_B1 = (x, y + self.cell_size + m_bl_y) if is_bl_large else (x + m_bl_x, y + self.cell_size + m_bl_y)
        P_B2 = (x + self.cell_size - m_br_x, y + self.cell_size + m_br_y) if is_bl_large else (x + self.cell_size, y + self.cell_size + m_br_y)
        
        P_L1 = (x - m_tl_x, y) if is_tl_large else (x - m_tl_x, y + m_tl_y)
        P_L2 = (x - m_bl_x, y + self.cell_size - m_bl_y) if is_tl_large else (x - m_bl_x, y + self.cell_size)
        
        P_R1 = (x + self.cell_size + m_tr_x, y) if is_tr_large else (x + self.cell_size + m_tr_x, y + m_tr_y)
        P_R2 = (x + self.cell_size + m_br_x, y + self.cell_size - m_br_y) if is_tr_large else (x + self.cell_size + m_br_x, y + self.cell_size)

        v_tl = self._line_intersection(P_T1, P_T2, P_L1, P_L2)
        v_tr = self._line_intersection(P_T1, P_T2, P_R1, P_R2)
        v_bl = self._line_intersection(P_B1, P_B2, P_L1, P_L2)
        v_br = self._line_intersection(P_B1, P_B2, P_R1, P_R2)

        self.draw_polygon([v_tl, v_tr, v_br, v_bl], self.red_stroke_style)