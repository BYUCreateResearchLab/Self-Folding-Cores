# Self-Folding-Cores

## Setup

1. Create a virtual environment:
   ```powershell
   python -m venv .venv
   ```

2. Activate it in PowerShell:
   ```powershell
   .\.venv\Scripts\activate
   ```

3. Install the dependencies from `requirements.txt`:
   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

## Geometry generator

Run the standard geometry generator from the repository root:
```powershell
python geometry_generator.py
```

This script writes generated SVG files into the `SVGs/` folder. The grid size, cell size, margins, and tab width are defined inside `geometry_generator.py`; edit those values if you need different output.

## Curved geometry generator

Run the curved geometry generator to create a curved variant:
```powershell
python curved_geometry_generator.py
```

This uses the variable-margin logic in `curved_geometry_generator.py` and also saves output into `SVGs/`.

## GUI

Launch the Streamlit GUI from the repository root:
```powershell
streamlit run app/main.py
```

When Streamlit starts, it prints a local URL such as `http://localhost:8501/`. Open that URL in your browser to view the GUI.

The app in `app/` provides sliders and export controls for previewing and generating tessellation geometry. Use the sidebar to adjust grid size, cell spacing, margins, tab behavior, and GCode export settings.

A new checkbox is available for adding an 8.5" × 11" paper boundary (216 mm × 279 mm) to the exported SVG. That rectangle is drawn as a separate paper sheet outline so Lightburn can import the design with a known sheet size.
