import svgwrite
import math
import os
import re

class CurvedGeometryGenerator:
    def __init__(self, filename, cols, rows, cell_size, min_margin, max_margin):
        self.filename = filename
        self.cols = cols
        self.rows = rows
        self.cell_size = cell_size
        self.min_margin = min_margin
        self.max_margin = max_margin
        self.canvas_width = cols * cell_size
        self.canvas_height = rows * cell_size
        self.stroke_style = {'stroke': 'white', 'stroke_width': 0.1, 'fill': 'none'}

    def get_margin(self, row, col):
        """
        Creates a gradient from min_margin to max_margin.
        Currently, this varies across the columns (X-axis) to induce a cylindrical bend.
        You can easily modify this math to create domes (radial) or saddles!
        """
        if self.cols <= 1:
            return self.min_margin
            
        # Linear gradient based on column position
        progress = col / (self.cols - 1)
        return self.min_margin + (self.max_margin - self.min_margin) * progress

    def create_drawing(self):
        return svgwrite.Drawing(
            self.filename,
            size=(f"{self.canvas_width}mm", f"{self.canvas_height}mm"),
            viewBox=f"0 0 {self.canvas_width} {self.canvas_height}"
        )

    def save_drawing(self, dwg):
        dwg.save()
        print(f"Successfully saved to {self.filename}")


class CurvedTabbedGrid(CurvedGeometryGenerator):
    def __init__(self, filename, cols, rows, cell_size, min_margin, max_margin, tab_width):
        super().__init__(filename, cols, rows, cell_size, min_margin, max_margin)
        self.tab_width = tab_width

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
                        dwg.add(dwg.rect(insert=(x, y), size=(self.cell_size, self.cell_size), **self.stroke_style))
                    else:
                        size = self.cell_size - (2 * m)
                        dwg.add(dwg.rect(insert=(x + m, y + m), size=(size, size), **self.stroke_style))

                # 2. Horizontal Rectangles (Even Row, Odd Col)
                elif row % 2 == 0 and col % 2 != 0:
                    # Look up margins of the left and right connecting nodes
                    m_left = self.get_margin(row, col - 1)
                    m_right = self.get_margin(row, col + 1)
                    
                    # By tapering the Y coordinates based on left/right margins, we keep a closed geometry
                    y1_L = y + m_left
                    y2_L = y + self.cell_size - m_left
                    y1_R = y + m_right
                    y2_R = y + self.cell_size - m_right

                    left_is_large = (row // 2 + (col - 1) // 2) % 2 == 0
                    if left_is_large:
                        end_x = x + self.cell_size - m_right
                        path_d = f"M {x} {y1_L} L {end_x} {y1_R} L {end_x} {y2_R} L {x} {y2_L} Z"
                        dwg.add(dwg.path(d=path_d, **self.stroke_style))
                    else:
                        start_x = x + m_left
                        end_x = x + self.cell_size
                        path_d = f"M {end_x} {y1_R} L {start_x} {y1_L} L {start_x} {y2_L} L {end_x} {y2_R} Z"
                        dwg.add(dwg.path(d=path_d, **self.stroke_style))

                # 3. Vertical Rectangles (Odd Row, Even Col)
                elif row % 2 != 0 and col % 2 == 0:
                    # Look up margins of the top and bottom connecting nodes
                    m_top = self.get_margin(row - 1, col)
                    m_bottom = self.get_margin(row + 1, col)

                    # Taper the X coordinates
                    x1_T = x + m_top
                    x2_T = x + self.cell_size - m_top
                    x1_B = x + m_bottom
                    x2_B = x + self.cell_size - m_bottom

                    top_is_large = ((row - 1) // 2 + col // 2) % 2 == 0
                    if top_is_large:
                        end_y = y + self.cell_size - m_bottom
                        path_d = f"M {x1_T} {y} L {x1_B} {end_y} L {x2_B} {end_y} L {x2_T} {y} Z"
                        dwg.add(dwg.path(d=path_d, **self.stroke_style))
                    else:
                        start_y = y + m_top
                        end_y = y + self.cell_size
                        path_d = f"M {x1_B} {end_y} L {x1_T} {start_y} L {x2_T} {start_y} L {x2_B} {end_y} Z"
                        dwg.add(dwg.path(d=path_d, **self.stroke_style))

                # 4. Alternating X-Tab Pattern (Odd Row, Odd Col)
                elif row % 2 != 0 and col % 2 != 0:
                    self._draw_x_tabs(dwg, x, y, row, col)

        self.save_drawing(dwg)

    def _draw_x_tabs(self, dwg, x, y, row, col):
        d = self.tab_width / math.sqrt(2)

        # Determine if the 4 adjacent corner nodes are large or small
        is_tl_large = ((row - 1) // 2 + (col - 1) // 2) % 2 == 0
        is_tr_large = ((row - 1) // 2 + (col + 1) // 2) % 2 == 0
        is_bl_large = ((row + 1) // 2 + (col - 1) // 2) % 2 == 0
        is_br_large = ((row + 1) // 2 + (col + 1) // 2) % 2 == 0

        # Fetch the exact local margin of each of the 4 adjacent nodes
        m_tl = self.get_margin(row - 1, col - 1)
        m_tr = self.get_margin(row - 1, col + 1)
        m_bl = self.get_margin(row + 1, col - 1)
        m_br = self.get_margin(row + 1, col + 1)

        # Map the X/Y coordinates to intersect perfectly with the modified nodes
        tl_x = x if is_tl_large else x - m_tl
        tl_y = y if is_tl_large else y - m_tl

        tr_x = x + self.cell_size if is_tr_large else x + self.cell_size + m_tr
        tr_y = y if is_tr_large else y - m_tr

        bl_x = x if is_bl_large else x - m_bl
        bl_y = y + self.cell_size if is_bl_large else y + self.cell_size + m_bl

        br_x = x + self.cell_size if is_br_large else x + self.cell_size + m_br
        br_y = y + self.cell_size if is_br_large else y + self.cell_size + m_br

        # Center point for the hollow diamond
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
    pattern = r"Array_(\d+)(_curved)?\.svg"

    for filename in os.listdir(folder):
        match = re.match(pattern, filename)
        if match:
            number = int(match.group(1))
            max_number = max(max_number, number)

    return max_number + 1

def main():
    GRID_COLS = 15  # Increased slightly to make gradient more noticeable
    GRID_ROWS = 3
    CELL_SIZE = 15.0
    MIN_MARGIN = 1.0  # Tighter gap on one side
    MAX_MARGIN = 3.5  # Wider gap on the other side
    TAB_WIDTH = 2.0

    next_number = get_next_array_number()
    output_filename = f"SVGs/Array_{next_number}_curved.svg"

    print(f"Generating {output_filename} with variable margins...")

    tabbed_grid = CurvedTabbedGrid(output_filename, GRID_COLS, GRID_ROWS, CELL_SIZE, MIN_MARGIN, MAX_MARGIN, TAB_WIDTH)
    tabbed_grid.generate()

    print(f"Complete! Created {output_filename}")

if __name__ == "__main__":
    main()
