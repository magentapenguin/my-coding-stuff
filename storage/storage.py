#from gevent import monkey; monkey.patch_all()

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
import brotli, gzip, zlib
from json import loads, dumps, JSONDecoder, JSONEncoder, JSONDecodeError
from datetime import datetime, timedelta, timezone
from typing import Any
import typing
from Crypto.Cipher import AES
import mimetypes

DEV = True
LOCATION = f"bookishsystem/{'bookish-system' if not DEV else 'dev'}/"

def logvisitor(session, rdb):
    visits = loads(rdb.get("visits"))
    session["visits"] = int(session.get("visits", 0)) + 1
    visits.append(
        {
            "user": session.get("user"),
            "visits": session["visits"],
            "time": datetime.now(timezone.utc).isoformat(),
            "first": session.get("visits") == "1",
        }
    )
    rdb.set("visits", dumps(visits))


def loadfile(file: bytes, filename: str, ignorefilename: bool=False) -> tuple[bytes, str]:
    if not filename.endswith(".aes.bin") and not ignorefilename:
        return file, filename
    key = bytes.fromhex(os.getenv("AES_KEY"))
    file = brotli.decompress(file)
    tag = file[:16]
    nonce = file[16 : 16 + 15]
    print(tag, nonce)
    cipher = AES.new(key, AES.MODE_OCB, nonce=nonce)
    filedata = file[16 + 15:]
    data = cipher.decrypt_and_verify(filedata, tag)
    return data, filename.lstrip(".aes.bin")


def savefile(file: bytes, filename: str, ignorefilename: bool=False) -> tuple[bytes, str]:
    if filename.endswith(".aes.bin") and not ignorefilename:
        return file, filename
    key = bytes.fromhex(os.getenv("AES_KEY"))
    cipher = AES.new(key, AES.MODE_OCB)
    data, tag = cipher.encrypt_and_digest(file)
    assert len(cipher.nonce) == 15
    assert len(tag) == 16
    print(tag, cipher.nonce)
    return brotli.compress(tag + cipher.nonce + data), filename + ".aes.bin"


def aesfilename(filename: str) -> str:
    if filename.endswith(".aes.bin"):
        return filename
    return filename + ".aes.bin"


def filedecode(filename):
    return (
        filename if not filename.endswith(".aes.bin") else filename[:-8],
        mimetypes.guess_type(filename if not filename.endswith(".aes.bin") else filename[:-8])[0],
    )


def metadata(user: str, filename: str, file: bytes):
    with s3.open(LOCATION + user + "/metadata.json", "r") as f:
        metadata = loads(f.read())
    metadata[filename] = {
        "type": mimetypes.guess_type(filename)[0],
        "size": len(file),
        "name": filename,
    }
    with s3.open(LOCATION + user + "/metadata.json", "w") as f:
        f.write(dumps(metadata))

def rmmetadata(user: str, filename: str):
    with s3.open(LOCATION + user + "/metadata.json", "r") as f:
        metadata = loads(f.read())
    del metadata[filename]
    with s3.open(LOCATION + user + "/metadata.json", "w") as f:
        f.write(dumps(metadata))


def getmetadata(user: str, filename: str):
    with s3.open(LOCATION + user + "/metadata.json", "r") as f:
        metadata = loads(f.read())
    return metadata.get(filename)

def getsize(user: str, rdb: Any):
    print(user)
    return sum([file["size"] for file in s3.ls(LOCATION + user + "/", detail=True)]), (10,15,20,30,40,50)[min(5,loads(rdb.get("users"))[user].get("permlevel",0))] * 1024 * 1024

def getfiles(user: str):
    if not user:
        return []
    with s3.open(LOCATION + user + "/metadata.json", "r") as f:
        metadata = loads(f.read())
    return list(metadata.values())


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

bottle.BaseRequest.MEMFILE_MAX = 1024 * 1024 * 1024


curdir = os.path.relpath(os.path.dirname(__file__))

bottle.TEMPLATE_PATH.insert(0, curdir+"/views")

session_plugin = bottle_session.SessionPlugin(
    cookie_secure=True, cookie_httponly=True, cookie_lifetime=60 * 60 * 24 * 7, cookie_name="session"
)
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
    s3.touch(LOCATION+"/0")
except FileExistsError:
    pass

