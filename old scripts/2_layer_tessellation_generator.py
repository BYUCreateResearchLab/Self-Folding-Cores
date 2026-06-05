import svgwrite
import math
import os
import re

class VariableGeometryGenerator:
    def __init__(self, filename, cols, rows, cell_size, min_margin, max_margin, min_tab_width, max_tab_width, bridge_size):
        self.filename = filename
        self.cols = cols
        self.rows = rows
        self.cell_size = cell_size
        self.min_margin = min_margin
        self.max_margin = max_margin
        self.min_tab_width = min_tab_width
        self.max_tab_width = max_tab_width
        self.bridge_size = bridge_size
        
        self.canvas_width = cols * cell_size
        self.canvas_height = rows * cell_size
        self.stroke_style = {'stroke': 'white', 'stroke_width': 0.1, 'fill': 'none'}
        self.red_stroke_style = {'stroke': 'red', 'stroke_width': 0.1, 'fill': 'none'}

    def get_margin(self, row, col):
        """Creates a gradient from min_margin to max_margin."""
        if self.cols <= 1:
            return self.min_margin
        progress = col / (self.cols - 1)
        return self.min_margin + (self.max_margin - self.min_margin) * progress

    def get_tab_width(self, row, col):
        """Creates a gradient from min_tab_width to max_tab_width based on position."""
        if self.cols <= 1:
            return self.min_tab_width
        progress = col / (self.cols - 1)
        return self.min_tab_width + (self.max_tab_width - self.min_tab_width) * progress

    def create_drawing(self):
        return svgwrite.Drawing(
            self.filename,
            size=(f"{self.canvas_width}mm", f"{self.canvas_height}mm"),
            viewBox=f"0 0 {self.canvas_width} {self.canvas_height}"
        )

    def save_drawing(self, dwg):
        dwg.save()
        print(f"Successfully saved to {self.filename}")

    def draw_solid_line(self, dwg, p1, p2):
        dwg.add(dwg.line(start=p1, end=p2, **self.stroke_style))

    def has_xtab(self, r, c):
        """Helper to check if an odd,odd coordinate contains an X-tab (inside grid bounds)."""
        return 0 <= r < self.rows and 0 <= c < self.cols

    def draw_square(self, dwg, x, y, size, is_large, row, col):
        # Check adjacent (Odd, Odd) cells to see if this corner connects to an X-tab
        corner_bridges = [
            self.has_xtab(row - 1, col - 1),  # Top-Left
            self.has_xtab(row - 1, col + 1),  # Top-Right
            self.has_xtab(row + 1, col + 1),  # Bottom-Right
            self.has_xtab(row + 1, col - 1)   # Bottom-Left
        ]
        
        corners = [
            (x, y),
            (x + size, y),
            (x + size, y + size),
            (x, y + size)
        ]
        
        # Determine if each of the 4 edges lies exactly on the canvas perimeter
        edge_on_perim = [
            row == 0,
            col == self.cols - 1,
            row == self.rows - 1,
            col == 0
        ]
        
        for i in range(4):
            p1 = corners[i]
            p2 = corners[(i + 1) % 4]
            
            has_start_bridge = corner_bridges[i]
            has_end_bridge = corner_bridges[(i + 1) % 4]
            
            # Mid-bridges only exist on Large Squares and NEVER on the perimeter
            has_mid_bridge = is_large and not edge_on_perim[i]
            
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            length = math.hypot(dx, dy)
            if length < 1e-5: continue
            
            ux = dx / length
            uy = dy / length
            
            # Calculate start and end offsets based on corner bridge requirements
            t_start = (self.bridge_size / 2.0) if has_start_bridge else 0.0
            t_end = length - ((self.bridge_size / 2.0) if has_end_bridge else 0.0)
            
            if t_start >= t_end:
                continue
                
            if has_mid_bridge:
                t_mid_left = (length / 2.0) - (self.bridge_size / 2.0)
                t_mid_right = (length / 2.0) + (self.bridge_size / 2.0)
                
                if t_start < t_mid_left:
                    dwg.add(dwg.line(start=(p1[0] + ux * t_start, p1[1] + uy * t_start),
                                     end=(p1[0] + ux * t_mid_left, p1[1] + uy * t_mid_left), **self.stroke_style))
                if t_mid_right < t_end:
                    dwg.add(dwg.line(start=(p1[0] + ux * t_mid_right, p1[1] + uy * t_mid_right),
                                     end=(p1[0] + ux * t_end, p1[1] + uy * t_end), **self.stroke_style))
            else:
                dwg.add(dwg.line(start=(p1[0] + ux * t_start, p1[1] + uy * t_start),
                                 end=(p1[0] + ux * t_end, p1[1] + uy * t_end), **self.stroke_style))


