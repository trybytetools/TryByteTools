"""
Try Byte Tools — Local Admin Panel
====================================
Run:  python admin.py
Open: http://localhost:5050

- SQLite database (tbt.db) lives next to this file — never pushed
- Deploy injects data directly into index.html then git pushes
- Background video upload copies file into assets/ folder
"""

import json
import mimetypes
import os
import re
import shutil
import sqlite3
import subprocess
import webbrowser
from datetime import datetime
from pathlib import Path
from threading import Timer

from flask import Flask, jsonify, render_template_string, request

# ── Paths ──────────────────────────────────────────────────────────────────
BASE       = Path(__file__).parent.resolve()
DB         = BASE / "tbt.db"
INDEX_HTML = BASE / "index.html"
ASSETS     = BASE / "assets"
ASSETS.mkdir(exist_ok=True)

CAT_LABELS = {
    "unity": "Unity Tool", "game": "Game", "web": "Web",
    "python": "Python",    "android": "Android", "ai": "AI",
}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 60 * 1024 * 1024   # 60 MB upload limit

# ══════════════════════════════════════════════════════════════════
#  DATABASE
# ══════════════════════════════════════════════════════════════════

def get_db():
    con = sqlite3.connect(str(DB))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    return con


def init_db():
    con = get_db()
    con.executescript("""
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS projects (
            id          TEXT PRIMARY KEY,
            title       TEXT NOT NULL,
            category    TEXT NOT NULL DEFAULT 'unity',
            status      TEXT NOT NULL DEFAULT 'idea',
            author      TEXT NOT NULL DEFAULT '',
            version     TEXT NOT NULL DEFAULT '',
            desc        TEXT NOT NULL DEFAULT '',
            links       TEXT NOT NULL DEFAULT '[]',
            patch_notes TEXT NOT NULL DEFAULT '[]',
            sort_order  INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS pipeline (
            id         TEXT PRIMARY KEY,
            title      TEXT NOT NULL,
            type       TEXT NOT NULL DEFAULT 'idea',
            version    TEXT NOT NULL DEFAULT '',
            desc       TEXT NOT NULL DEFAULT '',
            sort_order INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS team (
            id         TEXT PRIMARY KEY,
            name       TEXT NOT NULL,
            role       TEXT NOT NULL DEFAULT '',
            avatar     TEXT NOT NULL DEFAULT '',
            sort_order INTEGER NOT NULL DEFAULT 0
        );
    """)

    # Seed only if tables are empty
    if not con.execute("SELECT 1 FROM settings WHERE key='studioName'").fetchone():
        con.executemany("INSERT INTO settings VALUES (?,?)", [
            ("studioName", "Try Byte Tools"),
            ("email",      "TryByteTools@gmail.com"),
            ("siteUrl",    "https://trybytetools.github.io/TryByteTools/"),
            ("tagline",    "A small team that just wants to build cool stuff together."),
        ])

    if not con.execute("SELECT 1 FROM projects").fetchone():
        rows = [
            ("001", "Folder Icons", "unity", "wip", "Dminx", "1.0.0",
             "Right-click any folder in the Unity Project window to assign a custom color or icon. GUID-based persistence, zero runtime cost.",
             '[{"label":"Asset Store","href":"#","icon":"store"}]',
             '[{"version":"0.9.9","date":"2026-03-10","notes":"Waiting on release on the Unity Asset Store."}]', 0),
            ("002", "Scene Sticky Notes", "unity", "wip", "Dminx", "0.1.0",
             "Play-in-scene sticky notes for 2D & 3D editors. Pass tasks to teammates, or set reminders for your next session.",
             "[]",
             '[{"version":"0.1.0","date":"2026-03-10","notes":"Created the sticky note package — needs polishing."}]', 1),
            ("003", "Unity Inspector Refresh Fix", "unity", "live", "Dminx", "1.0.0",
             "Fixes an issue in Unity 6.3 where the Inspector does not show the selected object. Confirmed on Cosmic OS.",
             '[{"label":"GitHub","href":"https://github.com/trybytetools/Unity-Inspector-Refresh-Fix-COSMIC-OS/tree/main","icon":"github"}]',
             '[{"version":"1.0.0","date":"2026-03-10","notes":"Initial release. Uploaded to GitHub."}]', 2),
        ]
        con.executemany(
            "INSERT INTO projects (id,title,category,status,author,version,desc,links,patch_notes,sort_order)"
            " VALUES (?,?,?,?,?,?,?,?,?,?)", rows)

    if not con.execute("SELECT 1 FROM pipeline").fetchone():
        con.execute("INSERT INTO pipeline VALUES (?,?,?,?,?,?)",
            ("pl001", "Scene Sticky Notes", "update", "0.1.0",
             "Play-in-scene sticky notes for 2D & 3D editors.", 0))

    if not con.execute("SELECT 1 FROM team").fetchone():
        con.executemany("INSERT INTO team VALUES (?,?,?,?,?)", [
            ("t001",  "Dminx", "Solo Dev",    "", 0),
            ("t1002", "Robix", "Inspiration", "", 1),
        ])

    con.commit()
    con.close()


# ══════════════════════════════════════════════════════════════════
#  BUILD DATA OBJECT
# ══════════════════════════════════════════════════════════════════

def build_data():
    con = get_db()
    settings = {r["key"]: r["value"]
                for r in con.execute("SELECT key,value FROM settings")}
    projects = []
    for row in con.execute("SELECT * FROM projects ORDER BY sort_order,id"):
        cat = row["category"]
        projects.append({
            "id": row["id"], "title": row["title"],
            "category": cat, "tagLabel": CAT_LABELS.get(cat, cat),
            "status": row["status"], "author": row["author"],
            "version": row["version"], "desc": row["desc"],
            "links":      json.loads(row["links"]       or "[]"),
            "patchNotes": json.loads(row["patch_notes"] or "[]"),
        })
    pipeline = [
        {"id": r["id"], "title": r["title"], "type": r["type"],
         "version": r["version"], "desc": r["desc"]}
        for r in con.execute("SELECT * FROM pipeline ORDER BY sort_order,id")
    ]
    team = [
        {"id": r["id"], "name": r["name"], "role": r["role"], "avatar": r["avatar"]}
        for r in con.execute("SELECT * FROM team ORDER BY sort_order,id")
    ]
    con.close()
    return {"settings": settings, "projects": projects,
            "pipeline": pipeline, "team": team}


# ══════════════════════════════════════════════════════════════════
#  INJECT INTO index.html
# ══════════════════════════════════════════════════════════════════

