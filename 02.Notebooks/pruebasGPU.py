import os
import sys
import re
import platform
import subprocess
from pathlib import Path

import tensorflow as tf

PRINT_WIDTH = 80

def header(title):
    print("\n" + "=" * PRINT_WIDTH)
    print(title)
    print("=" * PRINT_WIDTH)

def run_cmd(cmd):
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        return True, out.strip()
    except Exception as e:
        return False, str(e)

def parse_nvcc_version(text):
    # Busca "release X.Y"
    m = re.search(r"release\s+(\d+\.\d+)", text)
    return m.group(1) if m else None

def extract_cudnn_version_from_header(header_path):
    try:
        text = Path(header_path).read_text(errors="ignore")
        maj = re.search(r"#define\s+CUDNN_MAJOR\s+(\d+)", text)
        mid = re.search(r"#define\s+CUDNN_MINOR\s+(\d+)", text)
        pat = re.search(r"#define\s+CUDNN_PATCHLEVEL\s+(\d+)", text)
        if maj and mid and pat:
            return f"{maj.group(1)}.{mid.group(1)}.{pat.group(1)}"
    except Exception:
        pass
    return None

def find_cudnn():
    """
    Intenta ubicar cuDNN y su versión (Linux/WSL2 y Windows).
    """
    candidates = []

    if os.name == "nt":
        # Rutas típicas en Windows
        cuda_path = os.environ.get("CUDA_PATH", r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA")
        if cuda_path and Path(cuda_path).exists():
            candidates += list(Path(cuda_path).rglob("cudnn64*.dll"))
        # También buscar en Program Files por si hay varias versiones
        candidates += list(Path(r"C:\Program Files\NVIDIA GPU Computing Toolkit").rglob("cudnn64*.dll"))
        header_candidates = list(Path(r"C:\Program Files\NVIDIA GPU Computing Toolkit").rglob("include\\cudnn*.h"))
    else:
        # Linux/WSL2
        lib_patterns = [
            "/usr/lib/x86_64-linux-gnu/libcudnn*.so*",
            "/usr/local/cuda/lib64/libcudnn*.so*",
            "/usr/local/cuda-*/lib64/libcudnn*.so*",
        ]
        for pat in lib_patterns:
            candidates += list(Path("/").glob(pat.replace("/", os.sep)))
        header_candidates = []
        for p in ["/usr/include", "/usr/local/cuda/include", "/usr/local/cuda-*/include"]:
            header_candidates += list(Path("/").glob((p + "/cudnn*.h").replace("/", os.sep)))

    cudnn_paths = [str(p) for p in candidates]
    cudnn_header_version = None
    # Intenta leer versión desde cudnn_version.h o cudnn.h
    for hp in header_candidates:
        ver = extract_cudnn_version_from_header(hp)
        if ver:
            cudnn_header_version = ver
            break

    return cudnn_paths, cudnn_header_version

def get_tf_build_info():
    info = {}
    try:
        from tensorflow.python.platform import build_info as tf_build_info
        info = getattr(tf_build_info, "build_info", {})
    except Exception:
        pass
    try:
        info2 = tf.sysconfig.get_build_info()
        info.update(info2 if isinstance(info2, dict) else {})
    except Exception:
        pass
    return info

def main():
    header("Verificación del entorno TensorFlow + GPU")

    print(f"Sistema operativo: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version.splitlines()[0]}")
    tf_version = tf.__version__
    print(f"TensorFlow: {tf_version}")

    # Advertencia por Windows nativo (TF >= 2.11)
    if os.name == "nt":
        try:
            major, minor, *_ = [int(x) for x in tf_version.split(".")]
            if (major, minor) >= (2, 11):
                print("\n[ADVERTENCIA] En Windows nativo, TensorFlow >= 2.11 no tiene soporte GPU.")
                print("Use WSL2 para GPU o cambie a TF <= 2.10 si quiere GPU en Windows nativo.")
        except Exception:
            pass
    # ¿TensorFlow fue compilado con soporte CUDA?
    print("\nSoporte CUDA en el binario de TensorFlow:")
    try:
        built_with_cuda = tf.test.is_built_with_cuda()
    except Exception:
        built_with_cuda = False
    print(f"  tf.test.is_built_with_cuda(): {built_with_cuda}")

    # Dispositivos detectados por TF
    print("\nDetección de GPUs por TensorFlow:")
    gpus = tf.config.list_physical_devices("GPU")
    if gpus:
        for i, gpu in enumerate(gpus):
            print(f"  GPU {i}: {gpu}")
        # Memory growth para evitar reservación total
        for gpu in gpus:
            try:
                tf.config.experimental.set_memory_growth(gpu, True)
            except Exception:
                pass
    else:
        print("No se detectó GPU con TensorFlow.")

    # nvidia-smi
    header("Información de la GPU (nvidia-smi)")
    ok, smi = run_cmd(["nvidia-smi"])
    if ok:
        print(smi)
    else:
        print("nvidia-smi no disponible o sin driver NVIDIA:", smi)

    # nvcc --version (opcional; no es obligatorio para usar TF)
    header("Versión de CUDA Toolkit (nvcc --version)")
    ok, nvcc_out = run_cmd(["nvcc", "--version"])
    cuda_toolkit = None
    if ok:
        print(nvcc_out)
        cuda_toolkit = parse_nvcc_version(nvcc_out)
        if cuda_toolkit:
            print(f"CUDA Toolkit detectado: {cuda_toolkit}")
    else:
        print("nvcc no encontrado (no es necesario para usar TensorFlow con GPU).")

    # cuDNN
    header("Verificación de cuDNN")
    cudnn_paths, cudnn_header_version = find_cudnn()
    if cudnn_paths:
        print("Archivos cuDNN detectados:")
        for p in sorted(set(cudnn_paths)):
            print("  -", p)
    else:
        print("No se encontraron binarios de cuDNN en rutas típicas.")
    if cudnn_header_version:
        print(f"Versión cuDNN (cabecera): {cudnn_header_version}")
    else:
        print("No se pudo inferir la versión de cuDNN desde las cabeceras.")

    # Tabla de compatibilidad (resumida y corregida)
    compat = {
        "2.10": {"cuda": "11.2", "cudnn": "8.1"},
        "2.11": {"cuda": "11.2", "cudnn": "8.1"},
        "2.12": {"cuda": "11.8", "cudnn": "8.6"},
        "2.13": {"cuda": "11.8", "cudnn": "8.6"},
        "2.14": {"cuda": "11.8", "cudnn": "8.6"},
        # 2.15 y superiores migran a rama CUDA 12.x y cuDNN 8.9+
        "2.15": {"cuda": "12.x", "cudnn": "8.9+"},
    }

    # Hallar clave mayor.menor de TF
    tf_mm = ".".join(tf_version.split(".")[:2])

    header("Compatibilidad entre versiones")
    if tf_mm in compat:
        exp = compat[tf_mm]
        print(f"Requisitos esperados para TensorFlow {tf_mm}: CUDA {exp['cuda']} y cuDNN {exp['cudnn']}")
        if cuda_toolkit:
            if exp["cuda"].endswith("x"):
                print(f"Detectado CUDA Toolkit {cuda_toolkit}. Asegúrate de estar dentro de la rama {exp['cuda']}.")
            elif cuda_toolkit == exp["cuda"]:
                print("La versión de CUDA Toolkit coincide con la esperada.")
            else:
                print(f"Versión de CUDA Toolkit detectada ({cuda_toolkit}) no coincide con la esperada ({exp['cuda']}).")
        else:
            print("No se pudo verificar CUDA Toolkit (nvcc ausente).")
        if cudnn_header_version:
            # Compara solo mayor.minor
            want = exp["cudnn"].rstrip("+")
            if want:
                want_mm = ".".join(want.split(".")[:2])
                got_mm = ".".join(cudnn_header_version.split(".")[:2])
                if got_mm == want_mm or exp["cudnn"].endswith("+"):
                    print("La versión de cuDNN parece compatible.")
                else:
                    print(f"cuDNN detectado {cudnn_header_version} difiere de lo esperado ({exp['cudnn']}).")
        else:
            print("No se pudo verificar la versión de cuDNN.")
    else:
        print("No hay tabla local para esta versión de TensorFlow. Consulta la guía oficial.")

    # Demostración en GPU
    header("Prueba de ejecución en /GPU:0")
    try:
        if gpus:
            with tf.device("/GPU:0"):
                a = tf.random.normal([1024, 1024])
                b = tf.random.normal([1024, 1024])
                c = tf.matmul(a, b)
                print("MatMul en GPU ejecutado. Resultado:", c.shape)
        else:
            print("No hay GPU visible para ejecutar la prueba.")
    except Exception as e:
        print("Falló la prueba en GPU:", e)

    # Nota sobre nvidia-smi vs nvcc
    header("Nota sobre versiones de CUDA (driver vs toolkit)")
    print("* 'nvidia-smi' muestra la versión de CUDA soportada por el DRIVER (máximo compatible).")
    print("* 'nvcc --version' muestra la versión del CUDA TOOLKIT instalado (compilador y libs).")
    print("Estas versiones pueden diferir y no necesariamente indican un problema.")

if __name__ == "__main__":
    main()