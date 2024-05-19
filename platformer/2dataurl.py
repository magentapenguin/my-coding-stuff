import base64, mimetypes, re, os.path, tempfile

def dataurl(mime, data):
    return 'data:%s;base64,%s' % (mime, base64.b64encode(data).decode('ascii'))

def dataurl_from_file(filename, fatal=False):
    mime, _ = mimetypes.guess_type(filename)
    print('Mime:', mime)
    try:
        with open(filename, 'rb') as f:
            return dataurl(mime, f.read())
    except FileNotFoundError as e:
        if fatal:
            raise e from e
        else:
            print('Warning: file not found:', filename)
            return e
    
def find_comments(s, filetype='js'):
    if filetype == 'js':
        return re.findall(r'//(.*)', s)
    elif filetype == 'html':
        return re.findall(r'<!--(.*?)-->', s, re.DOTALL)
    elif filetype == 'css':
        return re.findall(r'/\*(.*?)\*/', s, re.DOTALL)
    
def convert2dataurl(s, filetype='js', fatal=False):
    comments = find_comments(s, filetype)
    for comment in comments:
        if comment.strip().startswith('2dataurl'):
            code = comment.split('2dataurl')[1].strip()
            if code.startswith('->'):
                filename = code.split('->')[1].strip()
                print('Converting:', filename)
                x = filename
                
                if mimetypes.guess_type(filename)[0].startswith('text') or mimetypes.guess_type(filename)[0].startswith('application/javascript'):
                    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.'+os.path.split(filename)[1].split('.')[1]) as f, open(filename, 'r') as g:
                        f.write(g.read())
                        f.close()
                        x = run(f.name, os.path.abspath(os.path.split(filename)[0]))
                        os.unlink(f.name)
                    print('New file:', x)
                dataurl = dataurl_from_file(x, fatal)
                if isinstance(dataurl, Exception):
                    print('Error:', dataurl)
                    continue
                s = s.replace(comment, '')
                s = s.replace(filename, dataurl)
    if filetype == 'html':
        s = s.replace('data-exitbtn="true"', 'data-exitbtn="false"')
    return s

def runfunc_on_file(filename, func, newfile=False, cwd=None, args=(), kwargs={}):
    with open(filename, 'r') as f:
        s = f.read()
    olddir = os.getcwd()
    if cwd:
        os.chdir(cwd)
    else:
        os.chdir(os.path.abspath(os.path.split(filename)[0]))
    s = func(s, *args, **kwargs)
    if newfile:
        x = os.path.split(filename)[0]
        y = os.path.split(filename)[1]
        filename = os.path.join(x, y.split('.')[0] + '_new.' + y.split('.')[1])
    os.chdir(olddir)
    with open(filename, 'w') as f:
        f.write(s)
    return filename

def run(mode, filename, cwd=None):
    if mode == "quick":
        x = dataurl_from_file(filename)
        if len(x) >= 2000:
            print("Url too large, saved to file.")
            with open("saveddataurl.txt", 'w') as f:
                f.write(x)
        else:
            print(x)
        
    elif mode == "full":
        return runfunc_on_file(
            filename,
            convert2dataurl,
            newfile=True,
            cwd=cwd,
            args=(os.path.split(filename)[1].split('.')[1],)
        )


if __name__ == '__main__':
    import sys
    run(*sys.argv[1:])