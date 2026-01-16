"""
Generates high-quality thumbnails from the processed alpha PNG.
"""

import os
from PIL import Image
from src import config

def generate_thumbnail(input_path, output_path):
    """Generates high-quality thumbnails from the processed alpha PNG."""
    if os.path.exists(output_path):
        return

    try:
        img = Image.open(input_path)
        # Use the already clear alpha image
        w_p = config.THUMB_WIDTH / float(img.size[0])
        h_s = int((float(img.size[1]) * float(w_p)))
        img = img.resize((config.THUMB_WIDTH, h_s), Image.Resampling.LANCZOS)
        img.save(output_path)
        print(f"🔹 Thumbnail OK: {os.path.basename(output_path)}")
    except Exception as e:
        print(f"❌ Error generating thumbnail for {os.path.basename(input_path)}: {e}")