START = "/* TBT:DATA:START */"
END   = "/* TBT:DATA:END */"

def inject_html():
    if not INDEX_HTML.exists():
        return False, f"index.html not found at {INDEX_HTML}"
    html = INDEX_HTML.read_text(encoding="utf-8")
    if START not in html or END not in html:
        return False, "TBT:DATA markers missing from index.html"
    data     = build_data()
    js       = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    new_block = f"{START}\nconst DATA = {js};\n{END}"
    updated  = re.sub(re.escape(START) + r".*?" + re.escape(END),
                      new_block, html, flags=re.DOTALL)
    INDEX_HTML.write_text(updated, encoding="utf-8")
    return True, None


# ══════════════════════════════════════════════════════════════════
#  GIT DEPLOY
# ══════════════════════════════════════════════════════════════════

def git_deploy(message=None):
    msg = message or f"content: update via admin [{datetime.now():%Y-%m-%d %H:%M}]"
    for cmd in [
        ["git", "-C", str(BASE), "add", "index.html", "assets/"],
        ["git", "-C", str(BASE), "commit", "-m", msg],
        ["git", "-C", str(BASE), "pull", "--rebase", "origin", "main"],
        ["git", "-C", str(BASE), "push", "origin", "main"],
    ]:
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            out = r.stderr.strip() or r.stdout.strip()
            if "nothing to commit" in out:
                continue
            return {"ok": False, "error": out}
    return {"ok": True}


# ══════════════════════════════════════════════════════════════════
#  API ROUTES
# ══════════════════════════════════════════════════════════════════

# ── Inject / Deploy ────────────────────────────────────────────
@app.route("/api/inject", methods=["POST"])
def api_inject():
    ok, err = inject_html()
    if not ok:
        return jsonify({"ok": False, "error": err})
    d = build_data()
    return jsonify({"ok": True, "projects": len(d["projects"]),
                    "pipeline": len(d["pipeline"]), "team": len(d["team"])})

@app.route("/api/deploy", methods=["POST"])
def api_deploy():
    ok, err = inject_html()
    if not ok:
        return jsonify({"ok": False, "error": err})
    msg = (request.json or {}).get("message")
    result = git_deploy(msg)
    d = build_data()
    return jsonify({**result, "projects": len(d["projects"]),
                    "pipeline": len(d["pipeline"]), "team": len(d["team"])})


# ── Background upload ──────────────────────────────────────────
@app.route("/api/background", methods=["POST"])
def api_background():
    if "file" not in request.files:
        return jsonify({"ok": False, "error": "No file provided"})
    f    = request.files["file"]
    name = f.filename or ""
    ext  = Path(name).suffix.lower()
    if ext not in {".mp4", ".webm", ".gif", ".mov"}:
        return jsonify({"ok": False, "error": f"Unsupported file type: {ext}"})
    dest = ASSETS / f"bg{ext}"
    f.save(str(dest))
    size_mb = dest.stat().st_size / 1_048_576
    return jsonify({"ok": True, "path": f"assets/bg{ext}",
                    "size": f"{size_mb:.1f} MB", "ext": ext})

@app.route("/api/background", methods=["GET"])
def api_background_get():
    """Return which background files currently exist in assets/."""
    found = []
    for ext in [".mp4", ".webm", ".gif", ".mov"]:
        p = ASSETS / f"bg{ext}"
        if p.exists():
            found.append({"file": f"bg{ext}",
                          "size": f"{p.stat().st_size/1_048_576:.1f} MB"})
    return jsonify(found)

@app.route("/api/background/<ext>", methods=["DELETE"])
def api_background_delete(ext):
    p = ASSETS / f"bg.{ext}"
    if p.exists():
        p.unlink()
    return jsonify({"ok": True})


# ── Settings ───────────────────────────────────────────────────
@app.route("/api/settings", methods=["GET"])
def api_settings_get():
    con = get_db()
    rows = con.execute("SELECT key,value FROM settings").fetchall()
    con.close()
    return jsonify({r["key"]: r["value"] for r in rows})

@app.route("/api/settings", methods=["POST"])
def api_settings_post():
    con = get_db()
    for k, v in (request.json or {}).items():
        con.execute("INSERT OR REPLACE INTO settings VALUES (?,?)", (k, str(v)))
    con.commit(); con.close()
    return jsonify({"ok": True})


# ── Projects ───────────────────────────────────────────────────
@app.route("/api/projects", methods=["GET"])
def api_projects_get():
    con = get_db()
    rows = con.execute("SELECT * FROM projects ORDER BY sort_order,id").fetchall()
    con.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/projects", methods=["POST"])
def api_projects_post():
    d = request.json or {}
    if not d.get("id") or not d.get("title"):
        return jsonify({"ok": False, "error": "id and title required"})
    con = get_db()
    con.execute(
        "INSERT OR REPLACE INTO projects"
        " (id,title,category,status,author,version,desc,links,patch_notes,sort_order)"
        " VALUES (?,?,?,?,?,?,?,?,?,?)",
        (d["id"], d["title"], d.get("category","unity"), d.get("status","idea"),
         d.get("author",""), d.get("version",""), d.get("desc",""),
         json.dumps(d.get("links",[])), json.dumps(d.get("patchNotes",[])),
         d.get("sort_order", 0)))
    con.commit(); con.close()
    return jsonify({"ok": True})

@app.route("/api/projects/<pid>", methods=["DELETE"])
def api_projects_delete(pid):
    con = get_db()
    con.execute("DELETE FROM projects WHERE id=?", (pid,))
    con.commit(); con.close()
    return jsonify({"ok": True})


# ── Pipeline ───────────────────────────────────────────────────
@app.route("/api/pipeline", methods=["GET"])
def api_pipeline_get():
    con = get_db()
    rows = con.execute("SELECT * FROM pipeline ORDER BY sort_order,id").fetchall()
    con.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/pipeline", methods=["POST"])
def api_pipeline_post():
    d = request.json or {}
    if not d.get("id") or not d.get("title"):
        return jsonify({"ok": False, "error": "id and title required"})
    con = get_db()
    con.execute(
        "INSERT OR REPLACE INTO pipeline (id,title,type,version,desc,sort_order)"
        " VALUES (?,?,?,?,?,?)",
        (d["id"], d["title"], d.get("type","idea"),
         d.get("version",""), d.get("desc",""), d.get("sort_order",0)))
    con.commit(); con.close()
    return jsonify({"ok": True})

@app.route("/api/pipeline/<pid>", methods=["DELETE"])
def api_pipeline_delete(pid):
    con = get_db()
    con.execute("DELETE FROM pipeline WHERE id=?", (pid,))
    con.commit(); con.close()
    return jsonify({"ok": True})


