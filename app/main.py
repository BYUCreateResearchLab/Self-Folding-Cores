import streamlit as st
import base64
from geometry import VariableTabbedGrid

# Trigger Streamlit to reload to pick up geometry.py changes
st.set_page_config(layout="wide", page_title="Self-Folding Cores UI")

st.sidebar.title("Parameters")

st.sidebar.subheader("Visualization")
show_base = st.sidebar.checkbox("Museum Board Base (White Layer)", value=True)
show_top = st.sidebar.checkbox("Museum Board Top (Green Layer)", value=True)
show_red = st.sidebar.checkbox("Shrinky Dink / Tape Sheets (Red Layer)", value=True)
show_grid = st.sidebar.checkbox("Show 10x10mm Grid", value=True)
zoom_level = st.sidebar.slider("Preview Zoom (%)", 10, 1000, 100, 10)

st.sidebar.subheader("Grid Dimensions")
cols = st.sidebar.number_input("Columns", min_value=1, max_value=50, value=15)
rows = st.sidebar.number_input("Rows", min_value=1, max_value=50, value=11)
cell_size = st.sidebar.number_input("Cell Size (mm)", min_value=1.0, max_value=100.0, value=15.0)

st.sidebar.subheader("Margins & Tabs")
normal_gap = st.sidebar.slider("Normal Gap (mm)", 0.0, cell_size/2, 1.5, 0.1)
alt_gap = st.sidebar.slider("Alternate Gap (mm)", 0.0, cell_size/2, 0.5, 0.1)
bridge_size = st.sidebar.slider("Bridge Size (mm)", 0.1, 5.0, 0.5, 0.1)

# Create a signature for current settings to detect changes
current_settings = (cols, rows, cell_size, normal_gap, alt_gap, bridge_size, show_base, show_top, show_red, show_grid)

if 'last_settings' not in st.session_state or st.session_state.last_settings != current_settings:
    st.session_state.last_settings = current_settings

generator = VariableTabbedGrid(
    cols=int(cols), 
    rows=int(rows), 
    cell_size=float(cell_size), 
    normal_gap=float(normal_gap), 
    alt_gap=float(alt_gap), 
    bridge_size=float(bridge_size)
)

svg_str = generator.generate(
    show_base=show_base, 
    show_top=show_top, 
    show_red=show_red, 
    show_grid=show_grid
)

st.title("Tessellation Visualizer")

col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("### Preview")
    b64 = base64.b64encode(svg_str.encode('utf-8')).decode("utf-8")
    
    # CSS wrapper for panning and zooming the SVG
    html = f'''
    <div style="width: 100%; height: 75vh; overflow: auto; background-color: #1e1e1e; border: 1px solid #444; border-radius: 5px; padding: 20px;">
        <img src="data:image/svg+xml;base64,{b64}" style="width: {zoom_level}%; max-width: none;"/>
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)

with col2:
    st.markdown("### Export Full SVG")
    st.download_button(
        label="Download SVG",
        data=svg_str,
        file_name="tessellation.svg",
        mime="image/svg+xml"
    )
