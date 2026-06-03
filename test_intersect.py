import sys
import os
sys.path.append('app')
from geometry import VariableTabbedGrid

generator = VariableTabbedGrid(4, 4, 15.0, 1.5, 0.5, 0.5)
svg = generator.generate(False, True, False, False, False)
with open('test.svg', 'w') as f:
    f.write(svg)
print("SVG generated")
