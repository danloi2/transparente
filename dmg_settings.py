"""
Configuración para la creación del DMG de macOS.
"""

import os.path

base_dir = os.path.abspath('.')

# 1. CONTENIDO REAL (Cambiamos gui_main.app por FondoTransparente.app)
files = {
    os.path.join(base_dir, 'dist/FondoTransparente.app'): 'FondoTransparente.app',
    os.path.join(base_dir, 'dist/FondoTransparente/_internal'): '_internal'
}

# 2. ENLACES SIMBÓLICOS
symlinks = {
    'Aplicaciones': '/Applications'
}

# 3. POSICIONES (Asegúrate de que los nombres coincidan)
icon_locations = {
    'FondoTransparente.app': (140, 120),
    'Aplicaciones': (460, 120),
    '_internal': (300, 400)
}

window_rect = ((200, 200), (600, 350))
ICON_SIZE = 100