class VariableTabbedGrid(VariableGeometryGenerator):
    def generate(self):
        dwg = self.create_drawing()

        for row in range(self.rows):
            for col in range(self.cols):
                x = col * self.cell_size
                y = row * self.cell_size
                
                # Fetch local margin for this specific cell
                m = self.get_margin(row, col)

                # 1. Intersections (Even Row, Even Col)
                if row % 2 == 0 and col % 2 == 0:
                    is_large_square = (row // 2 + col // 2) % 2 == 0
                    if is_large_square:
                        self.draw_square(dwg, x, y, self.cell_size, True, row, col)
                    else:
                        size = self.cell_size - (2 * m)
                        self.draw_square(dwg, x + m, y + m, size, False, row, col)

                # 2. Horizontal Rectangles (Even Row, Odd Col)
                elif row % 2 == 0 and col % 2 != 0:
                    m_left = self.get_margin(row, col - 1)
                    m_right = self.get_margin(row, col + 1)
                    
                    y1_L = y + m_left
                    y2_L = y + self.cell_size - m_left
                    y1_R = y + m_right
                    y2_R = y + self.cell_size - m_right

                    left_is_large = (row // 2 + (col - 1) // 2) % 2 == 0
                    if left_is_large:
                        end_x = x + self.cell_size - m_right
                        self.draw_solid_line(dwg, (x, y1_L), (end_x, y1_R))     # Top
                        self.draw_solid_line(dwg, (end_x, y1_R), (end_x, y2_R)) # Right
                        self.draw_solid_line(dwg, (end_x, y2_R), (x, y2_L))     # Bottom
                        # Skipped Left side because it perfectly overlaps the bridged Large Square
                    else:
                        start_x = x + m_left
                        end_x = x + self.cell_size
                        self.draw_solid_line(dwg, (start_x, y1_L), (end_x, y1_R)) # Top
                        self.draw_solid_line(dwg, (start_x, y1_L), (start_x, y2_L)) # Left
                        self.draw_solid_line(dwg, (start_x, y2_L), (end_x, y2_R)) # Bottom
                        # Skipped Right side because it perfectly overlaps the bridged Large Square

                # 3. Vertical Rectangles (Odd Row, Even Col)
                elif row % 2 != 0 and col % 2 == 0:
                    m_top = self.get_margin(row - 1, col)
                    m_bottom = self.get_margin(row + 1, col)

                    x1_T = x + m_top
                    x2_T = x + self.cell_size - m_top
                    x1_B = x + m_bottom
                    x2_B = x + self.cell_size - m_bottom

                    top_is_large = ((row - 1) // 2 + col // 2) % 2 == 0
                    if top_is_large:
                        end_y = y + self.cell_size - m_bottom
                        self.draw_solid_line(dwg, (x1_T, y), (x1_B, end_y))       # Left
                        self.draw_solid_line(dwg, (x2_T, y), (x2_B, end_y))       # Right
                        self.draw_solid_line(dwg, (x1_B, end_y), (x2_B, end_y))   # Bottom
                        # Skipped Top side because it perfectly overlaps the bridged Large Square
                    else:
                        start_y = y + m_top
                        end_y = y + self.cell_size
                        self.draw_solid_line(dwg, (x1_T, start_y), (x1_B, end_y)) # Left
                        self.draw_solid_line(dwg, (x2_T, start_y), (x2_B, end_y)) # Right
                        self.draw_solid_line(dwg, (x1_T, start_y), (x2_T, start_y)) # Top
                        # Skipped Bottom side because it perfectly overlaps the bridged Large Square

                # 4. Alternating X-Tab Pattern (Odd Row, Odd Col)
                elif row % 2 != 0 and col % 2 != 0:
                    self._draw_x_tabs(dwg, x, y, row, col)

        self._draw_boundary_gaps(dwg)
        self._draw_red_layer(dwg)
        self.save_drawing(dwg)

    def _draw_x_tabs(self, dwg, x, y, row, col):
        local_tab_width = self.get_tab_width(row, col)
        d = local_tab_width / math.sqrt(2)

        is_tl_large = ((row - 1) // 2 + (col - 1) // 2) % 2 == 0
        is_tr_large = ((row - 1) // 2 + (col + 1) // 2) % 2 == 0
        is_bl_large = ((row + 1) // 2 + (col - 1) // 2) % 2 == 0
        is_br_large = ((row + 1) // 2 + (col + 1) // 2) % 2 == 0

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

        # --- Two parallel lines at 45° (\) ---
        dwg.add(dwg.line(start=(tl_x, tl_y - d), end=(cx, cy - d), **self.stroke_style))
        dwg.add(dwg.line(start=(cx + d, cy), end=(br_x + d, br_y), **self.stroke_style))
        dwg.add(dwg.line(start=(tl_x - d, tl_y), end=(cx - d, cy), **self.stroke_style))
        dwg.add(dwg.line(start=(cx, cy + d), end=(br_x, br_y + d), **self.stroke_style))

        # --- Two parallel lines at -45° (/) ---
        dwg.add(dwg.line(start=(bl_x - d, bl_y), end=(cx - d, cy), **self.stroke_style))
        dwg.add(dwg.line(start=(cx, cy - d), end=(tr_x, tr_y - d), **self.stroke_style))
        dwg.add(dwg.line(start=(bl_x, bl_y + d), end=(cx, cy + d), **self.stroke_style))
        dwg.add(dwg.line(start=(cx + d, cy), end=(tr_x + d, tr_y), **self.stroke_style))

    def _draw_boundary_gaps(self, dwg):
        # Top boundary (row = 0)
        row = 0
        y = 0
        for col in range(self.cols - 1):
            x = col * self.cell_size
            next_x = (col + 1) * self.cell_size
            if col % 2 == 0: # Square at col, H-Rect at col+1
                is_large = (row // 2 + col // 2) % 2 == 0
                m = self.get_margin(row, col)
                TR = (x + self.cell_size, y) if is_large else (x + self.cell_size - m, y + m)
                
                m_left = self.get_margin(row, col)
                left_is_large = is_large
                TL_next = (next_x, y + m_left) if left_is_large else (next_x + m_left, y + m_left)
                
                self.draw_solid_line(dwg, TR, TL_next)
            else: # H-Rect at col, Square at col+1
                m_right = self.get_margin(row, col + 1)
                right_is_large = (row // 2 + (col + 1) // 2) % 2 == 0
                TR = (x + self.cell_size, y + m_right) if right_is_large else (x + self.cell_size - m_right, y + m_right)
                
                is_large_next = right_is_large
                TL_next = (next_x, y) if is_large_next else (next_x + m_right, y + m_right)
                
                self.draw_solid_line(dwg, TR, TL_next)

        # Bottom boundary (row = self.rows - 1)
        row = self.rows - 1
        y_bottom = row * self.cell_size + self.cell_size
        for col in range(self.cols - 1):
            x = col * self.cell_size
            next_x = (col + 1) * self.cell_size
            if col % 2 == 0: # Square at col, H-Rect at col+1
                is_large = (row // 2 + col // 2) % 2 == 0
                m = self.get_margin(row, col)
                BR = (x + self.cell_size, y_bottom) if is_large else (x + self.cell_size - m, y_bottom - m)
                
                m_left = self.get_margin(row, col)
                left_is_large = is_large
                BL_next = (next_x, y_bottom - m_left) if left_is_large else (next_x + m_left, y_bottom - m_left)
                
                self.draw_solid_line(dwg, BR, BL_next)
            else: # H-Rect at col, Square at col+1
                m_right = self.get_margin(row, col + 1)
                right_is_large = (row // 2 + (col + 1) // 2) % 2 == 0
                BR = (x + self.cell_size, y_bottom - m_right) if right_is_large else (x + self.cell_size - m_right, y_bottom - m_right)
                
                is_large_next = right_is_large
                BL_next = (next_x, y_bottom) if is_large_next else (next_x + m_right, y_bottom - m_right)
                
                self.draw_solid_line(dwg, BR, BL_next)

        # Left boundary (col = 0)
        col = 0
        x = 0
        for row in range(self.rows - 1):
            y = row * self.cell_size
            next_y = (row + 1) * self.cell_size
            if row % 2 == 0: # Square at row, V-Rect at row+1
                is_large = (row // 2 + col // 2) % 2 == 0
                m = self.get_margin(row, col)
                BL = (x, y + self.cell_size) if is_large else (x + m, y + self.cell_size - m)
                
                m_top = self.get_margin(row, col)
                top_is_large = is_large
                TL_next = (x + m_top, next_y) if top_is_large else (x + m_top, next_y + m_top)
                
                self.draw_solid_line(dwg, BL, TL_next)
            else: # V-Rect at row, Square at row+1
                m_bottom = self.get_margin(row + 1, col)
                bottom_is_large = ((row + 1) // 2 + col // 2) % 2 == 0
                BL = (x + m_bottom, y + self.cell_size) if bottom_is_large else (x + m_bottom, y + self.cell_size - m_bottom)
                
                is_large_next = bottom_is_large
                TL_next = (x, next_y) if is_large_next else (x + m_bottom, next_y + m_bottom)
                
                self.draw_solid_line(dwg, BL, TL_next)

        # Right boundary (col = self.cols - 1)
        col = self.cols - 1
        x_right = col * self.cell_size + self.cell_size
        for row in range(self.rows - 1):
            y = row * self.cell_size
            next_y = (row + 1) * self.cell_size
            if row % 2 == 0: # Square at row, V-Rect at row+1
                is_large = (row // 2 + col // 2) % 2 == 0
                m = self.get_margin(row, col)
                BR = (x_right, y + self.cell_size) if is_large else (x_right - m, y + self.cell_size - m)
                
                m_top = self.get_margin(row, col)
                top_is_large = is_large
                TR_next = (x_right - m_top, next_y) if top_is_large else (x_right - m_top, next_y + m_top)
                
                self.draw_solid_line(dwg, BR, TR_next)
            else: # V-Rect at row, Square at row+1
                m_bottom = self.get_margin(row + 1, col)
                bottom_is_large = ((row + 1) // 2 + col // 2) % 2 == 0
                BR = (x_right - m_bottom, y + self.cell_size) if bottom_is_large else (x_right - m_bottom, y + self.cell_size - m_bottom)
                
                is_large_next = bottom_is_large
                TR_next = (x_right, next_y) if is_large_next else (x_right - m_bottom, next_y + m_bottom)
                
                self.draw_solid_line(dwg, BR, TR_next)

    def _line_intersection(self, p1, p2, p3, p4):
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3
        x4, y4 = p4
        
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denom) < 1e-8:
            return (x1, y1)
        
        px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denom
        py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denom
        return (px, py)

    def _draw_red_layer(self, dwg):
        # 1. Red Outer Perimeter
        points = []

        # Top Boundary
        row = 0
        y = 0
        for col in range(self.cols):
            x = col * self.cell_size
            if col % 2 == 0:
                m = self.get_margin(row, col)
                points.append((x + m, y + m))
                points.append((x + self.cell_size - m, y + m))
            else:
                m_left = self.get_margin(row, col - 1)
                m_right = self.get_margin(row, col + 1)
                points.append((x + m_left, y + m_left))
                points.append((x + self.cell_size - m_right, y + m_right))

        # Right Boundary
        col = self.cols - 1
        x_right = col * self.cell_size + self.cell_size
        for row in range(self.rows):
            y = row * self.cell_size
            if row % 2 == 0:
                m = self.get_margin(row, col)
                points.append((x_right - m, y + m))
                points.append((x_right - m, y + self.cell_size - m))
            else:
                m_top = self.get_margin(row - 1, col)
                m_bottom = self.get_margin(row + 1, col)
                points.append((x_right - m_top, y + m_top))
                points.append((x_right - m_bottom, y + self.cell_size - m_bottom))

        # Bottom Boundary
        row = self.rows - 1
        y_bottom = row * self.cell_size + self.cell_size
        for col in range(self.cols - 1, -1, -1):
            x = col * self.cell_size
            if col % 2 == 0:
                m = self.get_margin(row, col)
                points.append((x + self.cell_size - m, y_bottom - m))
                points.append((x + m, y_bottom - m))
            else:
                m_left = self.get_margin(row, col - 1)
                m_right = self.get_margin(row, col + 1)
                points.append((x + self.cell_size - m_right, y_bottom - m_right))
                points.append((x + m_left, y_bottom - m_left))

        # Left Boundary
        col = 0
        x = 0
        for row in range(self.rows - 1, -1, -1):
            y = row * self.cell_size
            if row % 2 == 0:
                m = self.get_margin(row, col)
                points.append((x + m, y + self.cell_size - m))
                points.append((x + m, y + m))
            else:
                m_top = self.get_margin(row - 1, col)
                m_bottom = self.get_margin(row + 1, col)
                points.append((x + m_bottom, y + self.cell_size - m_bottom))
                points.append((x + m_top, y + m_top))

        dwg.add(dwg.polygon(points=points, **self.red_stroke_style))

        # 2. Red Cutouts at X-Tabs
        for row in range(self.rows):
            for col in range(self.cols):
                if row % 2 != 0 and col % 2 != 0:
                    self._draw_red_cutout(dwg, col * self.cell_size, row * self.cell_size, row, col)

    def _draw_red_cutout(self, dwg, x, y, row, col):
        is_tl_large = ((row - 1) // 2 + (col - 1) // 2) % 2 == 0
        is_tr_large = ((row - 1) // 2 + (col + 1) // 2) % 2 == 0
        is_bl_large = ((row + 1) // 2 + (col - 1) // 2) % 2 == 0
        is_br_large = ((row + 1) // 2 + (col + 1) // 2) % 2 == 0

        m_tl = self.get_margin(row - 1, col - 1)
        m_tr = self.get_margin(row - 1, col + 1)
        m_bl = self.get_margin(row + 1, col - 1)
        m_br = self.get_margin(row + 1, col + 1)

        # Top line points
        P_T1 = (x, y - m_tl) if is_tl_large else (x + m_tl, y - m_tl)
        P_T2 = (x + self.cell_size - m_tr, y - m_tr) if is_tl_large else (x + self.cell_size, y - m_tr)
        
        # Bottom line points
        P_B1 = (x, y + self.cell_size + m_bl) if is_bl_large else (x + m_bl, y + self.cell_size + m_bl)
        P_B2 = (x + self.cell_size - m_br, y + self.cell_size + m_br) if is_bl_large else (x + self.cell_size, y + self.cell_size + m_br)
        
        # Left line points
        P_L1 = (x - m_tl, y) if is_tl_large else (x - m_tl, y + m_tl)
        P_L2 = (x - m_bl, y + self.cell_size - m_bl) if is_tl_large else (x - m_bl, y + self.cell_size)
        
        # Right line points
        P_R1 = (x + self.cell_size + m_tr, y) if is_tr_large else (x + self.cell_size + m_tr, y + m_tr)
        P_R2 = (x + self.cell_size + m_br, y + self.cell_size - m_br) if is_tr_large else (x + self.cell_size + m_br, y + self.cell_size)

        v_tl = self._line_intersection(P_T1, P_T2, P_L1, P_L2)
        v_tr = self._line_intersection(P_T1, P_T2, P_R1, P_R2)
        v_bl = self._line_intersection(P_B1, P_B2, P_L1, P_L2)
        v_br = self._line_intersection(P_B1, P_B2, P_R1, P_R2)

        dwg.add(dwg.polygon(points=[v_tl, v_tr, v_br, v_bl], **self.red_stroke_style))


def get_next_array_number(folder="SVGs"):
    if not os.path.exists(folder):
        os.makedirs(folder)
        return 1

    max_number = 0
    pattern = r"Array_(\d+)_2_layer"

    for filename in os.listdir(folder):
        match = re.search(pattern, filename)
        if match:
            number = int(match.group(1))
            max_number = max(max_number, number)

    return max_number + 1

def main():
    GRID_COLS = 7
    GRID_ROWS = 9
    CELL_SIZE = 15.0
    
    # Margin settings
    MIN_MARGIN = 0.5
    MAX_MARGIN = 1.5
    
    # Tab width scales with margin so it doesn't intersect
    MIN_TAB_WIDTH = 1.0
    MAX_TAB_WIDTH = 2.0  
    
    # Gap size for the micro-joints (in mm)
    BRIDGE_SIZE = 0.5     

    next_number = get_next_array_number()
    output_filename = f"SVGs/Array_{next_number}_2_layer.svg"

    print(f"Generating {output_filename} with dual layer support...")

    tabbed_grid = VariableTabbedGrid(
        output_filename, 
        GRID_COLS, 
        GRID_ROWS, 
        CELL_SIZE, 
        MIN_MARGIN, 
        MAX_MARGIN, 
        MIN_TAB_WIDTH, 
        MAX_TAB_WIDTH, 
        BRIDGE_SIZE
    )
    tabbed_grid.generate()

    print(f"Complete! Created {output_filename}")

if __name__ == "__main__":
    main()
