import bottle, os

@bottle.hook('after_request')
def no_drive():
    if not os.path.exists('.'):
        bottle.abort(503, "Website Offline :(")

@bottle.error(503)
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

@bottle.route('/')
def index():
    return bottle.template('./index.html')


@bottle.route('/<file:path>')
def static(file):
    return bottle.static_file(file, root='.')

bottle.run(host='localhost', port=8080, debug=True)
