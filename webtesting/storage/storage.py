import bottle_session
import os
import bottle, re, hashlib
import redis, webauthn, base64, dataclasses
from json import loads, dumps, JSONDecoder, JSONEncoder
from datetime import datetime, timedelta

app = bottle.Bottle()

##########################
# THIS NOT MY CODE
# I copied it from bottle_redis.py
# All credits to the original author

import inspect
from bottle import __version__, PluginError


class RedisPlugin(object):
    name = "redis"
    api = 2

    def __init__(self, keyword="rdb", *args, **kwargs):
        self.keyword = keyword
        self.redisdb = None
        self.args = args
        self.kwargs = kwargs

    def setup(self, app):
        for other in app.plugins:
            if not isinstance(other, RedisPlugin):
                continue
            if other.keyword == self.keyword:
                raise PluginError(
                    "Found another redis plugin with "
                    "conflicting settings (non-unique keyword)."
                )
        if self.redisdb is None:
            self.redisdb = redis.ConnectionPool(*self.args, **self.kwargs)

    def apply(self, callback, route):
        # hack to support bottle v0.9.x
        if __version__.startswith("0.9"):
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
            kwargs[self.keyword] = redis.Redis(connection_pool=self.redisdb)
            rv = callback(*args, **kwargs)
            return rv

        return wrapper


# End of copied code
##########################


class Base64Encoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return base64.b64encode(obj).decode("ascii")
        # Let the base class default method raise the TypeError
        return super().default(obj)


class Base64Decoder(JSONDecoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, object_hook=self.object_hook, **kwargs)

    def object_hook(self, obj):
        if "b64" in obj.keys():
            return base64.b64decode(obj["b64"])
        return obj


curdir = os.path.relpath(os.path.dirname(__file__))

session_plugin = bottle_session.SessionPlugin()
redis_plugin = RedisPlugin()

connection_pool = redis.ConnectionPool(host="localhost", port=6379)

session_plugin.connection_pool = connection_pool
redis_plugin.redisdb = connection_pool
app.install(session_plugin)
app.install(redis_plugin)


@app.route("/")
def index(session, rdb):
    return bottle.template(
        curdir + "/index.tpl.html", session=session, rdb=rdb, curdir=curdir, loggedin="user" in session
    )


@app.route("/canihave/user/<user>")
def canihaveuser(user, session, rdb):
    data = loads(rdb.get("users"), cls=Base64Decoder)
    if user in data.keys():
        return {"output": False}
    else:
        return {"output": True}


@app.route("/auth", method=["GET", "POST"])
@app.route("/auth/", method=["GET", "POST"])
def auth(session, rdb):
    bottle.response.content_type = "application/json"
    if bottle.request.method == "POST":
        data = bottle.request.json
        if not re.match(r"[0-9a-zA-Z]{3,20}", data["username"]):
            bottle.abort(400, "Invalid username")
        registration_verification = webauthn.verify_registration_response(
            credential=data["credential"],
            expected_challenge=webauthn.base64url_to_bytes(
                loads(session["challenge"])[1]
            ),
            expected_origin="https://bookish-system-jgvv7pxj96wh5wjq-8080.app.github.dev",
            expected_rp_id="bookish-system",
            require_user_verification=True,
        )

        session["challenge"] = "[null, null]"

        if registration_verification:
            users = loads(rdb.get("users"), cls=Base64Decoder)
            if not canihaveuser(data["username"], session=session, rdb=rdb)["output"]:
                print("User already exists")
                bottle.abort(400, "User already exists")
            users[data["username"]] = dataclasses.asdict(registration_verification)
            rdb.set("users", dumps(users, cls=Base64Encoder))
            return
    else:
        session["challenge"] = dumps(
            challenge := [
                datetime.now().isoformat(),
                base64.b64encode(os.urandom(256), b"--").decode("utf-8"),
            ]
        )
        return {"challenge": challenge[1]}


def make_session_token(user: str, rdb) -> str:
    token = (hashlib.sha256(user.encode()) + os.urandom(16)).hex()
    tokens = loads(rdb.get("tokens"))
    tokens[user] = [token, datetime.now().isoformat()]
    return token


def validate_session_token(token, user, rdb):
    tokens = loads(rdb.get("tokens"))
    if user in tokens:
        if (
            tokens[user][0] == token
            and datetime.fromisoformat(tokens[user][1]) + timedelta(seconds=60 * 60)
            > datetime.now()
            and hashlib.sha256(user.encode()) == bytes.fromhex(token)[:-16]
        ):
            return True
    return False


@app.route("/login", method=["POST"])
@app.route("/login/", method=["POST"])
def login(session, rdb):
    data = bottle.request.json
    users = loads(rdb.get("users"), cls=Base64Decoder)

    def find_user(credid):
        for key, user in users.items():
            print(
                user["credential_id"]
                .replace("/", "_")
                .replace("=", "")
                .replace("+", "-"),
                credid,
            )
            if (
                user["credential_id"]
                .replace("/", "_")
                .replace("=", "")
                .replace("+", "-")
                == credid
            ):
                return key
        return None

    if user := find_user(data["id"]):
        authentication_verification = webauthn.verify_authentication_response(
            credential=data,
            expected_challenge=webauthn.base64url_to_bytes(
                loads(session["challenge"])[1]
            ),
            expected_rp_id="bookish-system",
            expected_origin="https://bookish-system-jgvv7pxj96wh5wjq-8080.app.github.dev",
            credential_public_key=webauthn.base64url_to_bytes(
                users[user]["credential_public_key"]
            ),
            credential_current_sign_count=users[user]["sign_count"],
            require_user_verification=True,
        )
        users[user]["sign_count"] = authentication_verification.new_sign_count
        rdb.set("users", dumps(users, cls=Base64Encoder))
        session["challenge"] = "[null, null]"
        session["token"] = make_session_token(user, rdb)
        session["user"] = user
    else:
        print("User not found")
        bottle.abort(400, "User not found")



storapp = app