# ── Team ───────────────────────────────────────────────────────
@app.route("/api/team", methods=["GET"])
def api_team_get():
    con = get_db()
    rows = con.execute("SELECT * FROM team ORDER BY sort_order,id").fetchall()
    con.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/team", methods=["POST"])
def api_team_post():
    d = request.json or {}
    if not d.get("id") or not d.get("name"):
        return jsonify({"ok": False, "error": "id and name required"})
    con = get_db()
    con.execute(
        "INSERT OR REPLACE INTO team (id,name,role,avatar,sort_order)"
        " VALUES (?,?,?,?,?)",
        (d["id"], d["name"], d.get("role",""), d.get("avatar",""), d.get("sort_order",0)))
    con.commit(); con.close()
    return jsonify({"ok": True})

@app.route("/api/team/<tid>", methods=["DELETE"])
def api_team_delete(tid):
    con = get_db()
    con.execute("DELETE FROM team WHERE id=?", (tid,))
    con.commit(); con.close()
    return jsonify({"ok": True})


# ══════════════════════════════════════════════════════════════════
#  FRONTEND UI
# ══════════════════════════════════════════════════════════════════

UI = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>TBT Admin</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#040b14;--bg2:#060e1a;--bg3:#0a1628;
  --cyan:#00baff;--blue:#3d9eff;--blue-b:#7dc8ff;
  --text:#ddeeff;--text2:#9ab8d8;--muted:#3d5872;--muted2:#6a8eaa;
  --border:rgba(61,158,255,0.12);--border2:rgba(61,158,255,0.22);
  --green:#00e5a0;--red:#ff4a6e;--yellow:#ffd066;
  --r:10px;--rl:16px;
  --mono:'JetBrains Mono','Fira Code',monospace;
}
html{font-size:15px}
body{background:var(--bg);color:var(--text);font-family:system-ui,sans-serif;min-height:100vh;display:flex;flex-direction:column}

header{
  position:sticky;top:0;z-index:100;
  background:rgba(4,11,20,.95);backdrop-filter:blur(20px);
  border-bottom:1px solid var(--border);
  padding:.75rem 2rem;display:flex;align-items:center;gap:1.5rem;flex-wrap:wrap;
}
.logo{font-family:var(--mono);font-size:.72rem;font-weight:700;color:var(--blue-b);
  letter-spacing:.1em;display:flex;align-items:center;gap:.5rem}
.logo-dot{width:8px;height:8px;border-radius:50%;background:var(--cyan);
  box-shadow:0 0 10px var(--cyan);animation:pulse 2.5s ease-in-out infinite}
@keyframes pulse{0%,100%{box-shadow:0 0 6px var(--cyan)}50%{box-shadow:0 0 18px var(--cyan),0 0 30px rgba(0,186,255,.3)}}
.ha{margin-left:auto;display:flex;gap:.5rem}

nav{display:flex;gap:2px;border-left:1px solid var(--border);padding-left:1rem}
nav button{background:none;border:none;color:var(--muted2);font-family:var(--mono);
  font-size:.64rem;letter-spacing:.08em;text-transform:uppercase;
  padding:.4rem .85rem;border-radius:6px;cursor:pointer;transition:all .15s}
nav button:hover{color:var(--blue-b);background:rgba(61,158,255,.07)}
nav button.active{color:var(--cyan);background:rgba(0,186,255,.1);
  box-shadow:0 0 0 1px rgba(0,186,255,.2)}

main{flex:1;padding:2rem;max-width:1100px;margin:0 auto;width:100%}
.tab{display:none}.tab.active{display:block}

/* Buttons */
.btn{display:inline-flex;align-items:center;gap:.4rem;font-family:var(--mono);
  font-size:.66rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;
  padding:.5rem 1.1rem;border-radius:var(--r);border:none;cursor:pointer;transition:all .18s}
.btn-p{background:linear-gradient(135deg,var(--blue),var(--cyan));color:#020a14;
  box-shadow:0 0 20px rgba(0,186,255,.25)}
.btn-p:hover{transform:translateY(-2px);box-shadow:0 0 32px rgba(0,186,255,.45)}
.btn-g{background:transparent;color:var(--text2);border:1px solid var(--border2)}
.btn-g:hover{border-color:rgba(61,158,255,.4);color:var(--blue-b);background:rgba(61,158,255,.06)}
.btn-d{background:rgba(255,74,110,.1);color:var(--red);border:1px solid rgba(255,74,110,.25)}
.btn-d:hover{background:rgba(255,74,110,.22)}
.btn-sm{padding:.3rem .7rem;font-size:.6rem}
.btn:disabled{opacity:.4;cursor:not-allowed;transform:none!important}

/* Cards */
.card{background:var(--bg2);border:1px solid var(--border);border-radius:var(--rl);padding:1.5rem;margin-bottom:1rem}
.ch{display:flex;align-items:center;justify-content:space-between;gap:1rem;margin-bottom:1.25rem;flex-wrap:wrap}
.ct{font-family:var(--mono);font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;color:var(--blue-b)}
.ar{display:flex;gap:.5rem;flex-wrap:wrap}

/* Forms */
.fg{display:grid;grid-template-columns:1fr 1fr;gap:1rem}
.fg1{grid-template-columns:1fr}
.f{display:flex;flex-direction:column;gap:.4rem}
.s2{grid-column:span 2}
label{font-family:var(--mono);font-size:.6rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted2)}
input,select,textarea{
  background:var(--bg3);border:1px solid var(--border2);border-radius:var(--r);
  color:var(--text);font-family:var(--mono);font-size:.78rem;
  padding:.55rem .85rem;transition:border-color .15s,box-shadow .15s;outline:none;width:100%}
input:focus,select:focus,textarea:focus{
  border-color:rgba(0,186,255,.5);box-shadow:0 0 0 3px rgba(0,186,255,.08)}
textarea{resize:vertical;min-height:80px;line-height:1.7}
select option{background:var(--bg2)}
input[type=file]{padding:.45rem .85rem;cursor:pointer}

/* Table */
.tw{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:.82rem}
th{font-family:var(--mono);font-size:.6rem;letter-spacing:.1em;text-transform:uppercase;
  color:var(--muted);padding:.7rem 1rem;text-align:left;border-bottom:1px solid var(--border);white-space:nowrap}
td{padding:.75rem 1rem;border-bottom:1px solid rgba(61,158,255,.06);color:var(--text2);vertical-align:middle}
tr:hover td{background:rgba(61,158,255,.03)}
tr:last-child td{border-bottom:none}

