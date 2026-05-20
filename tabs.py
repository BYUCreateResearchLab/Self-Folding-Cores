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

            # 4. Alternating X-Tab Pattern (Odd Row, Odd Col)
            elif row % 2 != 0 and col % 2 != 0:
                C = tab_width / math.sqrt(2)
                trim = tab_width / math.sqrt(2)

                # Big square coordinates
                big_tl_x, big_tl_y = x, y
                big_br_x, big_br_y = x + cell_size, y + cell_size
                big_tr_x, big_tr_y = x + cell_size, y
                big_bl_x, big_bl_y = x, y + cell_size

                # Small square coordinates
                small_tl_x, small_tl_y = x + margin, y + margin
                small_br_x, small_br_y = x + cell_size - margin, y + cell_size - margin
                small_tr_x, small_tr_y = x + cell_size - margin, y + margin
                small_bl_x, small_bl_y = x + margin, y + cell_size - margin

                # Diagonal 1: Big square \ and Small square /
                # Two parallel lines for big square diagonal (top-left to bottom-right)
                # Line A: trim from both ends by moving toward center
                dwg.add(dwg.line(start=(big_tl_x + C + trim, big_tl_y + trim),
                                end=(big_br_x - trim, big_br_y - C - trim), **stroke_style))
                # Line B: trim from both ends by moving toward center
                dwg.add(dwg.line(start=(big_tl_x + trim, big_tl_y + C + trim),
                                end=(big_br_x - C - trim, big_br_y - trim), **stroke_style))

                # Two parallel lines for small square diagonal (top-right to bottom-left)
                # Line C: trim from both ends (slope is -1)
                dwg.add(dwg.line(start=(small_tr_x - C - trim, small_tr_y + trim),
                                end=(small_bl_x + trim, small_bl_y - C - trim), **stroke_style))
                # Line D: trim from both ends (slope is -1)
                dwg.add(dwg.line(start=(small_tr_x - trim, small_tr_y + C + trim),
                                end=(small_bl_x + C + trim, small_bl_y - trim), **stroke_style))

    dwg.save()

if __name__ == "__main__":
    create_tabbed_parametric_grid("SVGs/origami_tabs_straight.svg", 11, 11, 15.0, 1.5, 2.0)