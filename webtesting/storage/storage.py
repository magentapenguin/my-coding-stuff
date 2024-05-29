import bottle_session
import os
import s3fs
import bottle
import re
import hashlib
import redis
import webauthn
import base64
import dataclasses
from json import loads, dumps, JSONDecoder, JSONEncoder
from datetime import datetime, timedelta
from typing import Any
from Crypto.Cipher import AES

def loadfile(file: bytes, filename: str) -> tuple[bytes, str]:
    if not filename.endswith(".bin"):
        return file, filename
    key = os.getenv("AES_KEY").encode()
    tag = file[16:]
    nonce = file[16:16+15]
    cipher = AES.new(key, AES.MODE_OCB, nonce=nonce)
    data = cipher.decrypt_and_verify(file, tag)
    return data, filename.lstrip(".bin")

def savefile(file: bytes, filename: str) -> tuple[bytes, str]:
    if filename.endswith(".bin"):
        return file, filename
    key = os.getenv("AES_KEY").encode()
    cipher = AES.new(key, AES.MODE_OCB)
    data, tag = cipher.encrypt_and_digest(file)
    return tag+cipher.nonce+data, filename + ".bin"

app = bottle.Bottle()

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
            kwargs[self.keyword] = redis.Redis(connection_pool=self.redisdb)
            rv = callback(*args, **kwargs)
            return rv

        return wrapper


# End of copied code
##########################


class Base64Encoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return {"b64": base64.b64encode(obj).decode("ascii")}
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

session_plugin = bottle_session.SessionPlugin(cookie_secure=True, cookie_httponly=True, cookie_lifetime=60*60*24*7) # 7 days
redis_plugin = RedisPlugin()

connection_pool = redis.ConnectionPool(host="localhost", port=6379)

session_plugin.connection_pool = connection_pool
redis_plugin.redisdb = connection_pool
app.install(session_plugin)
app.install(redis_plugin)

s3 = s3fs.S3FileSystem(
    key=os.getenv("AWS_S3_ACCESS_KEY"),
    secret=os.getenv("AWS_S3_SECRET_KEY"),
)
try:
    s3.mkdir("bookishsystem/bookish-system")
except FileExistsError:
    pass

@app.route("/")
def index(session, rdb):
    if bottle.request.query.get("logout") is not None:
        session["token"] = ""
        session["user"] = ""
        print("Logged out", session.get("token"), session.get("user"))
        bottle.redirect("/storage")
    return bottle.template(
        curdir + "/index.tpl.html",
        curdir=curdir,
        session=session,
        rdb=rdb,
        loggedin=validate_session_token(session.get("token"), session.get("user"), rdb),
    )


@app.route("/home")
def home(session, rdb):
    if bottle.request.query.get("delete") is not None and validate_session_token(
        session.get("token"), session.get("user"), rdb
    ):
        print("Deleting Account", session.get("user"))
        users = loads(rdb.get("users"), cls=Base64Decoder)
        del users[session.get("user")]
        rdb.set("users", dumps(users, cls=Base64Encoder))
        
        tokens = loads(rdb.get("tokens"))
        del tokens[session.get("user")]
        rdb.set("tokens", dumps(tokens))
    return bottle.template(
        curdir + "/home.tpl.html",
        session=session,
        curdir=curdir,
        loggedin=validate_session_token(session.get("token"), session.get("user"), rdb),
    )


@app.route("/status")
def status(session, rdb):
    return bottle.template(
        curdir + "/status.tpl.html",
        session=session,
        curdir=curdir,
        loggedin=validate_session_token(session.get("token"), session.get("user"), rdb),
    )


