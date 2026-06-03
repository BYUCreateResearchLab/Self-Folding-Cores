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
min_margin = st.sidebar.slider("Min Margin (mm)", 0.0, cell_size/2, 1.5, 0.1)
max_margin = st.sidebar.slider("Max Margin (mm)", 0.0, cell_size/2, 1.5, 0.1)
bridge_size = st.sidebar.slider("Bridge Size (mm)", 0.1, 5.0, 0.5, 0.1)

# GCode Settings Expanders
with st.sidebar.expander("Museum Board GCode Settings"):
    mb_feed = st.number_input("Feed Rate (mm/min)", value=300, key='mb_feed')
    mb_power = st.number_input("Power (%)", value=100.0, key='mb_power')

with st.sidebar.expander("Shrinky Dink GCode Settings"):
    sd_feed = st.number_input("Feed Rate (mm/min)", value=500, key='sd_feed')
    sd_power = st.number_input("Power (%)", value=100.0, key='sd_power')

with st.sidebar.expander("Tape Sheets GCode Settings"):
    ts_feed = st.number_input("Feed Rate (mm/min)", value=1200, key='ts_feed')
    ts_power = st.number_input("Power (%)", value=30.0, key='ts_power')

gcode_settings = {
    'museum': {'feed_rate': float(mb_feed), 'power': float(mb_power)},
    'shrinky': {'feed_rate': float(sd_feed), 'power': float(sd_power)},
    'tape': {'feed_rate': float(ts_feed), 'power': float(ts_power)}
}

# Create a signature for current settings to detect changes
current_settings = (cols, rows, cell_size, min_margin, max_margin, bridge_size, show_base, show_top, show_red, show_grid, gcode_settings)

if 'last_settings' not in st.session_state or st.session_state.last_settings != current_settings:
    st.session_state.last_settings = current_settings
    st.session_state.gcodes_out = None

generator = VariableTabbedGrid(
    cols=int(cols), 
    rows=int(rows), 
    cell_size=float(cell_size), 
    min_margin=float(min_margin), 
    max_margin=float(max_margin), 
    bridge_size=float(bridge_size)
)

# Always generate SVG for preview, but skip GCode unless button is clicked
svg_str, _ = generator.generate(
    show_base=show_base, 
    show_top=show_top, 
    show_red=show_red, 
    show_grid=show_grid,
    gcode_settings=gcode_settings,
    generate_gcode=False
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
    
    st.markdown("### Export GCode")
    st.markdown("These generated files use the specific profile settings defined in the sidebar.")
    
    if st.button("Generate Optimized GCode"):
        with st.spinner("Generating and optimizing paths..."):
            _, st.session_state.gcodes_out = generator.generate(
                show_base=show_base, 
                show_top=show_top, 
                show_red=show_red, 
                show_grid=show_grid,
                gcode_settings=gcode_settings,
                generate_gcode=True
            )
            st.success("GCode generated successfully!")
            
    if st.session_state.gcodes_out:
        st.download_button(
            label="Museum Board Base (.gcode)",
            data=st.session_state.gcodes_out.get('base', ''),
            file_name="museum_board_base.gcode",
            mime="text/plain"
        )
        st.download_button(
            label="Museum Board Top (.gcode)",
            data=st.session_state.gcodes_out.get('top', ''),
            file_name="museum_board_top.gcode",
            mime="text/plain"
        )
        st.download_button(
            label="Shrinky Dink (.gcode)",
            data=st.session_state.gcodes_out.get('shrinky', ''),
            file_name="shrinky_dink.gcode",
            mime="text/plain"
        )
        st.download_button(
            label="Tape Sheets (.gcode)",
            data=st.session_state.gcodes_out.get('tape', ''),
            file_name="tape_sheets.gcode",
            mime="text/plain"
        )
