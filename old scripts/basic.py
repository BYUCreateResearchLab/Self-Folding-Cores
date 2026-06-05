import svgwrite

def create_grid(filename, cols, rows, cell_size, margin):
    canvas_width = cols * cell_size
    canvas_height = rows * cell_size

    print(f"Generating optimized SVG: {canvas_width}mm x {canvas_height}mm")

    dwg = svgwrite.Drawing(
        filename, 
        size=(f"{canvas_width}mm", f"{canvas_height}mm"),
        viewBox=f"0 0 {canvas_width} {canvas_height}"
    )

    stroke_style = {'stroke': 'blue', 'stroke_width': 0.1, 'fill': 'none'}

    large_sq_size = cell_size
    small_sq_size = cell_size - (2 * margin)
    rect_length = cell_size - margin
    rect_width = small_sq_size

    for row in range(rows):
        for col in range(cols):
            x = col * cell_size
            y = row * cell_size

            # 1. Intersections (Even Row, Even Col)
            if row % 2 == 0 and col % 2 == 0:
                is_large_square = (row // 2 + col // 2) % 2 == 0
                
                if is_large_square:
                    # Large squares remain closed rectangles
                    dwg.add(dwg.rect(insert=(x, y), size=(large_sq_size, large_sq_size), **stroke_style))
                else:
                    # Small squares remain closed rectangles
                    dwg.add(dwg.rect(insert=(x + margin, y + margin), size=(small_sq_size, small_sq_size), **stroke_style))

            # 2. Horizontal Rectangles (Even Row, Odd Col)
            elif row % 2 == 0 and col % 2 != 0:
                left_is_large = (row // 2 + (col - 1) // 2) % 2 == 0
                
                if left_is_large:
                    # Flush Left: Omit left line. Draw Top -> Right -> Bottom
                    path_d = f"M {x} {y + margin} L {x + rect_length} {y + margin} L {x + rect_length} {y + margin + rect_width} L {x} {y + margin + rect_width}"
                    dwg.add(dwg.path(d=path_d, **stroke_style))
                else:
                    # Flush Right: Omit right line. Draw Top -> Left -> Bottom
                    path_d = f"M {x + cell_size} {y + margin} L {x + margin} {y + margin} L {x + margin} {y + margin + rect_width} L {x + cell_size} {y + margin + rect_width}"
                    dwg.add(dwg.path(d=path_d, **stroke_style))

            # 3. Vertical Rectangles (Odd Row, Even Col)
            elif row % 2 != 0 and col % 2 == 0:
                top_is_large = ((row - 1) // 2 + col // 2) % 2 == 0
                
                if top_is_large:
                    # Flush Top: Omit top line. Draw Left -> Bottom -> Right
                    path_d = f"M {x + margin} {y} L {x + margin} {y + rect_length} L {x + margin + rect_width} {y + rect_length} L {x + margin + rect_width} {y}"
                    dwg.add(dwg.path(d=path_d, **stroke_style))
                else:
                    # Flush Bottom: Omit bottom line. Draw Left -> Top -> Right
                    path_d = f"M {x + margin} {y + cell_size} L {x + margin} {y + margin} L {x + margin + rect_width} {y + margin} L {x + margin + rect_width} {y + cell_size}"
                    dwg.add(dwg.path(d=path_d, **stroke_style))

            # 4. Empty Spaces (Odd Row, Odd Col)
            elif row % 2 != 0 and col % 2 != 0:
                pass 

    dwg.save()
    print(f"Successfully saved optimized file to {filename}")

if __name__ == "__main__":
    OUTPUT_FILE = "SVGs/origami_parametric.svg"

    # --- ADJUSTABLE VARIABLES ---
    GRID_COLS = 11      # Number of cells wide (keep odd for clean borders)
    GRID_ROWS = 11      # Number of cells high (keep odd for clean borders)
    CELL_SIZE = 7.5    # Base size of the grid cell in mm
    MARGIN = 0.75        # Gap from the edge (Total gap between pieces = 2x this value)

    create_grid(OUTPUT_FILE, GRID_COLS, GRID_ROWS, CELL_SIZE, MARGIN)