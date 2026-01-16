"""
Xxxx
xxxx
"""

import os
import re
import subprocess
import traceback
import math
import numpy as np

from PIL import Image, ImageFilter


def generate_grayscale_svg(
    input_path,
    output_path,
    num_tones=8,  # Número de tonos de gris (4-12 recomendado)
    smooth_edges=True,  # Suavizar bordes entre tonos
    turdsize=8,  # Tamaño mínimo de detalles
    alphamax=1.0,  # Suavidad de curvas
    contrast_boost=1.2,  # Aumentar contraste (1.0-1.5)
):
    """
    Genera SVG con múltiples tonos de gris, creando efecto de profundidad y sombras.
    Similar a una imagen en escala de grises pero vectorizada.

    Parámetros:
    - num_tones: Cantidad de grises diferentes (más tonos = más realismo, más peso)
    - smooth_edges: Suaviza transiciones entre tonos
    - turdsize: Ignorar detalles menores a N píxeles
    - alphamax: Suavidad de curvas (0.5-1.3)
    - contrast_boost: Aumenta el contraste para mejor definición
    """
    if os.path.exists(output_path):
        return

    temp_files = []

    try:
        # --- Cargar y preparar imagen ---
        img = Image.open(input_path).convert("RGBA")
        width, height = img.size

        # Crear fondo blanco y componer
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        composite = Image.alpha_composite(bg, img).convert("L")

        # --- Mejorar contraste ---
        if contrast_boost != 1.0:
            gray_array = np.array(composite).astype(np.float32)
            # Aumentar contraste alrededor del punto medio
            gray_array = 128 + (gray_array - 128) * contrast_boost
            gray_array = np.clip(gray_array, 0, 255).astype(np.uint8)
            composite = Image.fromarray(gray_array)

        # --- Suavizado opcional ---
        if smooth_edges:
            composite = composite.filter(ImageFilter.GaussianBlur(0.8))

        gray_array = np.array(composite)

        # --- Posterización en N tonos ---
        # Calcular los umbrales para dividir en tonos
        tone_levels = np.linspace(0, 255, num_tones + 1)

        svg_layers = []

        # Procesar cada tono de gris (del más oscuro al más claro)
        for i in range(num_tones):
            min_val = tone_levels[i]
            max_val = tone_levels[i + 1]

            # Color de este tono (más oscuro = menor valor)
            tone_value = int((min_val + max_val) / 2)

            # Crear máscara para este rango tonal
            # Los píxeles en este rango serán NEGROS (0), el resto BLANCOS (255)
            mask_array = np.where(
                (gray_array >= min_val) & (gray_array < max_val),
                0,  # Negro = área a rellenar
                255,  # Blanco = transparente
            ).astype(np.uint8)

            # Saltar tonos casi blancos (fondo)
            if tone_value > 245:
                continue

            # Contar píxeles de este tono
            pixel_count = np.sum(mask_array == 0)
            if pixel_count < 50:  # Saltar tonos con muy pocos píxeles
                continue

            mask = Image.fromarray(mask_array, mode="L").convert("1")

            # Limpiar ruido pequeño
            mask = mask.filter(ImageFilter.MinFilter(3))
            mask = mask.filter(ImageFilter.MaxFilter(3))

            # Guardar máscara temporal
            temp_bmp = f"{output_path}.tone{i}.bmp"
            temp_svg = f"{output_path}.tone{i}.svg"
            temp_files.extend([temp_bmp, temp_svg])

            mask.save(temp_bmp)

            # --- Ejecutar Potrace ---
            subprocess.run(
                [
                    "potrace",
                    temp_bmp,
                    "-s",
                    "-o",
                    temp_svg,
                    "--flat",
                    "--turdsize",
                    str(turdsize),
                    "--alphamax",
                    str(alphamax),
                    "--opttolerance",
                    "0.2",
                ],
                check=True,
                capture_output=True,
            )

            # --- Extraer paths del SVG ---
            with open(temp_svg, "r", encoding="utf-8") as f:
                content = f.read()

            # Buscar todos los paths (puede haber múltiples)
            paths = re.findall(r'<path d="([^"]+)"', content)
            transform_match = re.search(r'<g transform="([^"]+)"', content)
            transform = transform_match.group(1) if transform_match else ""

            if paths:
                # Color en escala de grises
                hex_color = f"#{tone_value:02x}{tone_value:02x}{tone_value:02x}"

                # Agregar todos los paths de este tono
                for path_d in paths:
                    svg_layers.append(
                        {
                            "tone": tone_value,
                            "svg": f'<path d="{path_d}" fill="{hex_color}" stroke="none" />',
                        }
                    )

        # --- Ordenar capas de claro a oscuro (fondo primero) ---
        svg_layers.sort(key=lambda x: -x["tone"])

        # --- Generar SVG final ---
        with open(output_path, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n')
            f.write('<svg version="1.1" xmlns="http://www.w3.org/2000/svg" ')
            f.write(
                f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">\n'
            )
            f.write(f"  <desc>Generated with {num_tones} gray tones</desc>\n")

            # Agrupar por tono si hay transform
            if transform:
                f.write(f'  <g transform="{transform}">\n')
                for layer in svg_layers:
                    f.write(f'    {layer["svg"]}\n')
                f.write("  </g>\n")
            else:
                for layer in svg_layers:
                    f.write(f'  {layer["svg"]}\n')

            f.write("</svg>\n")

        print(
            f"🎨 SVG Grayscale OK: {os.path.basename(output_path)} ({len(svg_layers)} tonos)"
        )

    except subprocess.CalledProcessError as e:
        print(f"\u274c Error Potrace: {e.stderr}")
        raise
    except Exception as e:
        print(f"\u274c Error: {e}")

        traceback.print_exc()
    finally:
        # Limpiar archivos temporales
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)


