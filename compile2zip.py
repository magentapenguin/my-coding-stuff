import zipfile, os, sys
import colorama, time

def zipdir(path, zip, exlude=[]):
    for root, dirs, files in os.walk(path):
        for file in files:
            if any([file.endswith(ext) for ext in exlude]):
                continue
            print("Adding %s" % os.path.join(root, file), end='... ')
            with open(os.path.join(root, file), 'rb') as src, zip.open(os.path.join(root, file)[2:], 'w') as dst:
                x = src.read()
                if file.endswith('.html') or file.endswith('.js') or file.endswith('.css'):
                    x = x.decode('utf-8')
                    x = x.replace('\r\n', '\n').replace('\r', '\n')
                    if file.endswith('.html'):
                        x = x.replace('data-exitbtn="true"', 'data-exitbtn="false"')
                    x = x.encode('utf-8')
                dst.write(x)
                print(colorama.Fore.GREEN + "OK" + colorama.Style.RESET_ALL)

def main():
    if len(sys.argv) < 2:
        print("Usage: python compile2zip.py <source> <destination>")
        sys.exit(1)
    source = sys.argv[1]
    if not os.path.isdir(source):
        print("Source must be a directory")
        sys.exit(1)
    if len(sys.argv) < 3:
        destination = source + ".zip"
    else:
        destination = sys.argv[2]
    zipf = zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED)
    zipdir(source, zipf, [".py",".md",".zip"])
    zipf.close()

if __name__ == "__main__":
    main()