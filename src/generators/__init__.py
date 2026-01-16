"""
Generators for different image processing tasks.
"""

from .alpha import generate_alpha_png
from .mono import generate_grayscale_svg, generate_halftone_svg, generate_lineart_svg
from .color import generate_color_svg
from .thumbnail import generate_thumbnail
