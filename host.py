#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gevent import monkey; monkey.patch_all()

import bottle, os.path
#from webtesting.storage.storage import storapp
import mimetypes
 
app = bottle.Bottle()

def make(dir='./'):
    dir = os.path.abspath(dir)
    x = "<ul class=\"fa-ul no-dot\" style='--fa-li-margin: 2em; margin-bottom: 0.25rem;'>"
    y = 0
    for entry in sorted(os.scandir(dir), key=lambda x: not x.is_dir()):
        y+=1
        if entry.is_file() and not entry.name.endswith(".tpl.html") and not entry.name.startswith("."):
            x += f"<li><span class=\"fa-li\"><i class=\"fa-regular fa-fw fa-file\"></i></span><a href=\"/{os.path.relpath(entry.path)[0:]}\""+("target='_blank'" if not entry.name.endswith('.html') else '')+f">{entry.name}</a></li>"
        elif entry.is_dir() and not (entry.name.startswith(".") or entry.name.endswith("__pycache__") or entry.name == "node_modules"):
            print(entry.name)
            x += f"<li><span class=\"click\"><span class=\"fa-li\"><i class=\"fa-solid fa-fw fa-folder-open\"></i></span>{entry.name}</span><br>"
            x += make(entry.path)
            x += "</li>"
    if y == 0:
        x += "<li style=\"margin-left: -1.5em;\" class=\"empty\"><i>(empty)</i></li>"
    x += "</ul>"
    return x

@app.hook('before_request')
def no_drive():
    if not os.path.exists('.'):
        bottle.abort(503, "Website Offline :(")

@app.hook('after_request')
def cacheit():
    bottle.response.headers['Cache-Control'] = 'public, max-age=31536000'

@app.error(503)
def offline(error):
    return bottle.template("""<!DOCTYPE html>
<html lang="en-us">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Offline</title>
        <style>
            body {
                font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            }
        </style>
    </head>
    <body>
        <h1>{{error.body}}</h1>
    </body>
</html>""", error=error)

@app.route("/")
def index():
    return bottle.template("./index.tpl.html")

@app.route("/nav")
def nav():
    return bottle.template("./nav.tpl.html", make=make)

@app.route("/<path:path>")
def static(path):
    if path.startswith('storage'):
        return

    print(path)
    if path.strip("/").endswith(".tpl.html"):
        bottle.abort(404, "Not Found")
    if not os.path.isfile(path):
        if os.path.exists(path + ".html"):
            bottle.redirect(path.split("/")[-1] + ".html", 302)
        if os.path.exists(path + "/index.html"):
            bottle.redirect(path.split("/")[-1] + "/index.html", 302)
    return bottle.static_file(path, root='./')



#app.mount('/storage', storapp)

app.run(host='localhost',port=8070, debug=True, server='gevent')
