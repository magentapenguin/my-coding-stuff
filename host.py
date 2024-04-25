import bottle, os.path

@bottle.route("/")
def index():
    return bottle.template("./index.html")

@bottle.route("/<path:path>")
def static(path):
    return bottle.static_file(path, root='./')

bottle.run(host='localhost',port=8080)
