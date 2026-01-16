# FondoTransparente

![GitHub release (latest by date)](https://img.shields.io/github/v/release/danloi2/transparente?style=flat-square&color=blue)
![Python Version](https://img.shields.io/badge/python-3.11-blue?style=flat-square&logo=python)
![OpenCV](https://img.shields.io/badge/OpenCV-5.x-white?style=flat-square&logo=opencv&logoColor=white&color=5C3EE8)
![ONNX Runtime](https://img.shields.io/badge/ONNX-Runtime-orange?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)

## 🚀 Instalación y Configuración

### Requisitos previos

Este proyecto utiliza **Conda** para la gestión de dependencias y entornos. Se recomienda el uso de [Miniforge](https://github.com/conda-forge/miniforge).

### Configuración del entorno

#### Crear el entorno desde el archivo yml

```bash
conda env create -f environment.yml
```

#### Activar el entorno

```bash
conda activate transparente
```

## Ejecución en desarrollo

```bash
python gui_main.py
```

## 🛠️ Compilación para macOS

Sigue estos pasos para generar un instalador nativo (.dmg) distribuible.

1. **Generar el paquete con PyInstaller**
   Este comando crea la estructura de la aplicación y empaqueta las librerías pesadas (OpenCV, ONNX, SciPy).

   ```bash
   pyinstaller --onedir --windowed --noconfirm \
     --name "FondoTransparente" \
     --collect-all cv2 \
     --collect-all onnxruntime \
     --collect-all scipy \
     gui_main.py
   ```

2. **Crear el Instalador (.dmg) con dmgbuild**

Para que el instalador sea visual y fácil de usar, ejecutamos dmgbuild.

Asegúrate de tener un archivo dmg_settings.py con este contenido:

```python
import os.path

base_dir = os.path.abspath('.')

# 1. CONTENIDO REAL
files = {
    os.path.join(base_dir, 'dist/FondoTransparente.app'): 'FondoTransparente.app',
    os.path.join(base_dir, 'dist/FondoTransparente/_internal'): '_internal'
}

# 2. ENLACES SIMBÓLICOS (Alias a Aplicaciones)
symlinks = {
    'Aplicaciones': '/Applications'
}

# 3. POSICIONES DE ICONOS (X, Y)
icon_locations = {
    'FondoTransparente.app': (140, 120),
    'Aplicaciones': (460, 120),
    '_internal': (300, 400) # Se coloca fuera de la vista principal
}

window_rect = ((200, 200), (600, 350))
icon_size = 100
```

**Comando final de construcción:**

```bash
# Limpiar instalaciones previas
rm -f dist/Fondo-Transparente-Installer.dmg

# Generar el nuevo DMG
dmgbuild -s dmg_settings.py "Fondo Transparente" dist/Fondo-Transparente-Installer.dmg
```

### Notas de Distribución

Seguridad: Al ser una app no firmada por un desarrollador identificado de Apple, el usuario final deberá permitir su ejecución en Ajustes del Sistema > Privacidad y Seguridad.

Estructura: No elimines la carpeta \_internal del interior del DMG, ya que contiene las dependencias críticas de Python.

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - mira el archivo [LICENSE](LICENSE) para más detalles.
