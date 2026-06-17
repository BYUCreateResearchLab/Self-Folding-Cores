import streamlit as st
import base64
import importlib
import geometry
importlib.reload(geometry)
from geometry import VariableTabbedGrid

def set_tess_pos(pos):
    st.session_state.tessellation_position = pos

# Trigger Streamlit to reload to pick up geometry.py changes
st.set_page_config(layout="wide", page_title="Self-Folding Cores UI")

layout_modes = ["Overlaid", "Side-by-Side", "Stacked Vertically"]
if 'layout_mode_idx' not in st.session_state:
    st.session_state.layout_mode_idx = 0

st.sidebar.title("Parameters")

st.sidebar.subheader("Grid Dimensions")
cols = st.sidebar.number_input("Columns", min_value=1, max_value=50, value=15)
rows = st.sidebar.number_input("Rows", min_value=1, max_value=50, value=11)
start_cell_size = st.sidebar.number_input("Start Cell Size (mm)", min_value=1.0, max_value=100.0, value=15.0)

for state_key, default_value in [
    ("show_base", True),
    ("show_top", True),
    ("show_red", True),
    ("show_grid", True),
    ("show_sheet", True),
]:
    if state_key not in st.session_state:
        st.session_state[state_key] = default_value

show_base = st.session_state.show_base
show_top = st.session_state.show_top
show_red = st.session_state.show_red
show_grid = st.session_state.show_grid
show_sheet = st.session_state.show_sheet

align_x = st.session_state.get("align_x", 5.0)
align_y = st.session_state.get("align_y", 5.0)

end_cell_size_x = st.session_state.get("end_cell_size_x", 15.0)
end_cell_size_y = st.session_state.get("end_cell_size_y", 15.0)
enable_curvature = st.sidebar.checkbox("Enable Curvature", value=False)

