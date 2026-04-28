import os
import sys

def main():
    if len(sys.argv) != 3:
        print("Uso: python main.py <path_carpeta> <extension>")
        print("Ejemplo: python main.py /home/user/proyecto .java")
        sys.exit(1)

    carpeta = sys.argv[1]
    extension = sys.argv[2]

    salida = "resultado.txt"

    with open(salida, "a", encoding="utf-8") as outfile:
        for root, dirs, files in os.walk(carpeta):

            # 🔥 Evitar entrar en carpetas ocultas
            dirs[:] = [d for d in dirs if not d.startswith('.')]

            for file in files:
                # Ignorar también archivos ocultos por seguridad
                if file.startswith('.'):
                    continue

                if file.endswith(extension):
                    ruta_completa = os.path.join(root, file)
                    try:
                        with open(ruta_completa, "r", encoding="utf-8", errors="ignore") as infile:
                            outfile.write(f"\n\n===== {ruta_completa} =====\n\n")
                            outfile.write(infile.read())
                    except Exception as e:
                        print(f"Error leyendo {ruta_completa}: {e}")

    print(f"Proceso finalizado. Ver archivo: {salida}")

if __name__ == "__main__":
    main()

