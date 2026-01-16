"""
Xxx
Xxx
"""

import os
import threading
import traceback
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from src import generators


class ImageProcessorGUI:
    """
    GUI para el procesador de imágenes.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Image to Vector & Alpha - Python Tool")
        self.root.geometry("600x450")
        self.root.resizable(False, False)

        # Variables
        self.input_file = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready. Please select a file.")

        # UI Layout
        self._setup_ui()

    def _setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            main_frame, text="Procesador Transparente", font=("Helvetica", 16, "bold")
        )
        title_label.pack(pady=(0, 20))

        # Input Selection Group
        input_group = ttk.LabelFrame(
            main_frame, text=" 1. Imagen de entrada (.png, .jpg) ", padding="10"
        )
        input_group.pack(fill=tk.X, pady=5)

        ttk.Entry(input_group, textvariable=self.input_file).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10)
        )
        btn_in = ttk.Button(
            input_group, text="Buscar Archivo", command=self._browse_input
        )
        btn_in.pack(side=tk.RIGHT)

        # Output Selection Group
        output_group = ttk.LabelFrame(
            main_frame, text=" 2. Carpeta de destino (donde guardar) ", padding="10"
        )
        output_group.pack(fill=tk.X, pady=5)

        ttk.Entry(output_group, textvariable=self.output_dir).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10)
        )
        btn_out = ttk.Button(
            output_group, text="Elegir Carpeta", command=self._browse_output
        )
        btn_out.pack(side=tk.RIGHT)

        # Process Button
        self.process_btn = ttk.Button(
            main_frame, text="INICIAR CONVERSION", command=self._process_image
        )
        self.process_btn.pack(pady=30)

        # Status Bar
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Label(
            status_frame, textvariable=self.status_var, font=("Helvetica", 9, "italic")
        ).pack(side=tk.LEFT)

    def _browse_input(self):
        print("DEBUG: Clicking Browse Input...")
        filename = filedialog.askopenfilename(
            parent=self.root,
            title="Seleccionar Imagen (PNG o JPEG)",
            filetypes=[
                ("Archivos de imagen", "*.png *.jpg *.jpeg *.JPG *.JPEG"),
                ("PNG", "*.png"),
                ("JPEG", "*.jpg *.jpeg"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if filename:
            print(f"DEBUG: Selected file: {filename}")
            self.input_file.set(filename)
            # Suggest output directory if empty
            if not self.output_dir.get():
                self.output_dir.set(os.path.dirname(filename))

    def _browse_output(self):
        print("DEBUG: Clicking Browse Output...")
        directory = filedialog.askdirectory(
            parent=self.root, title="Select Output Directory"
        )
        if directory:
            print(f"DEBUG: Selected directory: {directory}")
            self.output_dir.set(directory)

    def _process_image(self):

        input_path = self.input_file.get()
        output_dir = self.output_dir.get()

        print(
            f"DEBUG: [GUI] Iniciar Conversión pulsado. Input: {input_path}, Output: {output_dir}"
        )

        if not input_path or not os.path.exists(input_path):
            messagebox.showerror("Error", "Por favor, selecciona un archivo válido.")
            return
        if not output_dir or not os.path.exists(output_dir):
            messagebox.showerror(
                "Error", "Por favor, selecciona una carpeta de destino válida."
            )
            return

        # Check for potrace dependency
        if not shutil.which("potrace"):
            messagebox.showerror(
                "Error",
                "No se encontró 'potrace' en el sistema.\nPor favor, instálalo antes de continuar.",
            )
            return

        self.process_btn.state(["disabled"])
        self.status_var.set("Iniciando proceso...")
        self.root.update_idletasks()  # Force UI update

        # Run conversion in a separate thread to keep UI responsive
        def run_thread():
            try:
                print("DEBUG: [THREAD] Hilo iniciado.")
                base_name = os.path.splitext(os.path.basename(input_path))[0] + "_alpha"
                paths = {
                    "alpha": os.path.join(output_dir, base_name + ".png"),
                    "gray": os.path.join(output_dir, base_name + "_gray.svg"),
                    "halftone": os.path.join(output_dir, base_name + "_halftone.svg"),
                    "lineart": os.path.join(output_dir, base_name + "_lineart.svg"),
                    "color_logo": os.path.join(
                        output_dir, base_name + "_color_logo.svg"
                    ),
                    "color_illus": os.path.join(
                        output_dir, base_name + "_color_illus.svg"
                    ),
                    "thumb": os.path.join(output_dir, base_name + "_thumb.png"),
                }

                print("DEBUG: [THREAD] Generando Alpha...")
                self.status_var.set("Generando Alpha PNG (IA)...")
                self.root.update_idletasks()
                generators.generate_alpha_png(input_path, paths["alpha"])

                alpha_processed = paths["alpha"]
                if not os.path.exists(alpha_processed):
                    raise FileNotFoundError(
                        f"Fallo en la generación del PNG Alpha por IA: "
                        f"no se encontró {alpha_processed}"
                    )

                print("DEBUG: [THREAD] Generando SVG Grayscale...")
                self.status_var.set("Generando SVG Grayscale...")
                self.root.update_idletasks()
                generators.generate_grayscale_svg(alpha_processed, paths["gray"])

                print("DEBUG: [THREAD] Generando SVG Halftone...")
                self.status_var.set("Generando SVG Halftone...")
                self.root.update_idletasks()
                generators.generate_halftone_svg(alpha_processed, paths["halftone"])

                print("DEBUG: [THREAD] Generando SVG Lineart...")
                self.status_var.set("Generando SVG Lineart...")
                self.root.update_idletasks()
                generators.generate_lineart_svg(alpha_processed, paths["lineart"])

                print("DEBUG: [THREAD] Generando SVG Color (Logo)...")
                self.status_var.set("Generando SVG Color (Logo)...")
                self.root.update_idletasks()
                generators.generate_color_svg(
                    alpha_processed, paths["color_logo"], num_colors=16, blur_radius=0.5
                )

                print("DEBUG: [THREAD] Generando SVG Color (Ilustración)...")
                self.status_var.set("Generando SVG Color (Ilustración)...")
                self.root.update_idletasks()
                generators.generate_color_svg(
                    alpha_processed, paths["color_illus"], num_colors=48, blur_radius=1
                )

                print("DEBUG: [THREAD] Generando Miniatura...")
                self.status_var.set("Generando Miniatura...")
                self.root.update_idletasks()
                generators.generate_thumbnail(alpha_processed, paths["thumb"])

                print("DEBUG: [THREAD] ¡Todo OK!")
                self.status_var.set("¡Completado!")
                messagebox.showinfo("Éxito", f"Archivos generados en:\n{output_dir}")

            except Exception as e:  # pylint: disable=broad-exception-caught
                error_trace = traceback.format_exc()
                print(f"DEBUG: [THREAD] ERROR CRÍTICO: {e}\n{error_trace}")
                self.status_var.set("Error en el proceso.")
                messagebox.showerror(
                    "Error",
                    f"Fallo al procesar: {str(e)}\n\nRevisa la terminal para más detalles.",
                )
            finally:
                print("DEBUG: [THREAD] Hilo finalizado.")
                self.process_btn.state(["!disabled"])
                if self.status_var.get() != "¡Completado!":
                    self.status_var.set("Listo.")

        threading.Thread(target=run_thread, daemon=True).start()


def start_gui():
    """
    Inicia la GUI.
    """
    root = tk.Tk()
    _app = ImageProcessorGUI(root)
    root.mainloop()