@app.route("/<path>")
def altstatic(path):
    if path.strip("/").endswith(".tpl.html"):
        bottle.abort(404, "Not Found")
    return bottle.static_file(path, root=".")

@app.route("/")
def index(session, rdb):
    logvisitor(session, rdb)
    if bottle.request.query.get("logout") is not None:
        session["token"] = ""
        session["user"] = ""
        session["faking_user_as"] = ""
        print("Logged out", session.get("token"), session.get("user"))
        bottle.redirect("/")
    return bottle.template(
        "index.tpl.html",
        curdir="static",
        session=session,
        rdb=rdb,
        loggedin=validate_session_token(session.get("token"), session.get("user"), rdb, allowlocked=True),
        loads=loads,
        Base64Decoder=Base64Decoder,
    )

@app.route("/static/<path:path>")
def static(path):
    return bottle.static_file(path, root=curdir + "/static")

@app.route("/home")
def home(session, rdb):
    logvisitor(session, rdb)
    if bottle.request.query.get("deleteself") is not None and validate_session_token(
        session.get("token"), session.get("user"), rdb
    ):
        print("Deleting Account", session.get("user"))
        users = loads(rdb.get("users"), cls=Base64Decoder)
        del users[session.get("user")]
        rdb.set("users", dumps(users, cls=Base64Encoder))

        tokens = loads(rdb.get("tokens"))
        del tokens[session.get("user")]
        rdb.set("tokens", dumps(tokens))

        s3.rm(LOCATION + session.get("user"), recursive=True)

    if validate_session_token(
        session.get("token"), session.get("user"), rdb, permlevel=7
    ) and bottle.request.query.get("user") is not None:
        users = loads(rdb.get("users"), cls=Base64Decoder)
        target = bottle.request.query.get("user")
        print("Target", target, users.get(target))
        if users.get(target)['permlevel'] > loads(rdb.get("users"), cls=Base64Decoder)[session.get("user")]['permlevel']:
            bottle.redirect("/home")
        if bottle.request.query.get("delete") is not None:
            print("Deleting User", target)
            del users[target]
            rdb.set("users", dumps(users, cls=Base64Encoder))
            try:
                tokens = loads(rdb.get("tokens"))
                del tokens[target]
                rdb.set("tokens", dumps(tokens))

                s3.rm(LOCATION + target, recursive=True)

            except KeyError:
                pass
        elif bottle.request.query.get("lock") is not None:
            print("Locking User", target)
            users[target]["locked"] = not users[target]["locked"]
            rdb.set("users", dumps(users, cls=Base64Encoder))
        
        elif bottle.request.query.get("fake") is not None and users.get(session.get('user'))['permlevel'] >= 12:
            print("Faking user", target)
            session["faking_user_as"] = session.get('user')
            session["token"] = make_session_token(target, rdb)
            session["user"] = target

            
        bottle.redirect("/home")

    if bottle.request.query.get("download") is not None and validate_session_token(
        session.get("token"), session.get("user"), rdb, allowlocked=session.get("faking_user_as") is not None
    ):
        print("Downloading", bottle.request.query.get("download"), getfiles(session.get("user")))
        if getmetadata(session.get("user"), bottle.request.query.get("download")) is None:
            bottle.abort(404, "File not found")
        user = session.get("user")
        bottle.response.set_header(
            "Content-Disposition",
            "attachment; filename="
            + bottle.request.query.get("download"),
        )
        bottle.response.set_header(
            "Content-Type", filedecode(bottle.request.query.get("download"))[1]
        )
        try:
            return readfile(user, bottle.request.query.get("download"))
        except FileNotFoundError:
            bottle.abort(404, "File not found")
    if validate_session_token(
        session.get("token"), session.get("user"), rdb, permlevel=5
    ):
        visitdata = loads(rdb.get("visits"), cls=Base64Decoder) 
        # squash data to every 15 minutes
        data = []

        for visit in visitdata:
            time = datetime.fromisoformat(visit["time"])
            time = time.replace(minute=(time.minute // 15) * 15, second=0, microsecond=0)
            visit["time"] = time
        
        for visit in visitdata:
            if datetime.now(timezone.utc) - visit["time"] < timedelta(hours=24):
                if len(data) == 0 or data[-1]["time"] != visit["time"]:
                    data.append({"time": visit["time"], "visits": 1, "unique": 1 if visit["first"] else 0})
                else:
                    data[-1]["visits"] += 1
                    if visit["first"]:
                        data[-1]["unique"] += 1
        
        # add missing data
        for index, visit in enumerate(data):
            if index == 0:
                continue
            if visit["time"] - data[index - 1]["time"] > timedelta(minutes=15):
                data.insert(index, {"time": data[index - 1]["time"] + timedelta(minutes=15), "visits": 0, "unique": 0})

        for visit in data:
            visit["time"] = visit["time"].isoformat()
        
        data.sort(key=lambda x: x["time"])
    else:
        data = []
    return bottle.template(
        "home.tpl.html",
        session=session,
        rdb = rdb,
        curdir="static",
        loggedin=validate_session_token(session.get("token"), session.get("user"), rdb),
        files=getfiles(session.get("user")),
        loads=loads,
        Base64Decoder=Base64Decoder,
        visitdata=dumps(data),
        getsize=getsize,
    )


@app.route("/status")
def status(session, rdb):
    logvisitor(session, rdb)
    return bottle.template(
        "status.tpl.html",
        session=session,
        curdir="static",
        loggedin=validate_session_token(session.get("token"), session.get("user"), rdb),
    )


@app.route("/terms")
def terms(session, rdb):
    logvisitor(session, rdb)
    return bottle.template(
        "terms.html",
        session=session,
        curdir="static",
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
        if (
            not re.match(r"[0-9a-zA-Z]{3,20}", data["username"])
            or canihaveuser(data["username"], session=session, rdb=rdb)["output"]
            is False
        ):
            bottle.abort(400, "Invalid username")
        fake = False
        if data.get("fake") and validate_session_token(
            session.get("token"), session.get("user"), rdb, permlevel=7
        ):
            fake = True
            registration_verification = None
        else:
            registration_verification = webauthn.verify_registration_response(
                credential=data["credential"],
                expected_challenge=webauthn.base64url_to_bytes(
                    loads(session["challenge"])[1]
                ),
                expected_origin="https://bookish-system-jgvv7pxj96wh5wjq-8080.app.github.dev" if DEV else "???",
                expected_rp_id="bookish-system",
                require_user_verification=True,
            )

        session["challenge"] = "[null, null]"

        if registration_verification or fake:
            users = loads(rdb.get("users"), cls=Base64Decoder)
            if not canihaveuser(data["username"], session=session, rdb=rdb)["output"]:
                print("User already exists")
                bottle.abort(400, "User already exists")
            users[data["username"]] = dataclasses.asdict(registration_verification) if not fake else {"credential_id":b'', "permlevel": -1, "locked": True}
            print(
                "Creating user folder",
                data["username"],
            )
            user = data["username"]
            if not fake:
                print("Creating user folder", user)
                if not s3.exists(LOCATION + user + "/metadata.json"):
                    s3.touch(LOCATION + user + "/metadata.json")
                    with s3.open(
                        LOCATION + user + "/metadata.json", "wb"
                    ) as fw:
                        print("Creating metadata file for user", user)
                        fw.write(b"{}")
                users[user]["permlevel"] = 0
                users[user]["locked"] = False
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


def validate_session_token(token: str, user: str, rdb: Any, permlevel: int = 0, allowlocked: bool = False) -> bool:
    """
    Validates a session token for a given user.

    Args:
        token (str): The session token to validate.
        user (str): The user associated with the session token.
        rdb (Any): The Redis database object.
        permlevel (int, optional): The required permission level. Defaults to 0.
        allowlocked (bool, optional): Whether to allow locked users. Defaults to False.

    Returns:
        bool: True if the session token is valid, False otherwise.
    """
    tokens = loads(rdb.get("tokens"))
    users = loads(rdb.get("users"), cls=Base64Decoder)
    if user in tokens:
        if (
            tokens[user][0] == token
            and datetime.fromisoformat(tokens[user][1]) + timedelta(seconds=60 * 60 * 24)
            > datetime.now()
            and hashlib.sha256(user.encode()).digest() == bytes.fromhex(token)[:-16]
            and not users[user].get("locked", False) or allowlocked
        ):
            if users[user].get("permlevel", 0) >= permlevel:
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


@app.route("/storage", method=["GET", "DELETE", "POST"])
def storage(session, rdb):
    # bottle.abort(401, "Unauthorized")
    user = session.get("user")
    print("User", user)
    if validate_session_token(session.get("token"), session.get("user"), rdb, allowlocked=session.get("faking_user_as") is not None):
        if bottle.request.method == "GET":
            data = bottle.request.query
            if data.get("precheck").isdigit():
                print("Precheck passed")
                return {"output": not (int(data.get("precheck")) + getsize(user, rdb)[0] > getsize(user, rdb)[1])}
            if data.get("file") is None:
                return getfiles(user)
            if data.get("file") == "metadata.json":
                bottle.abort(403, "Forbidden")
            if data.get("download") is not None:
                bottle.response.set_header(
                    "Content-Disposition",
                    "attachment; filename=" + filedecode(data["file"])[0],
                )
                bottle.response.set_header("Content-Type", filedecode(data["file"])[1])
            try:
                return readfile(user, data["file"])
            except FileNotFoundError:
                bottle.abort(404, "File not found")
        elif bottle.request.method == "DELETE":
            data = bottle.request.query
            if modifyfile(user, data["file"], "delete"):
                rmmetadata(user, data["file"])
                return
            else:
                bottle.abort(404, "File not found")
        elif bottle.request.method == "POST":
            for file in bottle.request.files.values():

                print(dict(bottle.request.files))
                if file.filename == "metadata.json":
                    continue

                filedata = file.file.read()
                filename = file.filename

                len(filedata) + getsize(user, rdb)[0] > getsize(user, rdb)[1] and bottle.abort(413, "File too large")

                modifyfile(user, filename, "create")
                if modifyfile(user, filename, "write", filedata):
                    print("File written", filename)
                metadata(user, filename, filedata)

                bottle.redirect("/home")
            return
    else:
        bottle.abort(401, "Unauthorized")

@app.route("/get/<path>", method=["GET"])
def publicget(path):
    user = "public"
    data = bottle.request.query
    if path == "metadata.json":
        bottle.abort(403, "Forbidden")
    if data.get("download") is not None:
        bottle.response.set_header(
            "Content-Disposition",
            "attachment; filename=" + filedecode(path)[0],
        )
    try:
        bottle.response.set_header("Content-Type", filedecode(path)[1])
        return readfile(user, path)
    except FileNotFoundError:
        bottle.abort(404, "File not found")

def modifyfile(
    user: str, file: str, how: str, data: typing.Union[bytes, None] = None
) -> bool:
    file = LOCATION + user + "/" + aesfilename(file)
    if how == "delete":
        if s3.exists(file):
            s3.rm(file)
            return True
    elif how == "create":
        if not s3.exists(file):
            s3.touch(file)
            return True
    elif how == "write":
        if s3.exists(file):
            print(file)
            with s3.open(file,  "wb") as f:
                f.write(savefile(data, file, True)[0])
            return True
    return False


def readfile(user: str, file: str) -> bytes:
    file = LOCATION + user + "/" + aesfilename(file)
    with s3.open(file, "rb") as f:
        return loadfile(f.read(), file, True)[0]


db = redis.Redis(connection_pool=connection_pool)

if db.get("users") is None:
    db.set("users", dumps({}, cls=Base64Encoder))

if db.get("tokens") is None:
    db.set("tokens", dumps({}, cls=Base64Encoder))

if db.get("visits") is None:
    db.set("visits", dumps([], cls=Base64Encoder))


data = loads(db.get("users"), cls=Base64Decoder)
for user in data:
    try:
        print("Creating user folder", user)
        if not s3.exists(LOCATION + user + "/metadata.json"):
            s3.touch(LOCATION + user + "/metadata.json")
    except FileExistsError:
        pass
    try:
        with s3.open(
            LOCATION + user + "/metadata.json", "rb"
        ) as f:
           loads(f.read().decode("utf-8"))
    except JSONDecodeError:
        with s3.open(
            LOCATION + user + "/metadata.json", "wb"
        ) as fw:
            print("Creating metadata file for user", user)
            fw.write(b"{}")
        print(
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa "
            + user
        )
    if data[user].get("permlevel") is None:
        data[user]["permlevel"] = 0

    if data[user].get("locked") is None:
        data[user]["locked"] = False


db.set("users", dumps(data, cls=Base64Encoder))

storapp = app  # Rename app to storapp to avoid conflict with the app variable in the main.py file

if __name__ == "__main__":
    app.run(host='localhost',port=8080, debug=DEV) #server='gevent')