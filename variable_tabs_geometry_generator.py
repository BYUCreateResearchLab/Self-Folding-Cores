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


def get_next_array_number(folder="SVGs"):
    if not os.path.exists(folder):
        os.makedirs(folder)
        return 1

    max_number = 0
    pattern = r"Array_(\d+)"

    for filename in os.listdir(folder):
        match = re.search(pattern, filename)
        if match:
            number = int(match.group(1))
            max_number = max(max_number, number)

    return max_number + 1

def main():
    GRID_COLS = 15
    GRID_ROWS = 11
    CELL_SIZE = 15.0
    
    # Margin settings
    MIN_MARGIN = 1.0
    MAX_MARGIN = 3.5
    
    # Tab width scales with margin so it doesn't intersect
    MIN_TAB_WIDTH = 1.0 
    MAX_TAB_WIDTH = 2.0  
    
    # Gap size for the micro-joints (in mm)
    BRIDGE_SIZE = 0.5     

    next_number = get_next_array_number()
    output_filename = f"SVGs/Array_{next_number}_variable_tabs.svg"

    print(f"Generating {output_filename} with advanced bridge placement...")

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