if enable_curvature:
    max_w = max(start_cell_size, end_cell_size_x)
    max_h = max(start_cell_size, end_cell_size_y)

    st.sidebar.subheader("Curvature")
    normal_gap_x = st.sidebar.slider("Bottom Layer Vertical Gap (mm)", 0.0, float(max_w), 3.0, 0.1)
    normal_gap_y = st.sidebar.slider("Bottom Layer Horizontal Gap (mm)", 0.0, float(max_h), 3.0, 0.1)
    alt_gap_x = st.sidebar.slider("Top Layer Vertical Gap (mm)", 0.0, float(max_w), 1.0, 0.1)
    alt_gap_y = st.sidebar.slider("Top Layer Horizontal Gap (mm)", 0.0, float(max_h), 1.0, 0.1)

    st.sidebar.subheader("S-Curve Gap Transition")
    s_curve_axis = st.sidebar.selectbox("Transition Axis", ["X", "Y"])
    max_point = int(cols) if s_curve_axis == "X" else int(rows)
    label_point = "Transition Column" if s_curve_axis == "X" else "Transition Row"
    s_curve_point = st.sidebar.number_input(label_point, min_value=0, max_value=max_point, value=max_point // 2)
    s_curve_cells = st.sidebar.number_input("Transition Cells (Width of S-Curve)", min_value=0, max_value=max_point, value=min(3, max_point))
    max_t_gap = max_w if s_curve_axis == "X" else max_h
    s_curve_transition_gap = st.sidebar.slider("Transition Gap (mm)", 0.0, float(max_t_gap), 2.0, 0.1)
else:
    uniform_gap = st.sidebar.slider("Gap Size (mm)", 0.0, float(max(start_cell_size, end_cell_size_x, end_cell_size_y)), 3.0, 0.1)
    normal_gap_x = uniform_gap
    normal_gap_y = uniform_gap
    alt_gap_x = uniform_gap
    alt_gap_y = uniform_gap
    s_curve_axis = "None"
    s_curve_point = 0
    s_curve_cells = 0
    s_curve_transition_gap = 0.0

st.sidebar.subheader("Margins & Tabs")
bridge_size = st.sidebar.slider("Bridge Size (mm)", 0.1, 5.0, 0.8, 0.1)

st.sidebar.subheader("Gradient")
enable_gradient = st.sidebar.checkbox("Enable Gradient (Varying Cell Sizes)", key="enable_gradient", value=True)

if enable_gradient:
    end_cell_size_x = st.sidebar.number_input("End Cell Size X (Bottom-Right) (mm)", min_value=1.0, max_value=100.0, value=end_cell_size_x)
    end_cell_size_y = st.sidebar.number_input("End Cell Size Y (Top-Left) (mm)", min_value=1.0, max_value=100.0, value=end_cell_size_y)

    if end_cell_size_x != end_cell_size_y:
        st.sidebar.info("Note: To keep all grid cells as perfect squares, the X and Y end sizes must be identical. Different X and Y gradients will cause off-diagonal cells to stretch into rectangles to keep the grid connected.")

    enable_fixed_connector_length = st.sidebar.checkbox("Keep Connector Lengths Constant", key="enable_fixed_connector_length", value=False, help="Maintain constant length for connecting rectangles while allowing width to vary as trapezoids")

    if enable_fixed_connector_length:
        default_connector_length = start_cell_size / 2.0
        connector_length_mm = st.sidebar.slider("Connector Length (mm)", min_value=0.5, max_value=float(max(start_cell_size, end_cell_size_x, end_cell_size_y)), value=default_connector_length, step=0.1)
    else:
        connector_length_mm = 0.0

    max_w = max(start_cell_size, end_cell_size_x)
    max_h = max(start_cell_size, end_cell_size_y)
else:
    enable_fixed_connector_length = False
    connector_length_mm = 0.0
    max_w = start_cell_size
    max_h = start_cell_size

st.sidebar.subheader("Tessellation")
enable_tessellation = st.sidebar.checkbox("Enable Tessellation (Edge Splitting)", key="enable_tessellation", value=True)

tessellation_position = st.session_state.get("tessellation_position", 9)
tessellation_tolerance = st.session_state.get("tess_tol", 0.0)

if enable_tessellation:
    st.sidebar.write("**Tessellation Position**")
    st.sidebar.button("Normal (No modifications)", key="tess_pos_9", use_container_width=True, help="No tessellation modifications", on_click=set_tess_pos, args=(9,))
    st.sidebar.write("Select position in 3×3 grid:")
    positions = [
        (0, "Top-Left"), (1, "Top-Center"), (2, "Top-Right"),
        (3, "Middle-Left"), (4, "Center"), (5, "Middle-Right"),
        (6, "Bottom-Left"), (7, "Bottom-Center"), (8, "Bottom-Right"),
        (9, "Normal"),
    ]
    cols_small = st.sidebar.columns(3)
    for idx, (pos_idx, pos_name) in enumerate(positions[:9]):
        col_idx = idx % 3
        with cols_small[col_idx]:
            short_name = pos_name.replace("Top-", "T-").replace("Bottom-", "B-").replace("Middle-", "M-").replace("Center", "C").replace("-C", "C").replace("-Left", "L").replace("-Right", "R")
            st.button(short_name, key="tess_pos_" + str(pos_idx), use_container_width=True, help=pos_name, on_click=set_tess_pos, args=(pos_idx,))
    current_pos = st.session_state.get("tessellation_position", 9)
    st.sidebar.write("Current: " + dict(positions).get(current_pos, "Unknown"))

    st.sidebar.write("**Tessellation Adjustments**")
    tessellation_tolerance = st.sidebar.slider("Tolerance (mm)", min_value=-10.0, max_value=10.0, value=tessellation_tolerance, step=0.1, key="tess_tol", help="Positive = smaller shape (cut inward). Negative = bigger shape (cut outward).")

# Create a signature for current settings to detect changes
current_settings = (cols, rows, start_cell_size, end_cell_size_x, end_cell_size_y, normal_gap_x, normal_gap_y, alt_gap_x, alt_gap_y, bridge_size, show_base, show_top, show_red, show_grid, show_sheet, align_x, align_y, tessellation_position, tessellation_tolerance, s_curve_axis, s_curve_point, s_curve_cells, s_curve_transition_gap, enable_curvature, enable_gradient, enable_tessellation, enable_fixed_connector_length, connector_length_mm)

if 'last_settings' not in st.session_state or st.session_state.last_settings != current_settings:
    st.session_state.last_settings = current_settings

generator = VariableTabbedGrid(
    cols=int(cols),
    rows=int(rows),
    start_cell_size=float(start_cell_size),
    end_cell_size_x=float(end_cell_size_x),
    end_cell_size_y=float(end_cell_size_y),
    normal_gap_x=float(normal_gap_x) / 2.0,
    normal_gap_y=float(normal_gap_y) / 2.0,
    alt_gap_x=float(alt_gap_x) / 2.0,
    alt_gap_y=float(alt_gap_y) / 2.0,
    bridge_size=float(bridge_size),
    tessellation_position=tessellation_position,
    tessellation_tolerance=tessellation_tolerance,
    s_curve_axis=s_curve_axis,
    s_curve_point=float(s_curve_point),
    s_curve_cells=float(s_curve_cells),
    s_curve_transition_gap=float(s_curve_transition_gap) / 2.0,
    enable_gradient=enable_gradient,
    enable_tessellation=enable_tessellation,
    enable_fixed_connector_length=enable_fixed_connector_length,
    fixed_connector_length=float(connector_length_mm)
)

st.title("Tessellation Visualizer")

col1, col2 = st.columns([5, 1])

with col1:
    st.markdown("### Preview")
    layout_mode = layout_modes[st.session_state.layout_mode_idx]
    if layout_mode != "Overlaid":
        st.session_state.show_grid = False
        st.session_state.show_sheet = False
    show_grid = st.session_state.show_grid
    show_sheet = st.session_state.show_sheet

    def cycle_layout_mode():
        st.session_state.layout_mode_idx = (st.session_state.layout_mode_idx + 1) % len(layout_modes)

    st.button(f"Layout Mode: {layout_mode}", on_click=cycle_layout_mode)
    
    # Create a signature for current settings to detect changes (including layout_mode)
    current_settings = (cols, rows, start_cell_size, end_cell_size_x, end_cell_size_y, normal_gap_x, normal_gap_y, alt_gap_x, alt_gap_y, bridge_size, show_base, show_top, show_red, show_grid, show_sheet, align_x, align_y, tessellation_position, tessellation_tolerance, s_curve_axis, s_curve_point, s_curve_cells, s_curve_transition_gap, enable_curvature, layout_mode, enable_gradient, enable_tessellation)
    
    if 'last_settings' not in st.session_state or st.session_state.last_settings != current_settings:
        st.session_state.last_settings = current_settings

    # Generate SVG for preview (with grid if enabled)
    svg_str_preview = generator.generate(
        show_base=show_base,
        show_top=show_top,
        show_red=show_red,
        show_grid=show_grid,
        show_sheet=show_sheet,
        align_x=align_x,
        align_y=align_y,
        layout_mode=layout_mode
    )
    
    # Generate SVG for export (force grid off)
    svg_str_export = generator.generate(
        show_base=show_base,
        show_top=show_top,
        show_red=show_red,
        show_grid=False,
        show_sheet=show_sheet,
        align_x=align_x,
        align_y=align_y,
        layout_mode=layout_mode
    )
    
    b64 = base64.b64encode(svg_str_preview.encode('utf-8')).decode("utf-8")
    
    # CSS wrapper for panning and zooming the SVG, with drag support and zoom controls
    html = """
    <style>
        :root {
            --bg-color: #f8f9fa;
            --border-color: #ccc;
            --btn-bg: #eee;
            --btn-border: #ccc;
            --btn-text: #000;
            --text-color: #000;
        }
        @media (prefers-color-scheme: dark) {
            :root {
                --bg-color: #111;
                --border-color: #444;
                --btn-bg: #222;
                --btn-border: #444;
                --btn-text: #fff;
                --text-color: #fff;
            }
        }
        .toolbar { display: flex; gap: 12px; margin-bottom: 10px; align-items: center; color: var(--text-color); font-family: 'Source Sans Pro', sans-serif; flex-wrap: wrap; }
        .toolbar-group { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
        .toolbar button { 
            font-family: inherit; padding: 8px 14px; border: 1px solid var(--btn-border); 
            border-radius: 4px; background: var(--btn-bg); color: var(--btn-text); cursor: pointer; 
        }
        .toolbar button:hover { opacity: 0.8; }
        #draggable-preview { 
            position: relative; width: 100%; height: 85vh; overflow: hidden; 
            background-color: #ffffff; border: 1px solid var(--border-color); 
            border-radius: 5px; padding: 20px; cursor: grab; 
        }
    </style>
    <div class="toolbar">
        <div class="toolbar-group">
            <button id="zoom-in">Zoom In</button>
            <button id="zoom-out">Zoom Out</button>
            <button id="reset-view">Reset View</button>
            <button id="measure-btn">Measure: Off</button>
            <div id="zoom-label" style="align-self: center; margin-left: 10px;">100%</div>
            <div id="measure-label" style="align-self: center; color: #00ff00; margin-left: 10px; font-weight: bold;"></div>
        </div>
    </div>
    <div id="draggable-preview">
        <img id="preview-img" src="data:image/svg+xml;base64,{B64}" style="width: 100%; max-width: none; display: block; pointer-events: none;"/>
        <svg id="measure-overlay" style="position: absolute; top: 20px; left: 20px; width: calc(100% - 40px); height: calc(100% - 40px); pointer-events: none; overflow: visible;">
            <line id="measure-line" x1="0" y1="0" x2="0" y2="0" stroke="#00ff00" stroke-width="2" stroke-dasharray="4,4" display="none" />
        </svg>
    </div>
    <script>
        const preview = document.getElementById('draggable-preview');
        const previewImg = document.getElementById('preview-img');
        const zoomLabel = document.getElementById('zoom-label');
        const zoomInButton = document.getElementById('zoom-in');
        const zoomOutButton = document.getElementById('zoom-out');
        const resetButton = document.getElementById('reset-view');

        const stateKey = 'svg_viewer_state';
        let savedState = JSON.parse(sessionStorage.getItem(stateKey)) || { zoom: {ZOOM}, scrollLeft: 0, scrollTop: 0 };
        let currentZoom = savedState.zoom;

        let isDragging = false;
        let isMeasuring = false;
        let measureActive = false;
        let startX = 0;
        let startY = 0;
        let measureStartX = 0;
        let measureStartY = 0;
        let startScrollLeft = 0;
        let startScrollTop = 0;

        const measureBtn = document.getElementById('measure-btn');
        const measureLabel = document.getElementById('measure-label');
        const measureLine = document.getElementById('measure-line');

        measureBtn.addEventListener('click', () => {
            isMeasuring = !isMeasuring;
            measureBtn.textContent = isMeasuring ? 'Measure: On' : 'Measure: Off';
            measureBtn.style.background = isMeasuring ? '#006600' : '#111';
            preview.style.cursor = isMeasuring ? 'crosshair' : 'grab';
            measureLine.style.display = 'none';
            measureLabel.textContent = '';
        });

        const saveState = () => {
            sessionStorage.setItem(stateKey, JSON.stringify({
                zoom: currentZoom,
                scrollLeft: preview.scrollLeft,
                scrollTop: preview.scrollTop
            }));
        };

        const updateZoom = () => {
            previewImg.style.width = currentZoom + '%';
            zoomLabel.textContent = currentZoom + '%';
            saveState();
        };

        // Initialize state
        updateZoom();
        // Delay setting scroll to ensure image is loaded and dimensions are calculated
        setTimeout(() => {
            preview.scrollLeft = savedState.scrollLeft;
            preview.scrollTop = savedState.scrollTop;
        }, 50);

        preview.addEventListener('scroll', saveState);

        zoomInButton.addEventListener('click', () => {
            currentZoom = Math.min(1000, currentZoom + 10);
            updateZoom();
        });

        zoomOutButton.addEventListener('click', () => {
            currentZoom = Math.max(10, currentZoom - 10);
            updateZoom();
        });

        resetButton.addEventListener('click', () => {
            currentZoom = {ZOOM};
            preview.scrollLeft = 0;
            preview.scrollTop = 0;
            updateZoom();
        });

        preview.addEventListener('wheel', (event) => {
            if (event.ctrlKey || event.metaKey) {
                event.preventDefault();
                const delta = event.deltaY > 0 ? -10 : 10;
                currentZoom = Math.min(1000, Math.max(10, currentZoom + delta));
                updateZoom();
            }
        });

        preview.addEventListener('pointerdown', (event) => {
            if (event.target.tagName === 'BUTTON') return;
            event.preventDefault();
            
            if (isMeasuring) {
                measureActive = true;
                const rect = preview.getBoundingClientRect();
                measureStartX = event.clientX - rect.left + preview.scrollLeft - 20;
                measureStartY = event.clientY - rect.top + preview.scrollTop - 20;
                
                measureLine.setAttribute('x1', measureStartX);
                measureLine.setAttribute('y1', measureStartY);
                measureLine.setAttribute('x2', measureStartX);
                measureLine.setAttribute('y2', measureStartY);
                measureLine.style.display = 'block';
            } else {
                isDragging = true;
                preview.style.cursor = 'grabbing';
                startX = event.clientX;
                startY = event.clientY;
                startScrollLeft = preview.scrollLeft;
                startScrollTop = preview.scrollTop;
            }
            preview.setPointerCapture(event.pointerId);
        });

        preview.addEventListener('pointermove', (event) => {
            if (isMeasuring && measureActive) {
                const rect = preview.getBoundingClientRect();
                const currentX = event.clientX - rect.left + preview.scrollLeft - 20;
                const currentY = event.clientY - rect.top + preview.scrollTop - 20;
                
                measureLine.setAttribute('x2', currentX);
                measureLine.setAttribute('y2', currentY);
                
                const dx = currentX - measureStartX;
                const dy = currentY - measureStartY;
                const distPixels = Math.sqrt(dx*dx + dy*dy);
                
                // 3.7795275591 px/mm in original SVG.
                // Scale factor: previewImg.clientWidth / previewImg.naturalWidth
                const scale = previewImg.clientWidth / previewImg.naturalWidth;
                const distMm = (distPixels / scale) / 3.7795275591;
                
                measureLabel.textContent = distMm.toFixed(2) + ' mm';
            } else if (isDragging) {
                const dx = event.clientX - startX;
                const dy = event.clientY - startY;
                preview.scrollLeft = startScrollLeft - dx;
                preview.scrollTop = startScrollTop - dy;
                saveState();
            }
        });

        preview.addEventListener('pointerup', (event) => {
            if (isMeasuring && measureActive) {
                measureActive = false;
            } else if (isDragging) {
                isDragging = false;
                if (!isMeasuring) preview.style.cursor = 'grab';
            }
            preview.releasePointerCapture(event.pointerId);
        });

        preview.addEventListener('pointerleave', () => {
            if (isMeasuring && measureActive) {
                measureActive = false;
            } else if (isDragging) {
                isDragging = false;
                if (!isMeasuring) preview.style.cursor = 'grab';
            }
        });
    </script>
    """
    html = html.replace( '{B64}', b64 ).replace( '{ZOOM}', "100" )
    st.iframe(html, height=1000)

with col2:
    

    st.markdown("### Export Full SVG")
    svg_file_name = st.text_input("SVG name", value="tessellation", label_visibility="collapsed", placeholder="SVG name")
    safe_svg_file_name = svg_file_name.strip() or "tessellation"
    if not safe_svg_file_name.lower().endswith(".svg"):
        safe_svg_file_name += ".svg"
    st.download_button(
        label="Download SVG",
        data=svg_str_export,
        file_name=safe_svg_file_name,
        mime="image/svg+xml",
        use_container_width=True,
    )

    st.markdown("### Visualization")
    st.checkbox("Museum Board Base (Black Layer)", key="show_base")
    st.checkbox("Museum Board Top (Blue Layer)", key="show_top")
    st.checkbox("Shrinky Dink / Tape Sheets (Red Layer)", key="show_red")
    st.checkbox("Show 10x10mm Grid", key="show_grid")
    st.checkbox("8.5\" x 11\" landscape boundary (279mm × 216mm)", key="show_sheet")

    # st.markdown("---")
    st.markdown("### Pattern Alignment on Sheet")
    st.number_input("X Offset (mm)", value=5.0, step=1.0, key="align_x")
    st.number_input("Y Offset (mm)", value=5.0, step=1.0, key="align_y")

