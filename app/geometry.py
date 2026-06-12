import svgwrite
import math

class VariableGeometryGenerator:
    def __init__(self, cols, rows, start_cell_size, end_cell_size_x, end_cell_size_y, normal_gap_x, normal_gap_y, alt_gap_x, alt_gap_y, bridge_size, tessellation_position=4, tessellation_tolerance=0.0):
        self.scale = 3.7795275591  # 96 DPI scale for LightBurn (1mm = 3.7795px)
        self.cols = cols
        self.rows = rows
        self.start_cell_size = start_cell_size
        self.end_cell_size_x = end_cell_size_x
        self.end_cell_size_y = end_cell_size_y
        self.normal_gap_x = normal_gap_x
        self.normal_gap_y = normal_gap_y
        self.alt_gap_x = alt_gap_x
        self.alt_gap_y = alt_gap_y
        self.bridge_size = bridge_size
        self.tessellation_position = tessellation_position  # 0-8 for 3x3 grid (default 4 = center)
        self.tess_tolerance = tessellation_tolerance
        
        self.cell_widths = [self._calc_cell_size_x(c) for c in range(cols)]
        self.cell_heights = [self._calc_cell_size_y(r) for r in range(rows)]
        
        self.cell_x = [0.0] * cols
        curr_x = 0.0
        for c in range(cols):
            self.cell_x[c] = curr_x
            curr_x += self.cell_widths[c]
        self.canvas_width = curr_x

        self.cell_y = [0.0] * rows
        curr_y = 0.0
        for r in range(rows):
            self.cell_y[r] = curr_y
            curr_y += self.cell_heights[r]
        self.canvas_height = curr_y

        self.stroke_style = {'stroke': 'black', 'stroke_width': 0.2 * self.scale, 'fill': 'none'}
        self.red_stroke_style = {'stroke': 'red', 'stroke_width': 0.2 * self.scale, 'fill': 'none'}
        self.green_stroke_style = {'stroke': 'blue', 'stroke_width': 0.2 * self.scale, 'fill': 'none'}
        self.blue_dashed_style = {'stroke': 'blue', 'stroke_width': 0.2 * self.scale, 'fill': 'none', 'stroke_dasharray': '3,3'}
        self.sheet_style = {'stroke': 'blue', 'stroke_width': 0.4 * self.scale, 'fill': 'none'}
        
        self.offset_x = 0
        self.offset_y = 0
        self.current_dwg = None

    def _calc_cell_size_x(self, col):
        if self.cols <= 1: return self.start_cell_size
        return self.start_cell_size + (self.end_cell_size_x - self.start_cell_size) * (col / (self.cols - 1))

    def _calc_cell_size_y(self, row):
        if self.rows <= 1: return self.start_cell_size
        progress = (self.rows - 1 - row) / (self.rows - 1)  # Bottom row is 0.0, Top row is 1.0
        return self.start_cell_size + (self.end_cell_size_y - self.start_cell_size) * progress


    def _should_split_top_edge(self):
        """Returns True if top edge should be split in half for tessellation"""
        return self.tessellation_position in [3, 4, 5, 6, 7, 8]
    
    def _should_split_bottom_edge(self):
        """Returns True if bottom edge should be split in half for tessellation"""
        return self.tessellation_position in [0, 1, 2, 3, 4, 5]
    
    def _should_split_left_edge(self):
        """Returns True if left edge should be split in half for tessellation"""
        return self.tessellation_position in [1, 2, 4, 5, 7, 8]
    
    def _should_split_right_edge(self):
        """Returns True if right edge should be split in half for tessellation"""
        return self.tessellation_position in [0, 1, 3, 4, 6, 7]

    @property
    def clip_box(self):
        min_x = (0.5 * self.cell_widths[0]) + self.tess_tolerance if self._should_split_left_edge() else 0.0
        max_x = self.canvas_width - (0.5 * self.cell_widths[-1]) - self.tess_tolerance if self._should_split_right_edge() else self.canvas_width
        min_y = (0.5 * self.cell_heights[0]) + self.tess_tolerance if self._should_split_top_edge() else 0.0
        max_y = self.canvas_height - (0.5 * self.cell_heights[-1]) - self.tess_tolerance if self._should_split_bottom_edge() else self.canvas_height
        return (min_x, min_y, max_x, max_y)

    def _clip_line(self, p1, p2):
        min_x, min_y, max_x, max_y = self.clip_box
        x1, y1 = p1
        x2, y2 = p2
        
        INSIDE, LEFT, RIGHT, BOTTOM, TOP = 0, 1, 2, 4, 8
        def compute_outcode(x, y):
            code = INSIDE
            if x < min_x: code |= LEFT
            elif x > max_x: code |= RIGHT
            if y < min_y: code |= BOTTOM
            elif y > max_y: code |= TOP
            return code
            
        outcode1 = compute_outcode(x1, y1)
        outcode2 = compute_outcode(x2, y2)
        accept = False
        
        while True:
            if not (outcode1 | outcode2):
                accept = True
                break
            elif outcode1 & outcode2:
                break
            else:
                x, y = 0.0, 0.0
                outcode_out = outcode1 if outcode1 else outcode2
                if outcode_out & TOP:
                    x = x1 + (x2 - x1) * (max_y - y1) / (y2 - y1)
                    y = max_y
                elif outcode_out & BOTTOM:
                    x = x1 + (x2 - x1) * (min_y - y1) / (y2 - y1)
                    y = min_y
                elif outcode_out & RIGHT:
                    y = y1 + (y2 - y1) * (max_x - x1) / (x2 - x1)
                    x = max_x
                elif outcode_out & LEFT:
                    y = y1 + (y2 - y1) * (min_x - x1) / (x2 - x1)
                    x = min_x
                    
                if outcode_out == outcode1:
                    x1, y1 = x, y
                    outcode1 = compute_outcode(x1, y1)
                else:
                    x2, y2 = x, y
                    outcode2 = compute_outcode(x2, y2)
                    
        if accept:
            return (x1, y1), (x2, y2)
        return None, None

    def get_margins(self, row, col, is_inverted=False, is_red_layer=False):
        if is_red_layer:
            return self.normal_gap_x, self.normal_gap_y
        if not is_inverted:
            return self.normal_gap_x, self.normal_gap_y
            
        # For x-tabs (odd row and odd col), maintain the normal gap width
        if row % 2 != 0 and col % 2 != 0:
            return self.normal_gap_x, self.normal_gap_y
            
        is_large_square = (row // 2 + col // 2) % 2 == 0
        if is_inverted:
            is_large_square = not is_large_square
            
        if not is_large_square:
            return self.alt_gap_x, self.alt_gap_y
        else:
            return self.normal_gap_x, self.normal_gap_y

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
            
        scale = self.scale
        return svgwrite.Drawing(
            size=(f"{vw}mm", f"{vh}mm"),
            viewBox=f"{vx * scale} {vy * scale} {vw * scale} {vh * scale}"
        )

    def _translate_point(self, point):
        return ((point[0] + self.offset_x) * self.scale, (point[1] + self.offset_y) * self.scale)

    def _translate_points(self, points):
        return [self._translate_point(point) for point in points]

    def draw_solid_line(self, p1, p2, style=None, apply_clip=True):
        if style is None: style = self.stroke_style
        if apply_clip:
            clipped = self._clip_line(p1, p2)
            if clipped[0] and clipped[1]:
                p1_c, p2_c = clipped
                if self.current_dwg:
                    self.current_dwg.add(self.current_dwg.line(start=self._translate_point(p1_c), end=self._translate_point(p2_c), **style))
        else:
            if self.current_dwg:
                self.current_dwg.add(self.current_dwg.line(start=self._translate_point(p1), end=self._translate_point(p2), **style))
            
    def draw_polygon(self, points, style=None):
        if style is None: style = self.stroke_style
        if not points: return
        for i in range(len(points)):
            p1 = points[i]
            p2 = points[(i + 1) % len(points)]
            self.draw_solid_line(p1, p2, style)

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
        
        edge_on_perim = [row == 0, col == self.cols - 1, row == self.rows - 1, col == 0]
        
        # Determine which edges should be split for tessellation
        should_split_edges = [
            edge_on_perim[0] and self._should_split_top_edge(),      # top edge
            edge_on_perim[1] and self._should_split_right_edge(),    # right edge
            edge_on_perim[2] and self._should_split_bottom_edge(),   # bottom edge
            edge_on_perim[3] and self._should_split_left_edge()      # left edge
        ]

        corners = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        
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
    def generate(self, show_base, show_top, show_red, show_grid, show_sheet=False, align_x=5.0, align_y=5.0):
        sheet_w, sheet_h = 279, 216
        if show_sheet:
            self.offset_x = align_x
            self.offset_y = sheet_h - self.canvas_height - align_y
        else:
            self.offset_x = 0
            self.offset_y = 0

        self.current_dwg = self.create_drawing(show_sheet, sheet_w, sheet_h)

        if show_sheet:
            # Draw the sheet boundary
            self.current_dwg.add(
                self.current_dwg.rect(
                    insert=(0, 0),
                    size=(sheet_w * self.scale, sheet_h * self.scale),
                    **self.sheet_style
                )
            )
        
        # 1. 10x10 Grid (Visual only)
        if show_grid:
            self._draw_10x10_grid(show_sheet, sheet_w, sheet_h)

        # 2. Museum Board Base (White Layer)
        if show_base:
            self._draw_grid_layer(is_inverted=False, style=self.stroke_style)
            self._draw_boundary_gaps(is_inverted=False, style=self.stroke_style)
            self._draw_clip_boundaries(is_inverted=False, style=self.stroke_style)

        # 3. Museum Board Top (Green Layer)
        if show_top:
            self._draw_grid_layer(is_inverted=True, style=self.green_stroke_style)
            self._draw_boundary_gaps(is_inverted=True, style=self.green_stroke_style)
            self._draw_clip_boundaries(is_inverted=True, style=self.green_stroke_style)

        # 4. Shrinky Dink & Tape Sheets (Red Layer)
        if show_red:
            self._draw_red_layer()

        # Finalize
        svg_str = self.current_dwg.tostring()
        self.current_dwg = None
        return svg_str

    def _draw_clip_boundaries(self, is_inverted, style):
        min_x, min_y, max_x, max_y = self.clip_box
        if self._should_split_top_edge():
            self.draw_solid_line((min_x, min_y), (max_x, min_y), style, apply_clip=False)
        if self._should_split_bottom_edge():
            self.draw_solid_line((min_x, max_y), (max_x, max_y), style, apply_clip=False)
        if self._should_split_left_edge():
            self.draw_solid_line((min_x, min_y), (min_x, max_y), style, apply_clip=False)
        if self._should_split_right_edge():
            self.draw_solid_line((max_x, min_y), (max_x, max_y), style, apply_clip=False)

    def _draw_10x10_grid(self, show_sheet=False, sheet_w=279, sheet_h=216):
        grid_style = {'stroke': '#444444', 'stroke_width': 0.1, 'fill': 'none', 'stroke-dasharray': '2,2'}
        
        if show_sheet:
            width = sheet_w
            height = sheet_h
            for x in range(0, int(width) + 1, 10):
                self.current_dwg.add(
                    self.current_dwg.line(
                        start=(x * self.scale, 0),
                        end=(x * self.scale, height * self.scale),
                        **grid_style
                    )
                )
            for y in range(0, int(height) + 1, 10):
                self.current_dwg.add(
                    self.current_dwg.line(
                        start=(0, y * self.scale),
                        end=(width * self.scale, y * self.scale),
                        **grid_style
                    )
                )
        else:
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
                x = self.cell_x[col]
                y = self.cell_y[row]
                cell_w = self.cell_widths[col]
                cell_h = self.cell_heights[row]
                
                mx, my = self.get_margins(row, col, is_inverted)

                if row % 2 == 0 and col % 2 == 0:
                    is_large_square = (row // 2 + col // 2) % 2 == 0
                    if is_inverted: is_large_square = not is_large_square

                    if is_large_square:
                        self.draw_rectangle(x, y, cell_w, cell_h, True, row, col, style)
                    else:
                        w = cell_w - (2 * mx)
                        h = cell_h - (2 * my)
                        self.draw_rectangle(x + mx, y + my, w, h, False, row, col, style)

                elif row % 2 == 0 and col % 2 != 0:
                    m_left_x, m_left_y = self.get_margins(row, col - 1, is_inverted)
                    m_right_x, m_right_y = self.get_margins(row, col + 1, is_inverted)
                    y1_L, y2_L = y + m_left_y, y + cell_h - m_left_y
                    y1_R, y2_R = y + m_right_y, y + cell_h - m_right_y

                    left_is_large = (row // 2 + (col - 1) // 2) % 2 == 0
                    if is_inverted: left_is_large = not left_is_large

                    if left_is_large:
                        end_x = x + cell_w - m_right_x
                        self.draw_solid_line((x, y1_L), (end_x, y1_R), style)
                        self.draw_solid_line((end_x, y1_R), (end_x, y2_R), style)
                        self.draw_solid_line((end_x, y2_R), (x, y2_L), style)
                    else:
                        start_x, end_x = x + m_left_x, x + cell_w
                        self.draw_solid_line((start_x, y1_L), (end_x, y1_R), style)
                        self.draw_solid_line((start_x, y1_L), (start_x, y2_L), style)
                        self.draw_solid_line((start_x, y2_L), (end_x, y2_R), style)

                elif row % 2 != 0 and col % 2 == 0:
                    m_top_x, m_top_y = self.get_margins(row - 1, col, is_inverted)
                    m_bottom_x, m_bottom_y = self.get_margins(row + 1, col, is_inverted)
                    x1_T, x2_T = x + m_top_x, x + cell_w - m_top_x
                    x1_B, x2_B = x + m_bottom_x, x + cell_w - m_bottom_x

                    top_is_large = ((row - 1) // 2 + col // 2) % 2 == 0
                    if is_inverted: top_is_large = not top_is_large

                    if top_is_large:
                        end_y = y + cell_h - m_bottom_y
                        self.draw_solid_line((x1_T, y), (x1_B, end_y), style)
                        self.draw_solid_line((x2_T, y), (x2_B, end_y), style)
                        self.draw_solid_line((x1_B, end_y), (x2_B, end_y), style)
                    else:
                        start_y, end_y = y + m_top_y, y + cell_h
                        self.draw_solid_line((x1_T, start_y), (x1_B, end_y), style)
                        self.draw_solid_line((x2_T, start_y), (x2_B, end_y), style)
                        self.draw_solid_line((x1_T, start_y), (x2_T, start_y), style)

                elif row % 2 != 0 and col % 2 != 0:
                    self._draw_x_tabs(x, y, row, col, is_inverted, style)

    def _draw_x_tabs(self, x, y, row, col, is_inverted, style):
        d_center_x = self.normal_gap_x
        d_center_y = self.normal_gap_y
        
        cell_w = self.cell_widths[col]
        cell_h = self.cell_heights[row]

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

        tr_x = x + cell_w if is_tr_large else x + cell_w + m_tr_x
        tr_y = y if is_tr_large else y - m_tr_y

        bl_x = x if is_bl_large else x - m_bl_x
        bl_y = y + cell_h if is_bl_large else y + cell_h + m_bl_y

        br_x = x + cell_w if is_br_large else x + cell_w + m_br_x
        br_y = y + cell_h if is_br_large else y + cell_h + m_br_y

        cx = x + cell_w / 2
        cy = y + cell_h / 2

        self.draw_solid_line((tl_x, tl_y - m_tl_y), (cx, cy - d_center_y), style, apply_clip=False)
        self.draw_solid_line((cx + d_center_x, cy), (br_x + m_br_x, br_y), style, apply_clip=False)
        self.draw_solid_line((tl_x - m_tl_x, tl_y), (cx - d_center_x, cy), style, apply_clip=False)
        self.draw_solid_line((cx, cy + d_center_y), (br_x, br_y + m_br_y), style, apply_clip=False)

        self.draw_solid_line((bl_x - m_bl_x, bl_y), (cx - d_center_x, cy), style, apply_clip=False)
        self.draw_solid_line((cx, cy - d_center_y), (tr_x, tr_y - m_tr_y), style, apply_clip=False)
        self.draw_solid_line((bl_x, bl_y + m_bl_y), (cx, cy + d_center_y), style, apply_clip=False)
        self.draw_solid_line((cx + d_center_x, cy), (tr_x + m_tr_x, tr_y), style, apply_clip=False)

    def _draw_boundary_gaps(self, is_inverted, style):
        # Top boundary
        row, y = 0, 0
        for col in range(self.cols - 1):
            x = self.cell_x[col]
            cell_w = self.cell_widths[col]
            next_x = self.cell_x[col + 1] if col + 1 < self.cols else self.canvas_width
            
            if col % 2 == 0:
                is_large = (row // 2 + col // 2) % 2 == 0
                if is_inverted: is_large = not is_large
                mx, my = self.get_margins(row, col, is_inverted)
                TR = (x + cell_w, y) if is_large else (x + cell_w - mx, y + my)
                
                left_is_large = is_large
                TL_next = (next_x, y + my) if left_is_large else (next_x + mx, y + my)
                self.draw_solid_line(TR, TL_next, style)
            else:
                mx, my = self.get_margins(row, col + 1, is_inverted)
                right_is_large = (row // 2 + (col + 1) // 2) % 2 == 0
                if is_inverted: right_is_large = not right_is_large
                TR = (x + cell_w, y + my) if right_is_large else (x + cell_w - mx, y + my)
                
                is_large_next = right_is_large
                TL_next = (next_x, y) if is_large_next else (next_x + mx, y + my)
                self.draw_solid_line(TR, TL_next, style)

        # Bottom boundary
        row = self.rows - 1
        y_bottom = self.canvas_height
        for col in range(self.cols - 1):
            x = self.cell_x[col]
            cell_w = self.cell_widths[col]
            next_x = self.cell_x[col + 1] if col + 1 < self.cols else self.canvas_width
            
            if col % 2 == 0:
                is_large = (row // 2 + col // 2) % 2 == 0
                if is_inverted: is_large = not is_large
                mx, my = self.get_margins(row, col, is_inverted)
                BR = (x + cell_w, y_bottom) if is_large else (x + cell_w - mx, y_bottom - my)
                
                left_is_large = is_large
                BL_next = (next_x, y_bottom - my) if left_is_large else (next_x + mx, y_bottom - my)
                self.draw_solid_line(BR, BL_next, style)
            else:
                mx, my = self.get_margins(row, col + 1, is_inverted)
                right_is_large = (row // 2 + (col + 1) // 2) % 2 == 0
                if is_inverted: right_is_large = not right_is_large
                BR = (x + cell_w, y_bottom - my) if right_is_large else (x + cell_w - mx, y_bottom - my)
                
                is_large_next = right_is_large
                BL_next = (next_x, y_bottom) if is_large_next else (next_x + mx, y_bottom - my)
                self.draw_solid_line(BR, BL_next, style)

        # Left boundary
        col, x = 0, 0
        for row in range(self.rows - 1):
            y = self.cell_y[row]
            cell_h = self.cell_heights[row]
            next_y = self.cell_y[row + 1] if row + 1 < self.rows else self.canvas_height
            
            if row % 2 == 0:
                is_large = (row // 2 + col // 2) % 2 == 0
                if is_inverted: is_large = not is_large
                mx, my = self.get_margins(row, col, is_inverted)
                BL = (x, y + cell_h) if is_large else (x + mx, y + cell_h - my)
                
                top_is_large = is_large
                TL_next = (x + mx, next_y) if top_is_large else (x + mx, next_y + my)
                self.draw_solid_line(BL, TL_next, style)
            else:
                mx, my = self.get_margins(row + 1, col, is_inverted)
                bottom_is_large = ((row + 1) // 2 + col // 2) % 2 == 0
                if is_inverted: bottom_is_large = not bottom_is_large
                BL = (x + mx, y + cell_h) if bottom_is_large else (x + mx, y + cell_h - my)
                
                is_large_next = bottom_is_large
                TL_next = (x, next_y) if is_large_next else (x + mx, next_y + my)
                self.draw_solid_line(BL, TL_next, style)

        # Right boundary
        col = self.cols - 1
        x_right = self.canvas_width
        for row in range(self.rows - 1):
            y = self.cell_y[row]
            cell_h = self.cell_heights[row]
            next_y = self.cell_y[row + 1] if row + 1 < self.rows else self.canvas_height
            
            if row % 2 == 0:
                is_large = (row // 2 + col // 2) % 2 == 0
                if is_inverted: is_large = not is_large
                mx, my = self.get_margins(row, col, is_inverted)
                BR = (x_right, y + cell_h) if is_large else (x_right - mx, y + cell_h - my)
                
                top_is_large = is_large
                TR_next = (x_right - mx, next_y) if top_is_large else (x_right - mx, next_y + my)
                self.draw_solid_line(BR, TR_next, style)
            else:
                mx, my = self.get_margins(row + 1, col, is_inverted)
                bottom_is_large = ((row + 1) // 2 + col // 2) % 2 == 0
                if is_inverted: bottom_is_large = not bottom_is_large
                BR = (x_right - mx, y + cell_h) if bottom_is_large else (x_right - mx, y + cell_h - my)
                
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
        shrink_top_row = self._should_split_top_edge()
        shrink_bottom_row = self._should_split_bottom_edge()
        shrink_left_col = self._should_split_left_edge()
        shrink_right_col = self._should_split_right_edge()

        def _maybe_shrink_point(point):
            px, py = point
            eps = 1e-5
            min_x, min_y, max_x, max_y = self.clip_box
            
            if shrink_top_row and abs(py - self.normal_gap_y) < eps:
                py = min_y
            elif shrink_bottom_row and abs(py - (self.canvas_height - self.normal_gap_y)) < eps:
                py = max_y

            if shrink_left_col and abs(px - self.normal_gap_x) < eps:
                px = min_x
            elif shrink_right_col and abs(px - (self.canvas_width - self.normal_gap_x)) < eps:
                px = max_x

            return (px, py)

        # Top
        row, y = 0, 0
        for col in range(self.cols):
            x = self.cell_x[col]
            cell_w = self.cell_widths[col]
            if col % 2 == 0:
                mx, my = self.get_margins(row, col, is_red_layer=is_red_layer)
                points.extend([(x + mx, y + my), (x + cell_w - mx, y + my)])
            else:
                m_left_x, m_left_y = self.get_margins(row, col - 1, is_red_layer=is_red_layer)
                m_right_x, m_right_y = self.get_margins(row, col + 1, is_red_layer=is_red_layer)
                points.extend([(x + m_left_x, y + m_left_y), (x + cell_w - m_right_x, y + m_right_y)])

        # Right
        col = self.cols - 1
        x_right = self.canvas_width
        for row in range(self.rows):
            y = self.cell_y[row]
            cell_h = self.cell_heights[row]
            if row % 2 == 0:
                mx, my = self.get_margins(row, col, is_red_layer=is_red_layer)
                points.extend([(x_right - mx, y + my), (x_right - mx, y + cell_h - my)])
            else:
                m_top_x, m_top_y = self.get_margins(row - 1, col, is_red_layer=is_red_layer)
                m_bottom_x, m_bottom_y = self.get_margins(row + 1, col, is_red_layer=is_red_layer)
                points.extend([(x_right - m_top_x, y + m_top_y), (x_right - m_bottom_x, y + cell_h - m_bottom_y)])

        # Bottom
        row = self.rows - 1
        y_bottom = self.canvas_height
        for col in range(self.cols - 1, -1, -1):
            x = self.cell_x[col]
            cell_w = self.cell_widths[col]
            if col % 2 == 0:
                mx, my = self.get_margins(row, col, is_red_layer=is_red_layer)
                points.extend([(x + cell_w - mx, y_bottom - my), (x + mx, y_bottom - my)])
            else:
                m_left_x, m_left_y = self.get_margins(row, col - 1, is_red_layer=is_red_layer)
                m_right_x, m_right_y = self.get_margins(row, col + 1, is_red_layer=is_red_layer)
                points.extend([(x + cell_w - m_right_x, y_bottom - m_right_y), (x + m_left_x, y_bottom - m_left_y)])

        # Left
        col, x = 0, 0
        for row in range(self.rows - 1, -1, -1):
            y = self.cell_y[row]
            cell_h = self.cell_heights[row]
            if row % 2 == 0:
                mx, my = self.get_margins(row, col, is_red_layer=is_red_layer)
                points.extend([(x + mx, y + cell_h - my), (x + mx, y + my)])
            else:
                m_top_x, m_top_y = self.get_margins(row - 1, col, is_red_layer=is_red_layer)
                m_bottom_x, m_bottom_y = self.get_margins(row + 1, col, is_red_layer=is_red_layer)
                points.extend([(x + m_bottom_x, y + cell_h - m_bottom_y), (x + m_top_x, y + m_top_y)])

        for row in range(self.rows):
            for col in range(self.cols):
                if row % 2 != 0 and col % 2 != 0:
                    self._draw_red_cutout(self.cell_x[col], self.cell_y[row], row, col, is_red_layer)

        if shrink_top_row or shrink_bottom_row or shrink_left_col or shrink_right_col:
            shrunk_points = [_maybe_shrink_point(point) for point in points]
            self.draw_polygon(shrunk_points, self.red_stroke_style)
        else:
            self.draw_polygon(points, self.red_stroke_style)

        # Draw the blue dashed line across the cut boundaries for tape/shrinky scoring
        min_x, min_y, max_x, max_y = self.clip_box
        if shrink_top_row:
            self.draw_solid_line((min_x, min_y), (max_x, min_y), self.blue_dashed_style, apply_clip=False)
        if shrink_bottom_row:
            self.draw_solid_line((min_x, max_y), (max_x, max_y), self.blue_dashed_style, apply_clip=False)
        if shrink_left_col:
            self.draw_solid_line((min_x, min_y), (min_x, max_y), self.blue_dashed_style, apply_clip=False)
        if shrink_right_col:
            self.draw_solid_line((max_x, min_y), (max_x, max_y), self.blue_dashed_style, apply_clip=False)

    def _draw_red_cutout(self, x, y, row, col, is_red_layer):
        cell_w = self.cell_widths[col]
        cell_h = self.cell_heights[row]
        
        is_tl_large = ((row - 1) // 2 + (col - 1) // 2) % 2 == 0
        is_tr_large = ((row - 1) // 2 + (col + 1) // 2) % 2 == 0
        is_bl_large = ((row + 1) // 2 + (col - 1) // 2) % 2 == 0
        is_br_large = ((row + 1) // 2 + (col + 1) // 2) % 2 == 0

        m_tl_x, m_tl_y = self.get_margins(row - 1, col - 1, is_red_layer=is_red_layer)
        m_tr_x, m_tr_y = self.get_margins(row - 1, col + 1, is_red_layer=is_red_layer)
        m_bl_x, m_bl_y = self.get_margins(row + 1, col - 1, is_red_layer=is_red_layer)
        m_br_x, m_br_y = self.get_margins(row + 1, col + 1, is_red_layer=is_red_layer)

        P_T1 = (x, y - m_tl_y) if is_tl_large else (x + m_tl_x, y - m_tl_y)
        P_T2 = (x + cell_w - m_tr_x, y - m_tr_y) if is_tr_large else (x + cell_w, y - m_tr_y)
        
        P_B1 = (x, y + cell_h + m_bl_y) if is_bl_large else (x + m_bl_x, y + cell_h + m_bl_y)
        P_B2 = (x + cell_w - m_br_x, y + cell_h + m_br_y) if is_br_large else (x + cell_w, y + cell_h + m_br_y)
        
        P_L1 = (x - m_tl_x, y) if is_tl_large else (x - m_tl_x, y + m_tl_y)
        P_L2 = (x - m_bl_x, y + cell_h - m_bl_y) if is_bl_large else (x - m_bl_x, y + cell_h)
        
        P_R1 = (x + cell_w + m_tr_x, y) if is_tr_large else (x + cell_w + m_tr_x, y + m_tr_y)
        P_R2 = (x + cell_w + m_br_x, y + cell_h - m_br_y) if is_br_large else (x + cell_w + m_br_x, y + cell_h)

        v_tl = self._line_intersection(P_T1, P_T2, P_L1, P_L2)
        v_tr = self._line_intersection(P_T1, P_T2, P_R1, P_R2)
        v_bl = self._line_intersection(P_B1, P_B2, P_L1, P_L2)
        v_br = self._line_intersection(P_B1, P_B2, P_R1, P_R2)

        self.draw_polygon([v_tl, v_tr, v_br, v_bl], self.red_stroke_style)