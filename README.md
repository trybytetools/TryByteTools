# Try Byte Tools

**A small indie studio building Unity tools, games, and 3D assets.**

🌐 **[trybytetools.github.io/TryByteTools](https://trybytetools.github.io/TryByteTools/)**

---

## What We Make

| Category | Description |
|---|---|
| **Unity Tools** | Editor extensions and utilities for Unity developers |
| **Games** | Small, focused indie games |
| **3D Assets** | Models and packs for game development |

---

## Projects

### 🔵 Folder Icons — *In Dev*
Right-click any folder in the Unity Project window to assign a custom color or icon. GUID-based persistence, zero runtime cost, easily importable.

### 🟡 Scene Sticky Notes — *In Dev*
Play-in-scene sticky notes for 2D & 3D editors. Organize notes, pass tasks to teammates, or leave breadcrumbs for your next session.

### ✅ Unity Inspector Refresh Fix — *Live*
Fixes an issue in Unity 6.3 where the Inspector doesn't show the selected object or file. Confirmed working on Cosmic OS (Pop OS).
→ [GitHub](https://github.com/trybytetools/Unity-Inspector-Refresh-Fix-COSMIC-OS/tree/main)

---

## The Team

| Handle | Role |
|---|---|
| **Dminx** | Solo Dev |
| **Robix** | Inspiration |

---

## Stack

This site is a single-page app with no framework and no build step.

```
index.html          ← entire site
admin/              ← Decap CMS content editor
data/               ← JSON content files (projects, team, pipeline)
assets/             ← uploads and media
.github/workflows/  ← auto-updates content manifest on new CMS entries
```

Content is managed through [Decap CMS](https://decapcms.org/) at `/admin/` — every save commits directly to this repo and the site rebuilds in ~30 seconds via GitHub Pages.

---

## Contact

📧 [TryByteTools@gmail.com](mailto:TryByteTools@gmail.com)

---

<sub>Built with vanilla HTML/CSS/JS · Hosted on GitHub Pages · No corporate nonsense</sub>
