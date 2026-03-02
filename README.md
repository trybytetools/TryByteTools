# Try Byte Tools — Website

Live site: **https://trybytetools.github.io/TryByteTools/**

---

## Folder Structure

```
TryByteTools/
├── Website/                  ← This repo (online)
│   ├── index.html
│   ├── projects.html
│   ├── styles.css
│   ├── projects-data.js      ← Auto-generated, do not edit directly
│   └── assets/
│       └── avatars/          ← Team member avatars (gitignored)
│
└── Website Controller/       ← Local only, never pushed to GitHub
    ├── admin.py              ← Run this to manage the site
    └── admin-data/           ← Local backups & data store
```

---

## Making Changes

All content edits go through the **admin panel**, not directly in code.

```bash
# From the Website Controller folder:
python admin.py
# Opens at http://localhost:5050
```

- **Update Offline** — writes `projects-data.js` to the Website folder locally.
- **Update Online** — runs `git add / commit / push` on this repo to deploy live.

---

## Tech Stack

- Vanilla HTML / CSS / JS — no build step, no framework
- `projects-data.js` is the single source of truth for all dynamic content
- Hosted via GitHub Pages

---

## Contributing

Reach out at **TryByteTools@gmail.com** or open an issue.
