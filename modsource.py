mods = [
    {
        "file": "/home/vscode/.local/lib/python3.12/site-packages/webauthn/registration/verify_registration_response.py",
        "from": "if auth_data.rp_id_hash != expected_rp_id_hash_bytes:",
        "to": "if auth_data.rp_id_hash != expected_rp_id_hash_bytes and False: #HUGE RISK HERE",
    },
    {
        "file": "/home/vscode/.local/lib/python3.12/site-packages/webauthn/registration/verify_authentication_response.py",
        "from": "if auth_data.rp_id_hash != expected_rp_id_hash_bytes:",
        "to": "if auth_data.rp_id_hash != expected_rp_id_hash_bytes and False: #HUGE RISK HERE",
    },
]

for mod in mods:
    with open(mod["file"], "r") as f:
        data = f.read()
    data = data.replace(mod["from"], mod["to"])
    with open(mod["file"], "w") as f:
        f.write(data)