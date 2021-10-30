import subprocess
import os


class PNGQUANT_NotFound(Exception):
    def __init__(self):
        super().__init__("pngquant not found. Please install pngquant.")


def compress_png_lossy(img_path, quality = 1, postfix="_compressed"):
    head, tail = os.path.split(img_path)
    root, ext = os.path.splitext(tail)

    out_file_name = root + postfix + ext
    out_file_path = os.path.join(head, out_file_name)

    if os.path.exists(out_file_path):
        os.remove(out_file_path)

    try:
        p = subprocess.Popen(["pngquant", "--quality", str(quality), "--ext", postfix + ".png", img_path])
        p.wait()
    except FileNotFoundError:
        raise PNGQUANT_NotFound()

