#!/usr/bin/env python3
"""Lire et écrire les documents de Popote dans Supabase depuis Claude Code, sans session navigateur.

Le secret vient de ~/.config/popote/secret (copié depuis l'app › Réglages › « Clé pour Claude Code »).
L'URL et la clé anon viennent de config.js.

  python3 tools/popote_db.py dump            → tous les documents en JSON sur stdout
  python3 tools/popote_db.py dump semaines   → une seule collection
  python3 tools/popote_db.py put fichier.json → écrit une liste [{"coll","id","data"}] ; "data": null supprime
"""
import json, re, sys, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
cfg = (HERE / "config.js").read_text()
URL = re.search(r'supabaseUrl:\s*"([^"]+)"', cfg)[1]
KEY = re.search(r'supabaseAnonKey:\s*"([^"]+)"', cfg)[1]
SECRET_FILE = Path.home() / ".config/popote/secret"


def secret():
    if not SECRET_FILE.exists():
        sys.exit(f"Secret absent : colle la « Clé pour Claude Code » (app › Réglages) dans {SECRET_FILE}")
    return SECRET_FILE.read_text().strip()


def rpc(fn, body):
    req = urllib.request.Request(f"{URL}/rest/v1/rpc/{fn}", data=json.dumps(body).encode(),
                                 headers={"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read() or "null")
    except urllib.error.HTTPError as e:
        sys.exit(f"{fn} : HTTP {e.code} {e.read().decode()[:300]}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "dump"
    if cmd == "dump":
        docs = rpc("popote_dump", {"p_secret": secret()}) or []
        if len(sys.argv) > 2: docs = [d for d in docs if d["coll"] == sys.argv[2]]
        print(json.dumps(docs, ensure_ascii=False, indent=1))
    elif cmd == "put":
        docs = json.loads(Path(sys.argv[2]).read_text())
        print(rpc("popote_put", {"p_secret": secret(), "p_docs": docs}), "document(s) écrit(s)")
    else:
        sys.exit(__doc__)
