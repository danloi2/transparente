"""
Xxxx
xxxx
"""

import os
import re
import subprocess
import traceback

import numpy as np
from PIL import Image, ImageFilter
from sklearn.cluster import KMeans


def generate_color_svg(
    input_path,
    output_path,
    num_colors=32,  # Colores base más realista
    # color_tolerance=25,  # Tolerancia más fina
    # min_area=10,  # Área mínima de región
    turdsize=2,  # Detalles finos
    blur_radius=1,  # Suavizado previo
):
    """
    Genera SVG de alta calidad desde PNG con alpha, preservando colores y formas.
    """
    if os.path.exists(output_path):
        return

    try:
        # --- Cargar y preparar imagen ---
        img = Image.open(input_path).convert("RGBA")
        width, height = img.size
        rgba = np.array(img)
        rgb_arr = rgba[..., :3]
        alpha_arr = rgba[..., 3]

        # Crear máscara de píxeles visibles
        visible_mask = alpha_arr > 20

        # --- Detectar si es B/N ---
        if visible_mask.sum() > 0:
            visible_pixels = rgb_arr[visible_mask]
            saturation = np.std(visible_pixels, axis=1).mean()
            is_bw = saturation < 15
        else:
            is_bw = True

        svg_layers = []

        if is_bw:
            # --- Modo Blanco y Negro ---
            gray = np.array(img.convert("L"))
            # Umbralización adaptativa
            threshold = np.median(gray[visible_mask]) if visible_mask.sum() > 0 else 128
            mask_arr = np.where((gray < threshold) & visible_mask, 0, 255).astype(
                np.uint8
            )

            mask = Image.fromarray(mask_arr, mode="L")

            # Suavizado opcional
            if blur_radius > 0:
                mask = mask.filter(ImageFilter.GaussianBlur(blur_radius))

            t_bmp = f"{output_path}.temp.bmp"
            t_svg = f"{output_path}.temp.svg"

            mask.save(t_bmp)

            subprocess.run(
                [
                    "potrace",
                    t_bmp,
                    "-s",
                    "-o",
                    t_svg,
                    "--flat",
                    "--turdsize",
                    str(turdsize),
                    "--alphamax",
                    "0.5",  # Suavizar curvas
                ],
                check=True,
                capture_output=True,
            )

            with open(t_svg, "r", encoding="utf-8") as f:
                content = f.read()

            path_match = re.search(r'<path d="([^"]+)"', content)
            transform_match = re.search(r'<g transform="([^"]+)"', content)

            if path_match:
                d = path_match.group(1)
                transform = transform_match.group(1) if transform_match else ""
                svg_layers.append(
                    f'<g transform="{transform}"><path d="{d}" fill="#000000" stroke="none" /></g>'
                )

            os.remove(t_bmp)
            os.remove(t_svg)

        else:
            # --- Modo Color: Clustering K-means mejorado ---
            visible_pixels = rgb_arr[visible_mask]

            # Clustering con K-means para colores reales
            kmeans = KMeans(
                n_clusters=min(num_colors, len(visible_pixels)),
                random_state=42,
                n_init=10,
            )
            kmeans.fit(visible_pixels)

            # Obtener colores centrales y contar píxeles
            colors = kmeans.cluster_centers_.astype(int)
            labels = kmeans.labels_

            # Mapear labels de vuelta a la imagen completa
            full_labels = np.full((height, width), -1, dtype=int)
            full_labels[visible_mask] = labels

            # Calcular área de cada color
            unique_labels, counts = np.unique(labels, return_counts=True)

            # Ordenar por área (colores más grandes primero, como fondo)
            sorted_indices = np.argsort(-counts)

            for idx in sorted_indices:
                label = unique_labels[idx]
                color = tuple(colors[label])

                # Filtrar colores casi blancos (fondo)
                if sum(color) > 740:
                    continue

                # Crear máscara para este color
                color_mask = full_labels == label
                mask_arr = np.where(color_mask, 0, 255).astype(np.uint8)

                mask = Image.fromarray(mask_arr, mode="L")

                # Cerrar pequeños huecos
                mask = mask.filter(ImageFilter.MinFilter(3))
                mask = mask.filter(ImageFilter.MaxFilter(3))

                # Suavizado
                if blur_radius > 0:
                    mask = mask.filter(ImageFilter.GaussianBlur(blur_radius))

                t_bmp = f"{output_path}.layer{label}.bmp"
                t_svg = f"{output_path}.layer{label}.svg"

                mask.save(t_bmp)

                subprocess.run(
                    [
                        "potrace",
                        t_bmp,
                        "-s",
                        "-o",
                        t_svg,
                        "--flat",
                        "--turdsize",
                        str(turdsize),
                        "--alphamax",
                        "0.8",  # Curvas más suaves para color
                        "--opttolerance",
                        "0.2",
                    ],
                    check=True,
                    capture_output=True,
                )

                with open(t_svg, "r", encoding="utf-8") as f:
                    content = f.read()

                path_match = re.search(r'<path d="([^"]+)"', content)
                transform_match = re.search(r'<g transform="([^"]+)"', content)

                if path_match:
                    d = path_match.group(1)
                    transform = transform_match.group(1) if transform_match else ""
                    hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                    svg_layers.append(
                        f'<g transform="{transform}">'
                        f'<path d="{d}" fill="{hex_color}" stroke="none" />'
                        "</g>"
                    )

                os.remove(t_bmp)
                os.remove(t_svg)

        # --- Guardar SVG final ---
        with open(output_path, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n')
            f.write(
                f'<svg version="1.1" xmlns="http://www.w3.org/2000/svg" '
                f'width="{width}" height="{height}" '
                f'viewBox="0 0 {width} {height}">\n'
            )
            for layer in svg_layers:
                f.write(f"  {layer}\n")
            f.write("</svg>\n")

        print(
            f"🎨 SVG generado: {os.path.basename(output_path)} ({len(svg_layers)} capas)"
        )

    except Exception as e:
        print(f"❌ Error: {os.path.basename(input_path)}: {e}")
        traceback.print_exc()


# === EJEMPLO DE USO ===
if __name__ == "__main__":
    # Para logos con pocos colores
    generate_color_svg("logo.png", "logo.svg", num_colors=16, blur_radius=0.5)

    # Para ilustraciones complejas
    generate_color_svg(
        "illustration.png", "illustration.svg", num_colors=48, blur_radius=1
    )
