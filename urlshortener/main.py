import os
import bottle, secrets, redis

app = bottle.Bottle()

os.chdir(os.path.dirname(__file__))

bottle.TEMPLATE_PATH.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Connect to Redis
r = redis.StrictRedis(host='localhost', port=6379, db=3)

@app.route('/api/shorten', method='POST')
def shorten():
    url = bottle.request.json['url']
    shortened = shorten_url(url)
    return {'key': shortened}

def shorten_url(url):
    key = secrets.token_urlsafe(4)
    r.hset('urls', key, url)
    return key

@app.route('/api/expand/<key>')
def expand(key):
    url = r.hget('urls', key)
    if url:
        return {'url': url.decode()}
    else:
        bottle.abort(404)

@app.route('/api/urls', method='GET')
def urls():
    urls = r.hgetall('urls')
    print(urls)
    return {key.decode(): url.decode() for key, url in urls.items()}

@app.route('/form/shorten')
def shorten_form():
    url = bottle.request.query.url
    url = shorten_url(url)
    return bottle.template('shorten.tpl.html', root='.', url=url)

@app.route('/<key>')
def redirect(key):
    url = r.hget('urls', key)
    if url:
        bottle.redirect(url.decode(), 301)
    else:
        bottle.abort(404)


@app.route('/')
def index():
    return bottle.template('index.tpl.html', root='.')

@app.route('/static/<filename>')
def static(filename):
    return bottle.static_file(filename, root='./static')


if __name__ == '__main__':
    app.run(host='localhost', port=5000)
