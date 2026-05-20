import svgwrite
import math
import os
import re

class GeometryGenerator:
    def __init__(self, filename, cols, rows, cell_size, margin):
        self.filename = filename
        self.cols = cols
        self.rows = rows
        self.cell_size = cell_size
        self.margin = margin
        self.canvas_width = cols * cell_size
        self.canvas_height = rows * cell_size
        self.stroke_style = {'stroke': 'blue', 'stroke_width': 0.1, 'fill': 'none'}

        self.large_sq_size = cell_size
        self.small_sq_size = cell_size - (2 * margin)
        self.rect_length = cell_size - margin
        self.rect_width = self.small_sq_size

    def create_drawing(self):
        return svgwrite.Drawing(
            self.filename,
            size=(f"{self.canvas_width}mm", f"{self.canvas_height}mm"),
            viewBox=f"0 0 {self.canvas_width} {self.canvas_height}"
        )

    def save_drawing(self, dwg):
        dwg.save()
        print(f"Successfully saved to {self.filename}")

class SquareGrid(GeometryGenerator):
    def generate(self):
        dwg = self.create_drawing()

        for row in range(self.rows):
            for col in range(self.cols):
                x = col * self.cell_size
                y = row * self.cell_size

                # 1. Intersections (Even Row, Even Col)
                if row % 2 == 0 and col % 2 == 0:
                    is_large_square = (row // 2 + col // 2) % 2 == 0
                    if is_large_square:
                        dwg.add(dwg.rect(insert=(x, y), size=(self.large_sq_size, self.large_sq_size), **self.stroke_style))
                    else:
                        dwg.add(dwg.rect(insert=(x + self.margin, y + self.margin), size=(self.small_sq_size, self.small_sq_size), **self.stroke_style))

                # 2. Horizontal Rectangles (Even Row, Odd Col)
                elif row % 2 == 0 and col % 2 != 0:
                    left_is_large = (row // 2 + (col - 1) // 2) % 2 == 0
                    if left_is_large:
                        path_d = f"M {x} {y + self.margin} L {x + self.rect_length} {y + self.margin} L {x + self.rect_length} {y + self.margin + self.rect_width} L {x} {y + self.margin + self.rect_width}"
                        dwg.add(dwg.path(d=path_d, **self.stroke_style))
                    else:
                        path_d = f"M {x + self.cell_size} {y + self.margin} L {x + self.margin} {y + self.margin} L {x + self.margin} {y + self.margin + self.rect_width} L {x + self.cell_size} {y + self.margin + self.rect_width}"
                        dwg.add(dwg.path(d=path_d, **self.stroke_style))

                # 3. Vertical Rectangles (Odd Row, Even Col)
                elif row % 2 != 0 and col % 2 == 0:
                    top_is_large = ((row - 1) // 2 + col // 2) % 2 == 0
                    if top_is_large:
                        path_d = f"M {x + self.margin} {y} L {x + self.margin} {y + self.rect_length} L {x + self.margin + self.rect_width} {y + self.rect_length} L {x + self.margin + self.rect_width} {y}"
                        dwg.add(dwg.path(d=path_d, **self.stroke_style))
                    else:
                        path_d = f"M {x + self.margin} {y + self.cell_size} L {x + self.margin} {y + self.margin} L {x + self.margin + self.rect_width} {y + self.margin} L {x + self.margin + self.rect_width} {y + self.cell_size}"
                        dwg.add(dwg.path(d=path_d, **self.stroke_style))

                # 4. Empty Spaces (Odd Row, Odd Col)
                elif row % 2 != 0 and col % 2 != 0:
                    pass

        self.save_drawing(dwg)

class TabbedGrid(GeometryGenerator):
    def __init__(self, filename, cols, rows, cell_size, margin, tab_width):
        super().__init__(filename, cols, rows, cell_size, margin)
        self.tab_width = tab_width

    def generate(self):
        dwg = self.create_drawing()

        for row in range(self.rows):
            for col in range(self.cols):
                x = col * self.cell_size
                y = row * self.cell_size

                # 1. Intersections (Even Row, Even Col)
                if row % 2 == 0 and col % 2 == 0:
                    is_large_square = (row // 2 + col // 2) % 2 == 0
                    if is_large_square:
                        dwg.add(dwg.rect(insert=(x, y), size=(self.large_sq_size, self.large_sq_size), **self.stroke_style))
                    else:
                        dwg.add(dwg.rect(insert=(x + self.margin, y + self.margin), size=(self.small_sq_size, self.small_sq_size), **self.stroke_style))

                # 2. Horizontal Rectangles (Even Row, Odd Col)
                elif row % 2 == 0 and col % 2 != 0:
                    left_is_large = (row // 2 + (col - 1) // 2) % 2 == 0
                    if left_is_large:
                        path_d = f"M {x} {y + self.margin} L {x + self.rect_length} {y + self.margin} L {x + self.rect_length} {y + self.margin + self.rect_width} L {x} {y + self.margin + self.rect_width}"
                        dwg.add(dwg.path(d=path_d, **self.stroke_style))
                    else:
                        path_d = f"M {x + self.cell_size} {y + self.margin} L {x + self.margin} {y + self.margin} L {x + self.margin} {y + self.margin + self.rect_width} L {x + self.cell_size} {y + self.margin + self.rect_width}"
                        dwg.add(dwg.path(d=path_d, **self.stroke_style))

                # 3. Vertical Rectangles (Odd Row, Even Col)
                elif row % 2 != 0 and col % 2 == 0:
                    top_is_large = ((row - 1) // 2 + col // 2) % 2 == 0
                    if top_is_large:
                        path_d = f"M {x + self.margin} {y} L {x + self.margin} {y + self.rect_length} L {x + self.margin + self.rect_width} {y + self.rect_length} L {x + self.margin + self.rect_width} {y}"
                        dwg.add(dwg.path(d=path_d, **self.stroke_style))
                    else:
                        path_d = f"M {x + self.margin} {y + self.cell_size} L {x + self.margin} {y + self.margin} L {x + self.margin + self.rect_width} {y + self.margin} L {x + self.margin + self.rect_width} {y + self.cell_size}"
                        dwg.add(dwg.path(d=path_d, **self.stroke_style))

                # 4. Alternating X-Tab Pattern (Odd Row, Odd Col)
                elif row % 2 != 0 and col % 2 != 0:
                    self._draw_x_tabs(dwg, x, y)

        self.save_drawing(dwg)
    def _draw_x_tabs(self, dwg, x, y):
        # Correctly derive X/Y offsets for a perpendicular channel of `tab_width`
        d = self.tab_width / math.sqrt(2)

        # Derive current row and col to check the checkerboard pattern
        col = int(round(x / self.cell_size))
        row = int(round(y / self.cell_size))

        # Check if the 4 adjacent intersections are large or small
        is_tl_large = ((row - 1) // 2 + (col - 1) // 2) % 2 == 0
        is_tr_large = ((row - 1) // 2 + (col + 1) // 2) % 2 == 0
        is_bl_large = ((row + 1) // 2 + (col - 1) // 2) % 2 == 0
        is_br_large = ((row + 1) // 2 + (col + 1) // 2) % 2 == 0

        # Calculate exact bounding corners of the actual drawn squares.
        # If small, we push OUTWARD (- margin for left/top, + margin for right/bottom)
        tl_x = x if is_tl_large else x - self.margin
        tl_y = y if is_tl_large else y - self.margin

        tr_x = x + self.cell_size if is_tr_large else x + self.cell_size + self.margin
        tr_y = y if is_tr_large else y - self.margin

        bl_x = x if is_bl_large else x - self.margin
        bl_y = y + self.cell_size if is_bl_large else y + self.cell_size + self.margin

        br_x = x + self.cell_size if is_br_large else x + self.cell_size + self.margin
        br_y = y + self.cell_size if is_br_large else y + self.cell_size + self.margin

        # Center point for the hollow diamond
        cx = x + self.cell_size / 2
        cy = y + self.cell_size / 2

        # --- Two parallel lines at 45° (\) ---
        
        # Upper line (Line A): From Top-Left right-edge down to center Top-point
        dwg.add(dwg.line(start=(tl_x, tl_y - d), end=(cx, cy - d), **self.stroke_style))
        # From center Right-point down to Bottom-Right top-edge
        dwg.add(dwg.line(start=(cx + d, cy), end=(br_x + d, br_y), **self.stroke_style))
        
        # Lower line (Line B): From Top-Left bottom-edge down to center Left-point
        dwg.add(dwg.line(start=(tl_x - d, tl_y), end=(cx - d, cy), **self.stroke_style))
        # From center Bottom-point down to Bottom-Right left-edge
        dwg.add(dwg.line(start=(cx, cy + d), end=(br_x, br_y + d), **self.stroke_style))


        # --- Two parallel lines at -45° (/) ---
        # THE FIX: X and Y offsets correctly mapped to the Top/Left/Right/Bottom edges
        
        # Upper line (Line C): From Bottom-Left top-edge up to center Left-point
        dwg.add(dwg.line(start=(bl_x - d, bl_y), end=(cx - d, cy), **self.stroke_style))
        # From center Top-point up to Top-Right left-edge
        dwg.add(dwg.line(start=(cx, cy - d), end=(tr_x, tr_y - d), **self.stroke_style))
        
        # Lower line (Line D): From Bottom-Left right-edge up to center Bottom-point
        dwg.add(dwg.line(start=(bl_x, bl_y + d), end=(cx, cy + d), **self.stroke_style))
        # From center Right-point up to Top-Right bottom-edge
        dwg.add(dwg.line(start=(cx + d, cy), end=(tr_x + d, tr_y), **self.stroke_style))
        
def get_next_array_number(folder="SVGs"):
    """Get the next array number based on existing files in the folder."""
    if not os.path.exists(folder):
        os.makedirs(folder)
        return 1

    max_number = 0
    pattern = r"Array_(\d+)\.svg"

    for filename in os.listdir(folder):
        match = re.match(pattern, filename)
        if match:
            number = int(match.group(1))
            max_number = max(max_number, number)

    return max_number + 1

def main():
    GRID_COLS = 11
    GRID_ROWS = 11
    CELL_SIZE = 15.0
    MARGIN = 1.5
    TAB_WIDTH = 1.0

    next_number = get_next_array_number()
    output_filename = f"SVGs/Array_{next_number}.svg"

    print(f"Generating {output_filename}...")

    # Generate tabbed grid with all geometry
    tabbed_grid = TabbedGrid(output_filename, GRID_COLS, GRID_ROWS, CELL_SIZE, MARGIN, TAB_WIDTH)
    tabbed_grid.generate()

    print(f"Complete! Created {output_filename}")

if __name__ == "__main__":
    main()