import hashlib
import bottle, os, base64, inspect
from bottle_websocket import GeventWebSocketServer
from bottle_websocket import websocket
import redis, json, gevent
import geventwebsocket.exceptions
import bottle_session
from passlib.context import CryptContext
import datetime


pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
)

##########################
# THIS NOT MY CODE
# I copied it from bottle_redis.py
# All credits to the original author
# It had a bug that I need fixed to use it

import inspect

# removed import to PluginError, and __version__ as they could cause conflicts with this file


class RedisPlugin(object):
    name = "redis"
    api = 2

    def __init__(self, keyword="rdb", *args, **kwargs):
        self.keyword = keyword
        self.redisdb = None
        self.db = kwargs.get("db", 0)
        self.args = args
        self.kwargs = kwargs

    def setup(self, app):
        for other in app.plugins:
            if not isinstance(other, RedisPlugin):
                continue
            if other.keyword == self.keyword:
                raise bottle.PluginError(
                    "Found another redis plugin with "
                    "conflicting settings (non-unique keyword)."
                )
        if self.redisdb is None:
            self.redisdb = redis.ConnectionPool(*self.args, **self.kwargs)

    def apply(self, callback, route):
        # hack to support bottle v0.9.x
        if bottle.__version__.startswith("0.9"):
            config = route["config"]
            _callback = route["callback"]
        else:
            config = route.config
            _callback = route.callback

        conf = config.get("redis") or {}
        args = inspect.getfullargspec(_callback)[
            0
        ]  # modified from inspect.getargspec(_callback)[0]
        keyword = conf.get("keyword", self.keyword)
        if keyword not in args:
            return callback

        def wrapper(*args, **kwargs):
            kwargs[self.keyword] = redis.Redis(connection_pool=self.redisdb, db=self.db)
            rv = callback(*args, **kwargs)
            return rv

        return wrapper


# End of copied code
##########################


class Settings:
    def __init__(self):
        self.title = 'Chat'
    
    def prefix_title(self, prefix):
        return prefix + self.title

class CSPPlugin(object):
    name = "csp"
    api = 2

    def __init__(self, keyword="nonce", report_to=None):
        self.keyword = keyword
        self.report_to = report_to

    def setup(self, app):
        for other in app.plugins:
            if not isinstance(other, CSPPlugin):
                continue
            if other.keyword == self.keyword:
                raise bottle.PluginError(
                    "Found another csp plugin with "
                    "conflicting settings (non-unique keyword)."
                )

    def apply(self, callback, route):
        _callback = route.callback

        args = inspect.getfullargspec(_callback)[
            0
        ]
        keyword = self.keyword
        if keyword not in args:
            return callback

        def wrapper(*args, **kwargs):
            nonce = base64.b64encode(os.urandom(16)).decode("ascii")
            kwargs[self.keyword] = nonce
            bottle.response.add_header("Content-Security-Policy", f"default-src 'self'; connect-src 'self' wss://* ws://*; img-src *; script-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net; style-src 'self' 'nonce-{nonce}' 'sha256-drmNCjF3KdeG1e+w66sn1p7Ref5nZw1izM7ec4h3ejY=';" + (f"report-uri {self.report_to}" if self.report_to else ""))
            
            rv = callback(*args, **kwargs)
            return rv

        return wrapper

settings = Settings()

bottle.install(CSPPlugin())

session_plugin = bottle_session.SessionPlugin(
    cookie_secure=True, cookie_httponly=True, cookie_lifetime=60 * 60 * 24 * 7, cookie_name="session"
)
redis_plugin = RedisPlugin(db=1)


connection_pool = redis.ConnectionPool(host="localhost", port=6379, db=1)

session_plugin.connection_pool = connection_pool
redis_plugin.redisdb = connection_pool
bottle.install(session_plugin)
bottle.install(redis_plugin)

bottle.TEMPLATE_PATH.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/views')

@bottle.route('/ws')
def websocketchat(nonce):
    bottle.response.content_type = 'text/html'
    return bottle.template('ws-chat.tpl.html', settings=settings, nonce=nonce)

@bottle.route('/user')
def user(nonce, rdb, session):
    return bottle.template('user.tpl.html', settings=settings, nonce=nonce, user=api_user(rdb, session))

@bottle.route('/ws/socket', apply=[websocket])
def handle_websocket(ws, rdb: redis.Redis):

    sub = rdb.pubsub()
    sub.subscribe('chat')
    first = True
    try:
        while True:
            msg = None
            with gevent.Timeout(0.5, False):
                msg = ws.receive()
            
            
            if (msgs := rdb.lrange('chat', 0, -1)) and first:
                first = False
                print(msgs)
                for m in msgs:
                    print(json.loads(m.decode('utf-8')))
                    ws.send(m.decode('utf-8'))

            if msg is not None:
                msg = json.loads(msg) if isinstance(msg, (str, bytes, bytearray)) else msg
                print(msg)
                if msg['type'] == 'message':
                    rdb.rpush('chat', json.dumps(msg))
                    rdb.publish('chat', json.dumps(msg))
                elif msg['type'] == 'ping':
                    ws.send(json.dumps({'type': 'pong'}))
            
            # Look for new messages
            while m := sub.get_message(True):
                if m['type'] == 'message':
                    ws.send(m['data'].decode('utf-8'))
                    
    except Exception as e:
        if isinstance(e, geventwebsocket.exceptions.WebSocketError):
            print('Client disconnected')
        else:
            import traceback
            traceback.print_exc()
    finally:
        try:
            ws.close()
        except:
            pass

