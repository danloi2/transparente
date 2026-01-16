"""
Módulo principal del proyecto Transparente.
Este script procesa imágenes por lotes aplicando eliminación de fondo (Alpha),
vectorización (SVG) y generación de miniaturas.
"""

import os
import argparse
from src import generators

# Xxxx

def main():
    """
    Punto de entrada principal para la CLI.
    Gestiona los argumentos de entrada/salida, escanea el directorio
    y coordina la generación de archivos PNG y SVG.
    """
    parser = argparse.ArgumentParser(
        description="Procesador de imágenes por lotes (CLI)"
    )
    parser.add_argument(
        "--input", "-i", help="Carpeta con las imágenes originales", required=True
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Carpeta donde se guardarán los resultados",
        required=True,
    )

    args = parser.parse_args()

    input_dir = args.input
    output_dir = args.output

    if not os.path.exists(input_dir):
        print(f"❌ Input directory not found: {input_dir}")
        return

    os.makedirs(output_dir, exist_ok=True)

    extensions = (".png", ".jpg", ".jpeg")
    files = [
        f
        for f in os.listdir(input_dir)
        if f.lower().endswith(extensions)
        and ".temp." not in f
        and ".vtrace_temp." not in f
    ]

    if not files:
        print(f"ℹ️ No image files found in {input_dir}")
        return

    print(f"🚀 Processing {len(files)} images modularly...")

    for file in files:
        input_path = os.path.join(input_dir, file)
        base_name = os.path.splitext(file)[0] + "_alpha"

        # Define paths
        alpha_path = os.path.join(output_dir, base_name + ".png")
        gray_path = os.path.join(output_dir, base_name + "_gray.svg")
        halftone_path = os.path.join(output_dir, base_name + "_halftone.svg")
        lineart_path = os.path.join(output_dir, base_name + "_lineart.svg")
        color_logo_path = os.path.join(output_dir, base_name + "_color_logo.svg")
        color_illus_path = os.path.join(output_dir, base_name + "_color_illus.svg")
        thumb_path = os.path.join(output_dir, base_name + "_thumb.png")

        print(f"\n📦 Processing: {file}...")

        # 1. Generate the AI-processed Alpha PNG first
        generators.generate_alpha_png(input_path, alpha_path)

        # 2. Use the processed Alpha PNG as source for everything else
        if os.path.exists(alpha_path):
            generators.generate_grayscale_svg(alpha_path, gray_path)
            generators.generate_halftone_svg(alpha_path, halftone_path)
            generators.generate_lineart_svg(alpha_path, lineart_path)
            generators.generate_color_svg(
                alpha_path, color_logo_path, num_colors=16, blur_radius=0.5
            )
            generators.generate_color_svg(
                alpha_path, color_illus_path, num_colors=48, blur_radius=1
            )
            generators.generate_thumbnail(alpha_path, thumb_path)
        else:
            print(
                f"⚠️ Skipping vectorization for {file} because Alpha PNG was not created."
            )

    print("\n✅ All image processing complete.")


if __name__ == "__main__":
    main()