def generate_halftone_svg(
    input_path,
    output_path,
    dot_size=3,  # Tamaño máximo del punto
    spacing=5,  # Distancia entre centros de puntos
    angle=45,  # Ángulo de la trama (ej. 15, 45, 75)
):
    """
    Genera SVG con efecto de medio tono (halftone) como impresión tradicional.
    """
    if os.path.exists(output_path):
        return

    try:
        img = Image.open(input_path).convert("RGBA")
        width, height = img.size
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        composite = Image.alpha_composite(bg, img).convert("L")
        gray_array = np.array(composite)

        # Convertimos el ángulo a radianes para las funciones de math
        angle_rad = math.radians(angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        circles = []

        # Ampliamos el rango de escaneo para cubrir las esquinas al rotar
        # La diagonal de la imagen asegura que no queden huecos blancos
        diagonal = int(math.sqrt(width**2 + height**2))
        for y in range(-diagonal, diagonal, spacing):
            for x in range(-diagonal, diagonal, spacing):

                # Rotamos las coordenadas del grid hacia atrás para muestrear la imagen
                # (x_rot, y_rot) es donde estaría el punto si el grid no estuviera girado
                orig_x = int(x * cos_a - y * sin_a + width / 2)
                orig_y = int(x * sin_a + y * cos_a + height / 2)

                if 0 <= orig_x < width and 0 <= orig_y < height:
                    gray_val = gray_array[orig_y, orig_x]
                    darkness = 1 - (gray_val / 255.0)
                    radius = (dot_size * darkness) * 0.8

                    if radius > 0.5:
                        # Dibujamos el círculo en su posición original del grid rotado
                        # pero centrado en la imagen
                        circles.append(
                            f'<circle cx="{orig_x}" cy="{orig_y}" r="{radius:.2f}" fill="#000" />'
                        )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write(
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
                f'height="{height}" viewBox="0 0 {width} {height}">\n'
            )
            f.write('  <rect width="100%" height="100%" fill="white"/>\n')
            for circle in circles:
                f.write(f"  {circle}\n")
            f.write("</svg>\n")

        print(
            f"🎨 SVG Halftone OK: {os.path.basename(output_path)} ({len(circles)} puntos, {angle}º)"
        )

    except Exception as e:
        print(f"\u274c Error: {e}")


def generate_lineart_svg(
    input_path, output_path, threshold=140, turdsize=10, alphamax=1.0
):
    """
    Genera SVG con efecto de lineart como impresión tradicional.
    """
    if os.path.exists(output_path):
        return

    temp_bmp = output_path + ".temp.bmp"
    try:
        img = Image.open(input_path).convert("RGBA")
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        composite = Image.alpha_composite(bg, img).convert("L")

        # Umbralización simple para alto contraste
        mask = composite.point(lambda p: 0 if p < threshold else 255, "1")
        mask.save(temp_bmp)

        subprocess.run(
            [
                "potrace",
                temp_bmp,
                "-s",
                "-o",
                output_path,
                "--flat",
                "--turdsize",
                str(turdsize),
                "--alphamax",
                str(alphamax),
                "--opttolerance",
                "0.2",
            ],
            check=True,
            capture_output=True,
        )

        print(f"✏️ SVG Lineart OK: {os.path.basename(output_path)}")
    except Exception as e:
        print(f"\u274c Error generando Lineart SVG: {e}")
    finally:
        if os.path.exists(temp_bmp):
            os.remove(temp_bmp)


# === EJEMPLOS DE USO ===
if __name__ == "__main__":
    # Uso básico: 8 tonos de gris
    generate_grayscale_svg("portrait.png", "portrait_gray.svg")

    # Más tonos para mayor realismo (pero archivo más pesado)
    generate_grayscale_svg(
        "photo.png",
        "photo_gray.svg",
        num_tones=12,  # Más suave
        smooth_edges=True,
        contrast_boost=1.3,  # Mayor contraste
        turdsize=6,  # Preservar detalles
        alphamax=1.2,  # Curvas suaves
    )

    # Menos tonos para estilo gráfico
    generate_grayscale_svg(
        "logo.png",
        "logo_gray.svg",
        num_tones=4,  # Estilo poster
        contrast_boost=1.5,  # Alto contraste
        turdsize=12,
        alphamax=0.8,
    )

    # Efecto halftone (estilo vintage/impresión)
    generate_halftone_svg(
        "portrait.png", "portrait_halftone.svg", dot_size=4, spacing=6
    )