def make_session_token(user: str, rdb: redis.Redis) -> str:
    """
    Generate a session token for the given user and store it in the Redis database.

    Args:
        user (str): The username for which the session token is generated.
        rdb (redis.Redis): The Redis database connection object.

    Returns:
        str: The generated session token.

    """
    token = (hashlib.sha256(user.encode()).digest() + os.urandom(16)).hex() + '$' + datetime.datetime.now().isoformat()
    rdb.hset('tokens', user, token)
    return token


def validate_session_token(session: bottle_session.Session, rdb: redis.Redis) -> bool:
    """
    Validate the session token stored in the session object.

    Args:
        session (bottle_session.Session): The session object.
        rdb (redis.Redis): The Redis database connection object.

    Returns:
        bool: True if the session token is valid, False otherwise.

    """
    user = session.get('user')
    token = session.get('token')
    if not user or not token or not rdb.hexists('tokens', user):
        return False
    
    return token == rdb.hget('tokens', user).decode() and token[:64] == hashlib.sha256(user.encode()).hexdigest() and datetime.datetime.fromisoformat(token.split('$')[1]) > datetime.datetime.now() - datetime.timedelta(days=7)

@bottle.route('/p2p')
def p2pchat(nonce):
    bottle.response.content_type = 'text/html'
    return bottle.template('p2p-chat.tpl.html', settings=settings, nonce=nonce)

@bottle.route('/static/<filename:path>')
def static(filename):
    return bottle.static_file(filename, root=os.path.dirname(os.path.abspath(__file__)) + '/static')

@bottle.route('/api/user')
def api_user(rdb: redis.Redis, session, abort=True):
    if not validate_session_token(session, rdb):
        if abort:
            bottle.abort(401, 'Unauthorized')
        return None
    
    user = json.loads(rdb.hget('users',session['user']).decode())
    # Remove the hash from the user object
    user.pop('hash')
    user['name'] = session['user']
    return user

@bottle.route('/api/login', method=['POST','GET'])
def api_login(rdb: redis.Redis, session):
    if bottle.request.method == 'GET' and validate_session_token(session, rdb):
        bottle.redirect('/user')
    data = dict(bottle.request.forms)
    if not data or not isinstance(data, dict) or 'username' not in data or 'password' not in data:
        bottle.abort(400, 'Bad Request')
    user = data['username']
    # if the username is an email, convert it to a username
    if '@' in user:
        # Search for the user with the email
        d = rdb.hgetall('users')
        for u,d in zip(d,d):
            d = d.decode()
            d = rdb.hget('users', d).decode()
            d = json.loads(d)
            print(u,d)
            if d.get('email',False) == user:
                print('Found user with email')
                user = u.decode()
                break

    password = data['password']
    if pwd_context.verify(password, json.loads(rdb.hget('users', user))['hash']):
        session['user'] = user
        session['token'] = make_session_token(user, rdb)
        bottle.redirect('/user')
    else:
        bottle.abort(401, 'Unauthorized')

@bottle.route('/api/newuser', method=['POST','GET'])
def api_newuser(rdb: redis.Redis, session):
    data = dict(bottle.request.forms)
    if not data or not isinstance(data, dict) or 'username' not in data or 'password' not in data:
        bottle.abort(400, 'Bad Request')
    user = data['username']
    password = data['password']
    if rdb.hexists('users', user):
        bottle.abort(409, 'Conflict')
    rdb.hset('users', user, json.dumps({'hash': pwd_context.hash(password), 'created': datetime.datetime.now().isoformat(), 'email': data.get('email', ''), 'photoURL': 'https://gravatar.com/avatar/'+hashlib.sha256(user.encode()).hexdigest()+'?d=mp'}))
    session['user'] = user
    session['token'] = make_session_token(user, rdb)
    bottle.redirect('/user')

@bottle.route('/api/logout')
def api_logout(session, rdb: redis.Redis):
    session.delete()
    rdb.hdel('tokens', session['user'])
    bottle.redirect('/')

@bottle.route('/api/icanhasuser', method='GET')
def api_icanhasuser(rdb: redis.Redis, session):
    # Check if the user exists
    user = bottle.request.query.get('user')
    if not user:
        bottle.abort(400, 'Bad Request')
    return {'exists': rdb.hexists('users', user)}


def alert(rdb: redis.Redis, message: str):
    "Indicate something that staff should be aware of, or that requires their attention."
    date = datetime.datetime.now().isoformat()
    rdb.hset('alerts', date+'-'+hashlib.sha256(message.encode()).hexdigest(), date)

@bottle.route('/login')
def login(nonce):
    return bottle.template('login.tpl.html', settings=settings, login=True, nonce=nonce)

@bottle.route('/register')
def register(nonce):
    return bottle.template('login.tpl.html', settings=settings, login=False, nonce=nonce)

@bottle.route('/')
def index(nonce):
    return bottle.template('index.tpl.html', settings=settings, nonce=nonce)

err401tmplt = \
"""<!DOCTYPE html>
<html>
<head>
    <title>{{settings.title}}</title>
    <link rel="stylesheet" href="/static/styles.css">
    <link rel="prefetch" href="https://www.gravatar.com/avatar/000000000000000000000000000000000000000000000000000000?d=mp" as="image">
    <script src="/static/user-scripts.js" type="module"></script>
</head>
<body>
    <main>
        <user-cfg></user-cfg>
        <h1>You need to be logged in!</h1>
        <p>
        <a href="/">Home</a> | <a id="back" href="#">Back</a>
        <br>
        <a href="/login">Login</a> or <a href="/register">make an account</a>!
        </p>
        <p>401 Unauthorized</p>
        <script>
            document.getElementById('back').addEventListener('click', () => {
                window.history.back();
            });
        </script>
    </main>
</body>
</html>"""
                              

@bottle.error(401)
def error401(error):
    return bottle.template(err401tmplt, settings=settings)


bottle.run(host='localhost', port=8080, server=GeventWebSocketServer, debug=True)