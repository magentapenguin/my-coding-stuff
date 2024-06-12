#!/usr/bin/env python
# -*- coding: utf-8 -*-
import gevent.monkey
gevent.monkey.patch_all()
import bottle, os, time, threading


curdir = os.path.dirname(__file__)
 
app = bottle.Bottle()

@app.route("/receive/<user>", method="POST")
def receive(user):
    #if user == "s-isaabrown":
    #    bottle.abort(400)
    with open(curdir+"/"+user+".png", "wb") as f:
        f.write(bottle.request.body.read())
    bottle.abort(200)

@app.route("/img/<user>", method=["GET","DELETE"])
def img(user):
    if bottle.request.method == "DELETE":
        os.remove(curdir+"/"+user+".png")
        return "Deleted"
    return bottle.static_file(user+".png", root=curdir+"/")

@app.route("/", method="GET")
def root():
    return """<style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f0f0f0;
            color: #000;
        }
        @media (prefers-color-scheme: dark) {
            body {
                background-color: #333;
                color: #fff;
            }
        }</style><a href=\"/index\">EEEE</a>"""

@app.route("/index", method="GET")
@bottle.auth_basic(lambda x, y: x=="admin" and y=="8b4deed4cb3de96de2e648bd754f06ee")
def index():
    users = []
    for file in os.listdir(curdir+"/"):
        if file.endswith(".png"):
            users.append(file[:-4])
    return bottle.template(curdir+"/index.html", users=users)

@app.route("/users", method="GET")
def users():
    users = []
    for file in os.listdir(curdir+"/"):
        if file.endswith(".png"):
            users.append(file[:-4])
    return {'users':users}

app.run(debug=True, reloader=True, server="gevent")