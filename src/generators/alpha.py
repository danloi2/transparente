"""
Xxxx
xxxx
"""

import os
import traceback

try:
    import numpy as np
    import cv2
    from rembg import remove, new_session
except ImportError:
    print("\n❌ Error: Faltan dependencias críticas.")
    print("Por favor, ejecuta: pip install rembg opencv-python numpy\n")
    raise

from io import BytesIO
from PIL import Image
from src import config

# Inicializar sesión global de IA
SESSION = None


def get_ai_session():
    """Lazily initializes or returns the AI session with feedback."""
    global SESSION
    if SESSION is None:
        print("\nDEBUG: [AI_INIT] Iniciando get_ai_session...")
        print("[AI] Cargando modelo de Inteligencia Artificial (rembg)...")
        print(
            "[INFO] Si es la primera vez, esto puede tardar unos minutos (descargando ~150MB)."
        )
        try:
            print("DEBUG: [AI_INIT] Llamando a new_session('isnet-general-use')...")
            SESSION = new_session("isnet-general-use")
            print("DEBUG: [AI_INIT] new_session completado con éxito.")
            print("[AI] Modelo cargado correctamente.\n")
        except Exception as e:
            print(f"[ERROR] No se pudo cargar el modelo de IA: {e}")
            print(f"DEBUG: [AI_INIT] Traceback: {traceback.format_exc()}")
            SESSION = None
    return SESSION


# ----------------------------
# Postprocesado avanzado
# ----------------------------


def refine_alpha(img, feather=2, blur=1):
    """
    Refina el alpha de una imagen.
    """
    data = np.array(img)
    alpha = data[..., 3].astype(np.float32)

    # Blur suave
    if blur > 0:
        alpha = cv2.GaussianBlur(alpha, (0, 0), blur)

    # Feather morfológico
    if feather > 0:
        kernel = np.ones((feather, feather), np.uint8)
        alpha = cv2.morphologyEx(alpha, cv2.MORPH_CLOSE, kernel)

    # Normalización
    alpha = np.clip(alpha, 0, 255).astype(np.uint8)

    data[..., 3] = alpha
    return Image.fromarray(data)


def clean_white_halo(img):
    """
    Elimina el halo blanco de una imagen.
    """
    data = np.array(img).astype(np.float32)

    r = data[:, :, 0]
    g = data[:, :, 1]
    b = data[:, :, 2]
    a = data[:, :, 3]

    mask = (
        (np.abs(r - config.TRANSPARENT_COLOR[0]) <= config.TOLERANCE)
        & (np.abs(g - config.TRANSPARENT_COLOR[1]) <= config.TOLERANCE)
        & (np.abs(b - config.TRANSPARENT_COLOR[2]) <= config.TOLERANCE)
        & (a > 0)
    )

    # Eliminación directa
    a[mask] = 0

    # Descontaminación de color (despill)
    strength = config.DESPILL_STRENGTH
    r[mask] *= strength
    g[mask] *= strength
    b[mask] *= strength

    data[:, :, 0] = r
    data[:, :, 1] = g
    data[:, :, 2] = b
    data[:, :, 3] = np.clip(a, 0, 255)

    return Image.fromarray(data.astype(np.uint8))


def remove_tiny_alpha(img, min_alpha=8):
    """
    Elimina el alpha pequeño de una imagen.
    """
    data = np.array(img).astype(np.uint8)
    alpha = data[:, :, 3]

    alpha[alpha < min_alpha] = 0
    data[:, :, 3] = alpha

    return Image.fromarray(data)


# ----------------------------
# Pipeline principal
# ----------------------------


def generate_alpha_png(input_path, output_path):
    """
    Genera un archivo PNG con el alpha de una imagen.
    """
    if os.path.exists(output_path):
        return

    try:
        # --- IA ---
        session = get_ai_session()
        if session is None:
            raise RuntimeError(
                "La sesión de IA no está disponible (error al cargar el modelo)."
            )

        with open(input_path, "rb") as i:
            result = remove(i.read(), session=session)

        img = Image.open(BytesIO(result)).convert("RGBA")

        # --- Refinado avanzado ---
        img = clean_white_halo(img)
        img = remove_tiny_alpha(img, min_alpha=config.MIN_ALPHA)
        img = refine_alpha(img, feather=config.ALPHA_FEATHER, blur=config.ALPHA_BLUR)

        img.save(output_path, "PNG")

        print(f"🖼 PNG Alpha OK (PRO): {os.path.basename(output_path)}")

    except Exception as e:
        print(f"❌ Error generating Alpha PNG for {os.path.basename(input_path)}: {e}")