/* Badges */
.badge{display:inline-block;font-family:var(--mono);font-size:.55rem;letter-spacing:.08em;
  text-transform:uppercase;padding:.18rem .55rem;border-radius:5px;white-space:nowrap}
.bl{background:rgba(0,186,255,.12);color:#7dd8ff;border:1px solid rgba(0,186,255,.25)}
.bw{background:rgba(255,208,0,.1);color:var(--yellow);border:1px solid rgba(255,208,0,.25)}
.bi{background:rgba(255,208,0,.06);color:rgba(255,208,0,.6);border:1px solid rgba(255,208,0,.15)}
.ba{background:rgba(100,100,100,.1);color:var(--muted2);border:1px solid var(--border)}
.br{background:rgba(37,99,235,.2);color:#93c5fd;border:1px solid rgba(37,99,235,.4)}
.bu{background:rgba(0,186,255,.12);color:#7dd8ff;border:1px solid rgba(0,186,255,.25)}

/* Sub-list (links / patch notes) */
.sl{display:flex;flex-direction:column;gap:.5rem;margin-top:.5rem}
.si{background:var(--bg3);border:1px solid var(--border);border-radius:var(--r);
  padding:.65rem .9rem;display:flex;gap:.5rem;align-items:center;flex-wrap:wrap}
.si input{padding:.32rem .6rem;font-size:.72rem;flex:1;min-width:80px}
.si select{padding:.32rem .6rem;font-size:.72rem;width:auto}
.sa{font-family:var(--mono);font-size:.6rem;letter-spacing:.08em;text-transform:uppercase;
  color:var(--cyan);background:none;border:1px dashed rgba(0,186,255,.25);border-radius:var(--r);
  padding:.38rem 1rem;cursor:pointer;width:100%;transition:all .15s;margin-top:.25rem}
.sa:hover{background:rgba(0,186,255,.06);border-color:rgba(0,186,255,.4)}

/* Modal */
.mo{display:none;position:fixed;inset:0;z-index:500;background:rgba(2,6,14,.9);
  backdrop-filter:blur(8px);align-items:center;justify-content:center;padding:1rem}
.mo.open{display:flex}
.md{background:var(--bg2);border:1px solid var(--border2);border-radius:var(--rl);
  width:100%;max-width:680px;max-height:92vh;overflow-y:auto;
  box-shadow:0 0 80px rgba(0,0,0,.8)}
.mh{display:flex;align-items:center;justify-content:space-between;
  padding:1.2rem 1.5rem;border-bottom:1px solid var(--border);
  position:sticky;top:0;background:var(--bg2);z-index:1}
.mt{font-family:var(--mono);font-size:.72rem;letter-spacing:.1em;text-transform:uppercase;color:var(--blue-b)}
.mx{background:none;border:none;color:var(--muted2);font-size:1.1rem;cursor:pointer;
  width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;transition:all .15s}
.mx:hover{color:var(--text);background:rgba(255,255,255,.08)}
.mb{padding:1.5rem}
.mf{display:flex;justify-content:flex-end;gap:.5rem;padding:1rem 1.5rem;border-top:1px solid var(--border)}

/* Toast */
#toast{position:fixed;bottom:2rem;right:2rem;z-index:9000;display:flex;flex-direction:column;gap:.5rem;pointer-events:none}
.ti{font-family:var(--mono);font-size:.68rem;padding:.7rem 1.1rem;border-radius:var(--r);
  border:1px solid;opacity:0;transform:translateY(8px);transition:all .22s;pointer-events:none}
.ti.show{opacity:1;transform:none}
.tok{background:rgba(0,229,160,.1);border-color:rgba(0,229,160,.3);color:var(--green)}
.ter{background:rgba(255,74,110,.1);border-color:rgba(255,74,110,.3);color:var(--red)}
.tin{background:rgba(0,186,255,.1);border-color:rgba(0,186,255,.25);color:var(--cyan)}

/* Status row */
.sr{display:flex;align-items:center;gap:.75rem;font-family:var(--mono);font-size:.66rem;color:var(--muted2)}
.sd{width:7px;height:7px;border-radius:50%;flex-shrink:0}
.dok{background:var(--green);box-shadow:0 0 8px var(--green)}
.der{background:var(--red);box-shadow:0 0 8px var(--red)}
.did{background:var(--muted)}

/* Upload drop zone */
.dropzone{border:2px dashed rgba(0,186,255,.25);border-radius:var(--rl);padding:2rem;
  text-align:center;cursor:pointer;transition:all .2s;background:rgba(0,186,255,.02)}
.dropzone:hover,.dropzone.over{border-color:rgba(0,186,255,.5);background:rgba(0,186,255,.05)}
.dz-icon{font-size:1.8rem;margin-bottom:.5rem;opacity:.5}
.dz-text{font-family:var(--mono);font-size:.72rem;color:var(--muted2)}
.dz-sub{font-family:var(--mono);font-size:.6rem;color:var(--muted);margin-top:.25rem}
.bg-file-list{display:flex;flex-direction:column;gap:.5rem;margin-top:1rem}
.bg-file{display:flex;align-items:center;justify-content:space-between;
  background:var(--bg3);border:1px solid var(--border);border-radius:var(--r);
  padding:.65rem 1rem;font-family:var(--mono);font-size:.72rem}
.bg-file span{color:var(--text2)}
.bg-file code{color:var(--cyan)}

@media(max-width:600px){.fg{grid-template-columns:1fr}.s2{grid-column:1}}
</style>
</head>
<body>

<header>
  <div class="logo"><div class="logo-dot"></div>TBT ADMIN</div>
  <nav>
    <button class="active" onclick="tab('projects',this)">Projects</button>
    <button onclick="tab('pipeline',this)">Pipeline</button>
    <button onclick="tab('team',this)">Team</button>
    <button onclick="tab('background',this)">Background</button>
    <button onclick="tab('settings',this)">Settings</button>
  </nav>
  <div class="ha">
    <button class="btn btn-g btn-sm" onclick="doInject()">⬇ Write to HTML</button>
    <button class="btn btn-p btn-sm" onclick="openDeploy()">🚀 Deploy</button>
  </div>
</header>

<main>

<!-- PROJECTS -->
<div class="tab active" id="tab-projects">
  <div class="card">
    <div class="ch">
      <div class="ct">Projects</div>
      <button class="btn btn-p btn-sm" onclick="openProject(null)">+ New Project</button>
    </div>
    <div class="tw">
      <table>
        <thead><tr><th>ID</th><th>Title</th><th>Category</th><th>Status</th><th>Version</th><th></th></tr></thead>
        <tbody id="tb-projects"></tbody>
      </table>
    </div>
  </div>
</div>

<!-- PIPELINE -->
<div class="tab" id="tab-pipeline">
  <div class="card">
    <div class="ch">
      <div class="ct">Pipeline</div>
      <button class="btn btn-p btn-sm" onclick="openPipeline(null)">+ New Entry</button>
    </div>
    <div class="tw">
      <table>
        <thead><tr><th>ID</th><th>Title</th><th>Type</th><th>Version</th><th></th></tr></thead>
        <tbody id="tb-pipeline"></tbody>
      </table>
    </div>
  </div>
</div>

<!-- TEAM -->
<div class="tab" id="tab-team">
  <div class="card">
    <div class="ch">
      <div class="ct">Team</div>
      <button class="btn btn-p btn-sm" onclick="openTeam(null)">+ New Member</button>
    </div>
    <div class="tw">
      <table>
        <thead><tr><th>ID</th><th>Name</th><th>Role</th><th></th></tr></thead>
        <tbody id="tb-team"></tbody>
      </table>
    </div>
  </div>
</div>

<!-- BACKGROUND -->
<div class="tab" id="tab-background">
  <div class="card">
    <div class="ch"><div class="ct">Background Video / GIF</div></div>
    <p style="font-size:.82rem;color:var(--text2);line-height:1.85;margin-bottom:1.5rem">
      Upload a looping background file. It will be saved as <code style="color:var(--cyan)">assets/bg.ext</code>
      next to index.html. Keep files under 50 MB. Supported: <code style="color:var(--cyan)">.mp4 .webm .gif .mov</code><br>
      After uploading, hit <strong>Deploy</strong> — GitHub Pages will serve the video from your repo.
    </p>

    <div class="dropzone" id="dropzone" onclick="document.getElementById('bg-input').click()"
         ondragover="event.preventDefault();this.classList.add('over')"
         ondragleave="this.classList.remove('over')"
         ondrop="onDrop(event)">
      <div class="dz-icon">🎬</div>
      <div class="dz-text">Click to choose file, or drag and drop here</div>
      <div class="dz-sub">MP4 · WebM · GIF · MOV — max 50 MB</div>
    </div>
    <input type="file" id="bg-input" accept=".mp4,.webm,.gif,.mov" style="display:none" onchange="uploadBg(this.files[0])"/>

    <div id="bg-upload-status" style="margin-top:.75rem;font-family:var(--mono);font-size:.72rem;color:var(--muted2)"></div>

    <div class="bg-file-list" id="bg-file-list"></div>
  </div>
</div>

<!-- SETTINGS -->
<div class="tab" id="tab-settings">
  <div class="card">
    <div class="ch"><div class="ct">Studio Settings</div></div>
    <div style="max-width:500px;display:flex;flex-direction:column;gap:1rem">
      <div class="f"><label>Studio Name</label><input id="s-name" type="text"/></div>
      <div class="f"><label>Contact Email</label><input id="s-email" type="email"/></div>
      <div class="f"><label>Site URL</label><input id="s-url" type="url"/></div>
      <div class="f"><label>Tagline</label><textarea id="s-tag" rows="2"></textarea></div>
      <div><button class="btn btn-p" onclick="saveSettings()">Save Settings</button></div>
    </div>
  </div>
</div>

</main>

<!-- PROJECT MODAL -->
<div class="mo" id="mo-project">
<div class="md">
  <div class="mh">
    <div class="mt" id="mo-project-title">New Project</div>
    <button class="mx" onclick="closeModal('mo-project')">✕</button>
  </div>
  <div class="mb">
    <div class="fg">
      <div class="f"><label>ID *</label><input id="p-id" placeholder="004"/></div>
      <div class="f"><label>Version</label><input id="p-ver" placeholder="1.0.0"/></div>
      <div class="f s2"><label>Title *</label><input id="p-title"/></div>
      <div class="f">
        <label>Category</label>
        <select id="p-cat">
          <option value="unity">Unity Tool</option>
          <option value="game">Game</option>
          <option value="web">Web</option>
          <option value="python">Python</option>
          <option value="android">Android</option>
          <option value="ai">AI</option>
        </select>
      </div>
      <div class="f">
        <label>Status</label>
        <select id="p-status">
          <option value="live">Live</option>
          <option value="wip">In Dev</option>
          <option value="idea">Idea</option>
          <option value="archived">Archived</option>
        </select>
      </div>
      <div class="f"><label>Author</label><input id="p-author" placeholder="Dminx"/></div>
      <div class="f s2"><label>Description</label><textarea id="p-desc" rows="3"></textarea></div>
      <div class="f s2">
        <label>Links</label>
        <div id="p-links" class="sl"></div>
        <button class="sa" onclick="addLink()">+ Add Link</button>
      </div>
      <div class="f s2">
        <label>Patch Notes</label>
        <div id="p-patches" class="sl"></div>
        <button class="sa" onclick="addPatch()">+ Add Patch Note</button>
      </div>
    </div>
  </div>
  <div class="mf">
    <button class="btn btn-g btn-sm" onclick="closeModal('mo-project')">Cancel</button>
    <button class="btn btn-p btn-sm" onclick="saveProject()">Save Project</button>
  </div>
</div>
</div>

<!-- PIPELINE MODAL -->
<div class="mo" id="mo-pipeline">
<div class="md">
  <div class="mh">
    <div class="mt" id="mo-pipeline-title">New Pipeline Entry</div>
    <button class="mx" onclick="closeModal('mo-pipeline')">✕</button>
  </div>
  <div class="mb">
    <div class="fg">
      <div class="f"><label>ID *</label><input id="pl-id" placeholder="pl002"/></div>
      <div class="f">
        <label>Type</label>
        <select id="pl-type">
          <option value="release">Release</option>
          <option value="update">Update</option>
          <option value="idea">Idea</option>
        </select>
      </div>
      <div class="f s2"><label>Title *</label><input id="pl-title"/></div>
      <div class="f"><label>Version</label><input id="pl-ver" placeholder="0.1.0"/></div>
      <div class="f s2"><label>Description</label><textarea id="pl-desc" rows="3"></textarea></div>
    </div>
  </div>
  <div class="mf">
    <button class="btn btn-g btn-sm" onclick="closeModal('mo-pipeline')">Cancel</button>
    <button class="btn btn-p btn-sm" onclick="savePipeline()">Save Entry</button>
  </div>
</div>
</div>

<!-- TEAM MODAL -->
<div class="mo" id="mo-team">
<div class="md">
  <div class="mh">
    <div class="mt" id="mo-team-title">New Team Member</div>
    <button class="mx" onclick="closeModal('mo-team')">✕</button>
  </div>
  <div class="mb">
    <div class="fg">
      <div class="f"><label>ID *</label><input id="tm-id" placeholder="t003"/></div>
      <div class="f"><label>Name *</label><input id="tm-name"/></div>
      <div class="f"><label>Role</label><input id="tm-role" placeholder="Developer"/></div>
      <div class="f"><label>Avatar URL</label><input id="tm-avatar" placeholder="https://..."/></div>
    </div>
  </div>
  <div class="mf">
    <button class="btn btn-g btn-sm" onclick="closeModal('mo-team')">Cancel</button>
    <button class="btn btn-p btn-sm" onclick="saveTeam()">Save Member</button>
  </div>
</div>
</div>

<!-- DEPLOY MODAL -->
<div class="mo" id="mo-deploy">
<div class="md" style="max-width:500px">
  <div class="mh">
    <div class="mt">Deploy to GitHub Pages</div>
    <button class="mx" onclick="closeModal('mo-deploy')">✕</button>
  </div>
  <div class="mb">
    <p style="font-size:.82rem;color:var(--text2);line-height:1.85;margin-bottom:1.25rem">
      Writes database into <code style="color:var(--cyan)">index.html</code>
      then runs <code style="color:var(--cyan)">git add / commit / push</code>.
      Site updates in ~30 seconds.
    </p>
    <div class="f" style="margin-bottom:1rem">
      <label>Commit message (optional)</label>
      <input id="deploy-msg" placeholder="content: update projects"/>
    </div>
    <div class="sr" id="deploy-status">
      <div class="sd did"></div><span>Ready.</span>
    </div>
  </div>
  <div class="mf">
    <button class="btn btn-g btn-sm" onclick="closeModal('mo-deploy')">Cancel</button>
    <button class="btn btn-p" id="deploy-btn" onclick="doDeploy()">🚀 Deploy</button>
  </div>
</div>
</div>

<div id="toast"></div>

<script>
// ─────────────────────────────────────────────
// UTILITIES
// ─────────────────────────────────────────────
function tab(name, btn) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  btn.classList.add('active');
  if (name === 'background') loadBgFiles();
  if (name === 'settings') loadSettings();
}

function toast(msg, type = 'ok') {
  const el = document.createElement('div');
  el.className = 'ti t' + type;
  el.textContent = msg;
  document.getElementById('toast').appendChild(el);
  requestAnimationFrame(() => el.classList.add('show'));
  setTimeout(() => { el.classList.remove('show'); setTimeout(() => el.remove(), 300); }, 3500);
}

async function api(method, path, body) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const r = await fetch(path, opts);
  if (!r.ok) { const t = await r.text(); throw new Error(t); }
  return r.json();
}

function openModal(id)  { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }
document.addEventListener('click', e => {
  if (e.target.classList.contains('mo')) e.target.classList.remove('open');
});
document.addEventListener('keydown', e => {
  if (e.key === 'Escape')
    document.querySelectorAll('.mo.open').forEach(m => m.classList.remove('open'));
});

function badgeClass(val) {
  return { live:'bl', wip:'bw', idea:'bi', archived:'ba', release:'br', update:'bu' }[val] || 'ba';
}

// ─────────────────────────────────────────────
// PROJECTS
// ─────────────────────────────────────────────
async function loadProjects() {
  const rows = await api('GET', '/api/projects');
  document.getElementById('tb-projects').innerHTML = rows.length
    ? rows.map(p => `
      <tr>
        <td><code style="font-size:.7rem;color:var(--muted2)">${esc(p.id)}</code></td>
        <td style="color:var(--text);font-weight:500">${esc(p.title)}</td>
        <td style="font-size:.76rem">${esc(p.category)}</td>
        <td><span class="badge ${badgeClass(p.status)}">${esc(p.status)}</span></td>
        <td style="font-size:.76rem">${esc(p.version) || '—'}</td>
        <td><div class="ar">
          <button class="btn btn-g btn-sm" onclick="editProject(${esc(JSON.stringify(p), true)})">Edit</button>
          <button class="btn btn-d btn-sm" onclick="delProject(${esc(JSON.stringify(p.id), true)},${esc(JSON.stringify(p.title), true)})">Del</button>
        </div></td>
      </tr>`).join('')
    : '<tr><td colspan="6" style="text-align:center;color:var(--muted);padding:2rem;font-family:var(--mono);font-size:.72rem">No projects yet.</td></tr>';
}

function esc(val, attr = false) {
  if (typeof val !== 'string') return val;
  const s = val.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  return attr ? s.replace(/"/g,'&quot;').replace(/'/g,'&#39;') : s;
}

function openProject(p) {
  document.getElementById('mo-project-title').textContent = p ? 'Edit Project' : 'New Project';
  const idEl = document.getElementById('p-id');
  idEl.value = p ? p.id : '';
  idEl.readOnly = !!p;
  idEl.style.opacity = p ? '0.5' : '1';
  document.getElementById('p-title').value  = p ? p.title   : '';
  document.getElementById('p-ver').value    = p ? p.version : '';
  document.getElementById('p-cat').value    = p ? p.category: 'unity';
  document.getElementById('p-status').value = p ? p.status  : 'idea';
  document.getElementById('p-author').value = p ? p.author  : '';
  document.getElementById('p-desc').value   = p ? p.desc    : '';
  const ll = document.getElementById('p-links');
  ll.innerHTML = '';
  const links = p ? JSON.parse(p.links || '[]') : [];
  links.forEach(l => appendLink(l));
  const pl = document.getElementById('p-patches');
  pl.innerHTML = '';
  const patches = p ? JSON.parse(p.patch_notes || '[]') : [];
  patches.forEach(n => appendPatch(n));
  openModal('mo-project');
}

function editProject(p) { openProject(p); }

function appendLink(l) {
  l = l || {};
  const el = document.createElement('div');
  el.className = 'si';
  el.innerHTML = `
    <input placeholder="Label" value="${esc(l.label||'', true)}" data-key="label" style="min-width:80px"/>
    <input placeholder="https://..." value="${esc(l.href||'', true)}" data-key="href" style="flex:2"/>
    <select data-key="icon">
      <option value="github"${l.icon==='github'?' selected':''}>GitHub</option>
      <option value="store"${l.icon==='store'?' selected':''}>Store</option>
    </select>
    <button class="btn btn-d btn-sm" onclick="this.closest('.si').remove()">✕</button>`;
  document.getElementById('p-links').appendChild(el);
}
function addLink() { appendLink({}); }

function appendPatch(n) {
  n = n || {};
  const el = document.createElement('div');
  el.className = 'si';
  el.innerHTML = `
    <input placeholder="v1.0.0" value="${esc(n.version||'', true)}" data-key="version" style="min-width:90px"/>
    <input type="date" value="${esc(n.date||'', true)}" data-key="date" style="min-width:140px"/>
    <input placeholder="What changed" value="${esc(n.notes||'', true)}" data-key="notes" style="flex:2"/>
    <button class="btn btn-d btn-sm" onclick="this.closest('.si').remove()">✕</button>`;
  document.getElementById('p-patches').appendChild(el);
}
function addPatch() { appendPatch({ date: new Date().toISOString().slice(0,10) }); }

function collectList(id) {
  return [...document.getElementById(id).querySelectorAll('.si')].map(row => {
    const obj = {};
    row.querySelectorAll('[data-key]').forEach(el => { obj[el.dataset.key] = el.value; });
    return obj;
  });
}

async function saveProject() {
  const payload = {
    id:       document.getElementById('p-id').value.trim(),
    title:    document.getElementById('p-title').value.trim(),
    category: document.getElementById('p-cat').value,
    status:   document.getElementById('p-status').value,
    author:   document.getElementById('p-author').value.trim(),
    version:  document.getElementById('p-ver').value.trim(),
    desc:     document.getElementById('p-desc').value.trim(),
    links:       collectList('p-links'),
    patchNotes:  collectList('p-patches'),
  };
  if (!payload.id || !payload.title) { toast('ID and Title are required', 'er'); return; }
  try {
    const r = await api('POST', '/api/projects', payload);
    if (r.ok) { toast('Project saved ✓'); closeModal('mo-project'); loadProjects(); }
    else toast(r.error || 'Error saving', 'er');
  } catch(e) { toast('Error: ' + e.message, 'er'); }
}

async function delProject(id, title) {
  if (!confirm(`Delete "${title}"? This cannot be undone.`)) return;
  try {
    await api('DELETE', '/api/projects/' + encodeURIComponent(id));
    toast('Deleted ' + id); loadProjects();
  } catch(e) { toast('Error: ' + e.message, 'er'); }
}

// ─────────────────────────────────────────────
// PIPELINE
// ─────────────────────────────────────────────
async function loadPipeline() {
  const rows = await api('GET', '/api/pipeline');
  document.getElementById('tb-pipeline').innerHTML = rows.length
    ? rows.map(p => `
      <tr>
        <td><code style="font-size:.7rem;color:var(--muted2)">${esc(p.id)}</code></td>
        <td style="color:var(--text);font-weight:500">${esc(p.title)}</td>
        <td><span class="badge ${badgeClass(p.type)}">${esc(p.type)}</span></td>
        <td style="font-size:.76rem">${esc(p.version) || '—'}</td>
        <td><div class="ar">
          <button class="btn btn-g btn-sm" onclick="editPipeline(${esc(JSON.stringify(p), true)})">Edit</button>
          <button class="btn btn-d btn-sm" onclick="delPipeline(${esc(JSON.stringify(p.id), true)})">Del</button>
        </div></td>
      </tr>`).join('')
    : '<tr><td colspan="5" style="text-align:center;color:var(--muted);padding:2rem;font-family:var(--mono);font-size:.72rem">No pipeline entries.</td></tr>';
}

function openPipeline(p) {
  document.getElementById('mo-pipeline-title').textContent = p ? 'Edit Entry' : 'New Pipeline Entry';
  const idEl = document.getElementById('pl-id');
  idEl.value = p ? p.id : ''; idEl.readOnly = !!p; idEl.style.opacity = p ? '0.5' : '1';
  document.getElementById('pl-title').value = p ? p.title   : '';
  document.getElementById('pl-type').value  = p ? p.type    : 'idea';
  document.getElementById('pl-ver').value   = p ? p.version : '';
  document.getElementById('pl-desc').value  = p ? p.desc    : '';
  openModal('mo-pipeline');
}
function editPipeline(p) { openPipeline(p); }

async function savePipeline() {
  const payload = {
    id:      document.getElementById('pl-id').value.trim(),
    title:   document.getElementById('pl-title').value.trim(),
    type:    document.getElementById('pl-type').value,
    version: document.getElementById('pl-ver').value.trim(),
    desc:    document.getElementById('pl-desc').value.trim(),
  };
  if (!payload.id || !payload.title) { toast('ID and Title are required', 'er'); return; }
  try {
    const r = await api('POST', '/api/pipeline', payload);
    if (r.ok) { toast('Pipeline entry saved ✓'); closeModal('mo-pipeline'); loadPipeline(); }
    else toast(r.error || 'Error saving', 'er');
  } catch(e) { toast('Error: ' + e.message, 'er'); }
}

async function delPipeline(id) {
  if (!confirm(`Delete "${id}"?`)) return;
  try { await api('DELETE', '/api/pipeline/' + encodeURIComponent(id)); toast('Deleted'); loadPipeline(); }
  catch(e) { toast('Error: ' + e.message, 'er'); }
}

// ─────────────────────────────────────────────
// TEAM
// ─────────────────────────────────────────────
async function loadTeam() {
  const rows = await api('GET', '/api/team');
  document.getElementById('tb-team').innerHTML = rows.length
    ? rows.map(m => `
      <tr>
        <td><code style="font-size:.7rem;color:var(--muted2)">${esc(m.id)}</code></td>
        <td style="color:var(--text);font-weight:500">${esc(m.name)}</td>
        <td>${esc(m.role)}</td>
        <td><div class="ar">
          <button class="btn btn-g btn-sm" onclick="editTeam(${esc(JSON.stringify(m), true)})">Edit</button>
          <button class="btn btn-d btn-sm" onclick="delTeam(${esc(JSON.stringify(m.id), true)},${esc(JSON.stringify(m.name), true)})">Del</button>
        </div></td>
      </tr>`).join('')
    : '<tr><td colspan="4" style="text-align:center;color:var(--muted);padding:2rem;font-family:var(--mono);font-size:.72rem">No team members.</td></tr>';
}

function openTeam(m) {
  document.getElementById('mo-team-title').textContent = m ? 'Edit Member' : 'New Team Member';
  const idEl = document.getElementById('tm-id');
  idEl.value = m ? m.id : ''; idEl.readOnly = !!m; idEl.style.opacity = m ? '0.5' : '1';
  document.getElementById('tm-name').value   = m ? m.name   : '';
  document.getElementById('tm-role').value   = m ? m.role   : '';
  document.getElementById('tm-avatar').value = m ? m.avatar : '';
  openModal('mo-team');
}
function editTeam(m) { openTeam(m); }

async function saveTeam() {
  const payload = {
    id:     document.getElementById('tm-id').value.trim(),
    name:   document.getElementById('tm-name').value.trim(),
    role:   document.getElementById('tm-role').value.trim(),
    avatar: document.getElementById('tm-avatar').value.trim(),
  };
  if (!payload.id || !payload.name) { toast('ID and Name are required', 'er'); return; }
  try {
    const r = await api('POST', '/api/team', payload);
    if (r.ok) { toast('Team member saved ✓'); closeModal('mo-team'); loadTeam(); }
    else toast(r.error || 'Error saving', 'er');
  } catch(e) { toast('Error: ' + e.message, 'er'); }
}

async function delTeam(id, name) {
  if (!confirm(`Remove ${name}?`)) return;
  try { await api('DELETE', '/api/team/' + encodeURIComponent(id)); toast('Removed'); loadTeam(); }
  catch(e) { toast('Error: ' + e.message, 'er'); }
}

// ─────────────────────────────────────────────
// BACKGROUND UPLOAD
// ─────────────────────────────────────────────
async function loadBgFiles() {
  try {
    const files = await api('GET', '/api/background');
    const el = document.getElementById('bg-file-list');
    el.innerHTML = files.length
      ? files.map(f => `
        <div class="bg-file">
          <span><code>${f.file}</code> — ${f.size}</span>
          <button class="btn btn-d btn-sm" onclick="deleteBg('${f.file.split('.').pop()}')">Remove</button>
        </div>`).join('')
      : '<div style="font-family:var(--mono);font-size:.7rem;color:var(--muted);margin-top:.5rem">No background file uploaded yet.</div>';
  } catch(e) { console.error(e); }
}

async function uploadBg(file) {
  if (!file) return;
  const status = document.getElementById('bg-upload-status');
  status.textContent = `Uploading ${file.name} (${(file.size/1048576).toFixed(1)} MB)…`;
  const fd = new FormData();
  fd.append('file', file);
  try {
    const r = await fetch('/api/background', { method: 'POST', body: fd });
    const data = await r.json();
    if (data.ok) {
      toast(`Uploaded → ${data.path} (${data.size})`);
      status.textContent = `✓ Saved as ${data.path}`;
      loadBgFiles();
    } else {
      toast(data.error || 'Upload failed', 'er');
      status.textContent = 'Upload failed: ' + (data.error || 'unknown error');
    }
  } catch(e) {
    toast('Upload error: ' + e.message, 'er');
    status.textContent = 'Error: ' + e.message;
  }
  document.getElementById('bg-input').value = '';
}

function onDrop(e) {
  e.preventDefault();
  document.getElementById('dropzone').classList.remove('over');
  const file = e.dataTransfer.files[0];
  if (file) uploadBg(file);
}

async function deleteBg(ext) {
  if (!confirm(`Remove bg.${ext}?`)) return;
  try {
    await api('DELETE', '/api/background/' + ext);
    toast('Removed bg.' + ext);
    loadBgFiles();
  } catch(e) { toast('Error: ' + e.message, 'er'); }
}

// ─────────────────────────────────────────────
// SETTINGS
// ─────────────────────────────────────────────
async function loadSettings() {
  try {
    const s = await api('GET', '/api/settings');
    document.getElementById('s-name').value  = s.studioName || '';
    document.getElementById('s-email').value = s.email      || '';
    document.getElementById('s-url').value   = s.siteUrl    || '';
    document.getElementById('s-tag').value   = s.tagline    || '';
  } catch(e) { toast('Error loading settings', 'er'); }
}

async function saveSettings() {
  try {
    const r = await api('POST', '/api/settings', {
      studioName: document.getElementById('s-name').value,
      email:      document.getElementById('s-email').value,
      siteUrl:    document.getElementById('s-url').value,
      tagline:    document.getElementById('s-tag').value,
    });
    if (r.ok) toast('Settings saved ✓'); else toast(r.error || 'Error', 'er');
  } catch(e) { toast('Error: ' + e.message, 'er'); }
}

// ─────────────────────────────────────────────
// INJECT + DEPLOY
// ─────────────────────────────────────────────
async function doInject() {
  try {
    const r = await api('POST', '/api/inject');
    if (r.ok) toast(`Written to index.html — ${r.projects} projects, ${r.pipeline} pipeline, ${r.team} team`);
    else toast(r.error || 'Failed to write', 'er');
  } catch(e) { toast('Error: ' + e.message, 'er'); }
}

function openDeploy() {
  document.getElementById('deploy-status').innerHTML =
    '<div class="sd did"></div><span>Ready.</span>';
  document.getElementById('deploy-msg').value = '';
  openModal('mo-deploy');
}

async function doDeploy() {
  const btn    = document.getElementById('deploy-btn');
  const status = document.getElementById('deploy-status');
  btn.disabled = true; btn.textContent = 'Deploying…';
  status.innerHTML = '<div class="sd did"></div><span>Writing index.html and pushing to GitHub…</span>';
  const msg = document.getElementById('deploy-msg').value.trim();
  try {
    const r = await api('POST', '/api/deploy', { message: msg || null });
    if (r.ok) {
      status.innerHTML = '<div class="sd dok"></div><span>Pushed ✓ — site updates in ~30s</span>';
      toast('Deployed successfully ✓');
    } else {
      status.innerHTML = `<div class="sd der"></div><span>${r.error || 'Push failed'}</span>`;
      toast('Deploy failed — see status', 'er');
    }
  } catch(e) {
    status.innerHTML = `<div class="sd der"></div><span>${e.message}</span>`;
    toast('Error: ' + e.message, 'er');
  }
  btn.disabled = false; btn.textContent = '🚀 Deploy';
}

// ─────────────────────────────────────────────
// INIT
// ─────────────────────────────────────────────
loadProjects();
loadPipeline();
loadTeam();
</script>
</body>
</html>"""


@app.route("/")
def index():
    return render_template_string(UI)


if __name__ == "__main__":
    init_db()
    print(f"\n  TBT Admin  →  http://localhost:5050")
    print(f"  Repo root  :  {BASE}")
    print(f"  Database   :  {DB}")
    print(f"  index.html :  {INDEX_HTML}\n")
    Timer(0.8, lambda: webbrowser.open("http://localhost:5050")).start()
    app.run(host="127.0.0.1", port=5050, debug=False)
