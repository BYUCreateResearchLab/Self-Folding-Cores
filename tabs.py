import svgwrite
import math

def create_tabbed_parametric_grid(filename, cols, rows, cell_size, margin, tab_width):
    canvas_width = cols * cell_size
    canvas_height = rows * cell_size

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
                    dwg.add(dwg.rect(insert=(x, y), size=(large_sq_size, large_sq_size), **stroke_style))
                else:
                    dwg.add(dwg.rect(insert=(x + margin, y + margin), size=(small_sq_size, small_sq_size), **stroke_style))

            # 2. Horizontal Rectangles (Even Row, Odd Col)
            elif row % 2 == 0 and col % 2 != 0:
                left_is_large = (row // 2 + (col - 1) // 2) % 2 == 0
                if left_is_large:
                    path_d = f"M {x} {y + margin} L {x + rect_length} {y + margin} L {x + rect_length} {y + margin + rect_width} L {x} {y + margin + rect_width}"
                    dwg.add(dwg.path(d=path_d, **stroke_style))
                else:
                    path_d = f"M {x + cell_size} {y + margin} L {x + margin} {y + margin} L {x + margin} {y + margin + rect_width} L {x + cell_size} {y + margin + rect_width}"
                    dwg.add(dwg.path(d=path_d, **stroke_style))

            # 3. Vertical Rectangles (Odd Row, Even Col)
            elif row % 2 != 0 and col % 2 == 0:
                top_is_large = ((row - 1) // 2 + col // 2) % 2 == 0
                if top_is_large:
                    path_d = f"M {x + margin} {y} L {x + margin} {y + rect_length} L {x + margin + rect_width} {y + rect_length} L {x + margin + rect_width} {y}"
                    dwg.add(dwg.path(d=path_d, **stroke_style))
                else:
                    path_d = f"M {x + margin} {y + cell_size} L {x + margin} {y + margin} L {x + margin + rect_width} {y + margin} L {x + margin + rect_width} {y + cell_size}"
                    dwg.add(dwg.path(d=path_d, **stroke_style))

            # 4. Alternating Straight-Line Tabs (Odd Row, Odd Col)
            elif row % 2 != 0 and col % 2 != 0:
                r_gap = row // 2
                c_gap = col // 2
                
                is_tl_large = (r_gap + c_gap) % 2 == 0
                is_tr_large = not is_tl_large
                
                C = tab_width / math.sqrt(2)
                
                if (r_gap + c_gap) % 2 == 0:
                    # Draw \ (Top-Left to Bottom-Right)
                    tl_x = x if is_tl_large else x - margin
                    tl_y = y if is_tl_large else y - margin
                    br_x = x + cell_size if is_tl_large else x + cell_size + margin
                    br_y = y + cell_size if is_tl_large else y + cell_size + margin
                    
                    dwg.add(dwg.line(start=(tl_x + C, tl_y), end=(br_x, br_y - C), **stroke_style))
                    dwg.add(dwg.line(start=(tl_x, tl_y + C), end=(br_x - C, br_y), **stroke_style))
                else:
                    # Draw / (Top-Right to Bottom-Left)
                    tr_x = x + cell_size if is_tr_large else x + cell_size + margin
                    tr_y = y if is_tr_large else y - margin
                    bl_x = x if is_tr_large else x - margin
                    bl_y = y + cell_size if is_tr_large else y + cell_size + margin
                    
                    dwg.add(dwg.line(start=(tr_x - C, tr_y), end=(bl_x, bl_y - C), **stroke_style))
                    dwg.add(dwg.line(start=(tr_x, tr_y + C), end=(bl_x + C, bl_y), **stroke_style))

    dwg.save()

if __name__ == "__main__":
    create_tabbed_parametric_grid("origami_tabs_straight.svg", 11, 11, 15.0, 1.5, 2.0)