@app.route("/terms")
def terms(session, rdb):
    return bottle.template(
        curdir + "/terms.html",
        session=session,
        curdir=curdir,
        loggedin=validate_session_token(session.get("token"), session.get("user"), rdb),
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
        if not re.match(r"[0-9a-zA-Z]{3,20}", data["username"]) or canihaveuser(data["username"], session=session, rdb=rdb)["output"] is False:
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
            print("Creating user folder", data["username"],)
            s3.mkdir("bookishsystem/bookish-system/"+data["username"],)
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


def make_session_token(user: str, rdb: Any) -> str:
    """
    Generate a session token for the given user and store it in the Redis database.

    Args:
        user (str): The username for which the session token is generated.
        rdb (Any): The Redis database connection object.

    Returns:
        str: The generated session token.

    """
    token = (hashlib.sha256(user.encode()).digest() + os.urandom(16)).hex()
    tokens = loads(rdb.get("tokens"))
    tokens[user] = [token, datetime.now().isoformat()]
    rdb.set("tokens", dumps(tokens))
    return token


def validate_session_token(token: str, user: str, rdb: Any) -> bool:
    """
    Validates the session token for a given user.

    Args:
        token (str): The session token to validate.
        user (str): The user associated with the session token.
        rdb (Any): The Redis database connection object.

    Returns:
        bool: True if the session token is valid, False otherwise.
    """
    tokens = loads(rdb.get("tokens"))
    if user in tokens:
        if (
            tokens[user][0] == token
            and datetime.fromisoformat(tokens[user][1]) + timedelta(seconds=60 * 60)
            > datetime.now()
            and hashlib.sha256(user.encode()).digest() == bytes.fromhex(token)[:-16]
        ):
            return True
        else:
            del tokens[user]
            rdb.set("tokens", dumps(tokens))
    return False


@app.route("/login", method=["POST"])
@app.route("/login/", method=["POST"])
def login(session, rdb):
    data = bottle.request.json
    users = loads(rdb.get("users"), cls=Base64Decoder)

    def find_user(credid):
        for key, user in users.items():
            print(
                user["credential_id"],
                webauthn.base64url_to_bytes(credid),
            )
            if user["credential_id"] == webauthn.base64url_to_bytes(credid):
                return key
        return None

    if user := find_user(data["id"]):
        print(session.get("challenge"))
        authentication_verification = webauthn.verify_authentication_response(
            credential=data,
            expected_challenge=webauthn.base64url_to_bytes(
                loads(session["challenge"])[1]
            ),
            expected_rp_id="bookish-system",
            expected_origin="https://bookish-system-jgvv7pxj96wh5wjq-8080.app.github.dev",
            credential_public_key=users[user]["credential_public_key"],
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

@app.route("/storage", method=["GET", "DELETE", "PUT"])
def storage(session, rdb):
    #bottle.abort(401, "Unauthorized")
    user = session.get("user")
    if validate_session_token(session.get("token"), session.get("user"), rdb):
        if bottle.request.method == "GET":
            return {"files": s3.ls("bookishsystem/bookish-system/"+user)}
        elif bottle.request.method == "DELETE":
            data = bottle.request.json
            if modifyfile(data["file"], "delete"):
                return
            else:
                bottle.abort(404, "File not found")
        elif bottle.request.method == "PUT":
            data = bottle.request.json
            modifyfile(data["file"], "create")
            if modifyfile(data["file"], "write", data["data"]):
                return
            else:
                bottle.abort(404, "File not found")
    else:
        bottle.abort(401, "Unauthorized")


def modifyfile(file: str, how: str, data: Any = None) -> bool:
    if how == "delete":
        if s3.exists(file):
            s3.rm(file)
            return True
    elif how == "create":
        if not s3.exists(file):
            s3.touch(file)
            return True
    elif how == "rename":
        if s3.exists(file):
            s3.rename(file, data)
            return True
    elif how == "write":
        if s3.exists(file):
            with s3.open(file, "wb") as f: 
                f.write(data)
            return True
    return False


print(s3.ls("bookishsystem/bookish-system/"))

db = redis.Redis(connection_pool=connection_pool)
for user in loads(db.get("users"), cls=Base64Decoder):
    try:
        print("Creating user folder", user)
        s3.mkdir("bookishsystem/bookish-system/"+user+"/")
    except FileExistsError:
        pass
    print(s3.ls("bookishsystem/bookish-system/"+user+"/"))



storapp = app  # Rename app to storapp to avoid conflict with the app variable in the main.py file
