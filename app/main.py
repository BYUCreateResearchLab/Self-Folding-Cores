import streamlit as st
import base64
from geometry import VariableTabbedGrid

# Trigger Streamlit to reload to pick up geometry.py changes
st.set_page_config(layout="wide", page_title="Self-Folding Cores UI")

st.markdown(
    """
    <style>
        body, .stApp, .main, .block-container {
            background-color: #000000 !important;
            color: #ffffff !important;
        }
        section[data-testid="stSidebar"] {
            background-color: #000000 !important;
        }
        .css-1ynx3rn {
            background-color: #000000 !important;
        }
        .stButton button, .stDownloadButton button {
            background-color: #111111 !important;
            color: #ffffff !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.title("Parameters")

st.sidebar.subheader("Visualization")
show_base = st.sidebar.checkbox("Museum Board Base (Black Layer)", value=True)
show_top = st.sidebar.checkbox("Museum Board Top (Blue Layer)", value=True)
show_red = st.sidebar.checkbox("Shrinky Dink / Tape Sheets (Red Layer)", value=True)
show_grid = st.sidebar.checkbox("Show 10x10mm Grid", value=True)
show_sheet = st.sidebar.checkbox("8.5\" x 11\" landscape boundary (279mm × 216mm)", value=True)

st.sidebar.subheader("Pattern Alignment on Sheet")
align_x = st.sidebar.number_input("X Offset (mm)", value=5.0, step=1.0)
align_y = st.sidebar.number_input("Y Offset (mm)", value=5.0, step=1.0)

st.sidebar.subheader("Grid Dimensions")
cols = st.sidebar.number_input("Columns", min_value=1, max_value=50, value=15)
rows = st.sidebar.number_input("Rows", min_value=1, max_value=50, value=11)
cell_size = st.sidebar.number_input("Cell Size (mm)", min_value=1.0, max_value=100.0, value=15.0)

st.sidebar.subheader("Margins & Tabs")
normal_gap = st.sidebar.slider("Total Normal Gap (mm)", 0.0, float(cell_size), 3.0, 0.1)
alt_gap = st.sidebar.slider("Total Alternate Gap (mm)", 0.0, float(cell_size), 1.0, 0.1)
bridge_size = st.sidebar.slider("Bridge Size (mm)", 0.1, 5.0, 0.5, 0.1)

# Create a signature for current settings to detect changes
current_settings = (cols, rows, cell_size, normal_gap, alt_gap, bridge_size, show_base, show_top, show_red, show_grid, show_sheet, align_x, align_y)

if 'last_settings' not in st.session_state or st.session_state.last_settings != current_settings:
    st.session_state.last_settings = current_settings

generator = VariableTabbedGrid(
    cols=int(cols), 
    rows=int(rows), 
    cell_size=float(cell_size), 
    normal_gap=float(normal_gap) / 2.0, 
    alt_gap=float(alt_gap) / 2.0, 
    bridge_size=float(bridge_size)
)

# Generate SVG for preview (with grid if enabled)
svg_str_preview = generator.generate(
    show_base=show_base,
    show_top=show_top,
    show_red=show_red,
    show_grid=show_grid,
    show_sheet=show_sheet,
    align_x=align_x,
    align_y=align_y
)

# Generate SVG for export (force grid off)
svg_str_export = generator.generate(
    show_base=show_base,
    show_top=show_top,
    show_red=show_red,
    show_grid=False,
    show_sheet=show_sheet,
    align_x=align_x,
    align_y=align_y
)

st.title("Tessellation Visualizer")

col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("### Preview")
    b64 = base64.b64encode(svg_str_preview.encode('utf-8')).decode("utf-8")
    
    # CSS wrapper for panning and zooming the SVG, with drag support and zoom controls
    html = """
    <div style="display: flex; gap: 8px; margin-bottom: 10px;">
        <button id="zoom-in" style="padding: 8px 14px; border: 1px solid #444; border-radius: 4px; background: #111; color: #fff; cursor: pointer;">Zoom In</button>
        <button id="zoom-out" style="padding: 8px 14px; border: 1px solid #444; border-radius: 4px; background: #111; color: #fff; cursor: pointer;">Zoom Out</button>
        <button id="reset-view" style="padding: 8px 14px; border: 1px solid #444; border-radius: 4px; background: #111; color: #fff; cursor: pointer;">Reset View</button>
        <div id="zoom-label" style="align-self: center; color: #fff;">100%</div>
    </div>
    <div id="draggable-preview" style="position: relative; width: 100%; height: 75vh; overflow: auto; background-color: #ffffff; border: 1px solid #444; border-radius: 5px; padding: 20px; cursor: grab;">
        <img id="preview-img" src="data:image/svg+xml;base64,{B64}" style="width: 100%; max-width: none; display: block;"/>
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
        let startX = 0;
        let startY = 0;
        let startScrollLeft = 0;
        let startScrollTop = 0;

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
            event.preventDefault();
            const delta = event.deltaY > 0 ? -10 : 10;
            currentZoom = Math.min(1000, Math.max(10, currentZoom + delta));
            updateZoom();
        });

        preview.addEventListener('pointerdown', (event) => {
            if (event.target.tagName === 'BUTTON') return;
            event.preventDefault();
            isDragging = true;
            preview.style.cursor = 'grabbing';
            startX = event.clientX;
            startY = event.clientY;
            startScrollLeft = preview.scrollLeft;
            startScrollTop = preview.scrollTop;
            preview.setPointerCapture(event.pointerId);
        });

        preview.addEventListener('pointermove', (event) => {
            if (!isDragging) return;
            const dx = event.clientX - startX;
            const dy = event.clientY - startY;
            preview.scrollLeft = startScrollLeft - dx;
            preview.scrollTop = startScrollTop - dy;
            saveState();
        });

        preview.addEventListener('pointerup', (event) => {
            if (!isDragging) return;
            isDragging = false;
            preview.style.cursor = 'grab';
            preview.releasePointerCapture(event.pointerId);
        });

        preview.addEventListener('pointerleave', () => {
            if (!isDragging) return;
            isDragging = false;
            preview.style.cursor = 'grab';
        });
    </script>
    """
    html = html.replace( '{B64}', b64 ).replace( '{ZOOM}', "100" )
    st.iframe(html, height=820)

with col2:
    st.markdown("### Export Full SVG")
    st.download_button(
        label="Download SVG",
        data=svg_str_export,
        file_name="tessellation.svg",
        mime="image/svg+xml"
    )
