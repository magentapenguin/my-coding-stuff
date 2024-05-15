import base64, mimetypes, re, os.path

def dataurl(mime, data):
    return 'data:%s;base64,%s' % (mime, base64.b64encode(data).decode('ascii'))

def dataurl_from_file(filename, fatal=False):
    mime, _ = mimetypes.guess_type(filename)
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
                if mimetypes.guess_type(filename)[0].startswith('text'):
                    x = run(filename)
                dataurl = dataurl_from_file(x, fatal)
                if isinstance(dataurl, Exception):
                    print('Error:', dataurl)
                    continue
                s = s.replace(comment, '')
                s = s.replace(filename, dataurl)
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

def run(filename, cwd=None):
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