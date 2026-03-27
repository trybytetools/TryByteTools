/* TBT:DATA:START */
const DATA = {
  "settings": {
    "studioName": "Try Byte Tools",
    "email": "TryByteTools@gmail.com",
    "siteUrl": "https://trybytetools.github.io/TryByteTools/",
    "tagline": "A small team that just wants to build cool stuff together."
  },
  "projects": [
    {
      "id": "001",
      "title": "Folder Icons",
      "category": "unity",
      "tagLabel": "Unity Tool",
      "status": "wip",
      "author": "Dminx",
      "version": "1.0.0",
      "desc": "Right-click any folder in the Unity Project window to assign a custom color or icon. GUID-based persistence, zero runtime cost, easily importable.",
      "links": [{"label": "Asset Store", "href": "#", "icon": "store"}],
      "patchNotes": [{"version": "0.9.9", "date": "2026-03-10", "notes": "Waiting on release on the Unity Asset Store."}]
    },
    {
      "id": "002",
      "title": "Scene Sticky Notes",
      "category": "unity",
      "tagLabel": "Unity Tool",
      "status": "wip",
      "author": "Dminx",
      "version": "0.1.0",
      "desc": "Play-in-scene sticky notes for 2D & 3D editors. Organize notes, pass tasks to teammates, or set reminders.",
      "links": [],
      "patchNotes": [{"version": "0.1.0", "date": "2026-03-10", "notes": "Created the sticky note package — needs polishing before release."}]
    },
    {
      "id": "003",
      "title": "Unity Inspector Refresh Fix",
      "category": "unity",
      "tagLabel": "Unity Tool",
      "status": "live",
      "author": "Dminx",
      "version": "1.0.0",
      "desc": "Fixes an issue in Unity 6.3 where the Inspector does not show the selected object. Confirmed working on Cosmic OS.",
      "links": [{"label": "GitHub", "href": "https://github.com/trybytetools/Unity-Inspector-Refresh-Fix-COSMIC-OS/tree/main", "icon": "github"}],
      "patchNotes": [{"version": "1.0.0", "date": "2026-03-10", "notes": "Initial release. Uploaded to GitHub."}]
    }
  ],
  "pipeline": [
    {"id": "pl001", "title": "Scene Sticky Notes", "type": "update", "version": "0.1.0", "desc": "Play-in-scene sticky notes for 2D & 3D editors."}
  ],
  "team": [
    {"id": "t001", "name": "Dminx", "role": "Solo Dev", "avatar": ""},
    {"id": "t1002", "name": "Robix", "role": "Inspiration", "avatar": ""}
  ]
};
/* TBT:DATA:END */

(function() {
  const loader = document.getElementById('loader');
  const bar    = document.getElementById('loader-bar');
  let pct = 0;
  const fill = setInterval(() => {
    pct = Math.min(pct + (pct < 70 ? 2.2 : 0.6), 98);
    bar.style.width = pct + '%';
  }, 40);

  window.addEventListener('load', () => {
    setTimeout(() => {
      clearInterval(fill);
      bar.style.width = '100%';
      setTimeout(() => { loader.classList.add('done'); }, 200);
    }, 800);
  });

  setTimeout(() => { clearInterval(fill); loader.classList.add('done'); }, 3000);
})();

document.getElementById('bg-video').playbackRate = 0.8;

(function() {
  const dot = document.getElementById('cur');
  let tx = 0, ty = 0, cx = 0, cy = 0;
  let raf;

  document.addEventListener('mousemove', e => {
    tx = e.clientX; ty = e.clientY;
    if (!raf) raf = requestAnimationFrame(step);
  }, { passive: true });

  function step() {
    cx += (tx - cx) * 0.18;
    cy += (ty - cy) * 0.18;
    dot.style.left = cx + 'px';
    dot.style.top  = cy + 'px';
    if (Math.abs(tx - cx) > 0.1 || Math.abs(ty - cy) > 0.1) {
      raf = requestAnimationFrame(step);
    } else {
      raf = null;
    }
  }

  document.addEventListener('mouseleave', () => { dot.style.opacity = '0'; });
  document.addEventListener('mouseenter', () => { dot.style.opacity = '1'; });
})();

(function() {
  const nav     = document.getElementById('nav');
  const navLinks= nav.querySelectorAll('.nav-links a, .nav-drawer a');
  const SECS    = ['home','pipeline','projects','changelog','about','contact'];

  const tlEl = document.getElementById('timeline');
  if (tlEl) {
    new IntersectionObserver(entries => {
      entries.forEach(e => { if (e.isIntersecting) tlEl.classList.add('line-in'); });
    }, { threshold: 0.08 }).observe(tlEl);
  }

  const prefersReducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  const scrollBehavior = prefersReducedMotion ? 'auto' : 'smooth';
  const terminalEl = document.querySelector('.terminal');
  const terminalNextBtn = document.getElementById('terminal-next');
  let navigating = false;

  function goToPipeline() {
    if (navigating) return;
    const el = document.getElementById('pipeline');
    if (!el) return;
    navigating = true;
    el.scrollIntoView({ behavior: scrollBehavior, block: 'start' });
    setTimeout(() => { navigating = false; }, 650);
  }

  if (terminalNextBtn) terminalNextBtn.addEventListener('click', goToPipeline);

  if (terminalEl) {
    let sx = 0;
    let sy = 0;
    let startTs = 0;

    terminalEl.addEventListener('touchstart', (e) => {
      if (!e.touches || e.touches.length !== 1) return;
      const t = e.touches[0];
      sx = t.clientX;
      sy = t.clientY;
      startTs = Date.now();
    }, { passive: true });

    terminalEl.addEventListener('touchend', (e) => {
      if (!startTs || !e.changedTouches || e.changedTouches.length !== 1) return;
      const t = e.changedTouches[0];
      const dx = t.clientX - sx;
      const dy = t.clientY - sy;
      startTs = 0;

      if (dx < -70 && Math.abs(dy) < 95) goToPipeline();
    }, { passive: true });
  }

  const scrollRoot = document.documentElement;
  window.addEventListener('scroll', () => {
    const sy = window.scrollY;
    nav.classList.toggle('scrolled', sy > 40);

    let current = 'home';
    SECS.forEach(id => {
      const el = document.getElementById(id);
      if (el && sy >= el.offsetTop - window.innerHeight / 2) current = id;
    });

    navLinks.forEach(a => {
      a.classList.toggle('active', a.getAttribute('href') === '#' + current);
    });
  }, { passive: true });

  const hb = document.getElementById('hamburger');
  const drawer = document.getElementById('nav-drawer');
  hb.addEventListener('click', () => {
    const open = hb.classList.toggle('open');
    hb.setAttribute('aria-expanded', open);
    drawer.classList.toggle('open', open);
    drawer.setAttribute('aria-hidden', !open);
    document.body.style.overflow = open ? 'hidden' : '';
  });
  drawer.querySelectorAll('a').forEach(a => a.addEventListener('click', () => {
    hb.classList.remove('open'); drawer.classList.remove('open');
    document.body.style.overflow = '';
  }));
  document.addEventListener('keydown', e => {
    if (e.key==='Escape') { hb.classList.remove('open'); drawer.classList.remove('open'); document.body.style.overflow=''; }
  });
})();

(function() {
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add('in'); obs.unobserve(e.target); }
    });
  }, { threshold: 0.08 });
  document.querySelectorAll('.reveal').forEach(el => obs.observe(el));

  const tlObs = new IntersectionObserver(entries => {
    entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('in-view'); });
  }, { threshold: 0.05 });
  const tl = document.getElementById('timeline');
  if (tl) tlObs.observe(tl);
})();

function initSpotlight(selector) {
  document.querySelectorAll(selector).forEach(card => {
    card.addEventListener('mousemove', e => {
      const r = card.getBoundingClientRect();
      card.style.setProperty('--mx', ((e.clientX-r.left)/r.width*100)+'%');
      card.style.setProperty('--my', ((e.clientY-r.top)/r.height*100)+'%');
    });
  });
}

function animateCount(el, target, dur=1400) {
  const start = performance.now();
  (function tick(now) {
    const p = Math.min((now-start)/dur,1);
    const ease = 1-Math.pow(1-p,3);
    el.textContent = Math.round(target*ease);
    if (p<1) requestAnimationFrame(tick); else el.textContent=target;
  })(start);
}

function initStats() {
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (!e.isIntersecting) return;
      e.target.querySelectorAll('[data-count]').forEach(el => animateCount(el, +el.dataset.count));
      obs.unobserve(e.target);
    });
  }, { threshold: 0.5 });
  const row = document.getElementById('stats-row');
  if (row) obs.observe(row);
}

const PROJ_MAP = Object.fromEntries(DATA.projects.map(p=>[p.id,p]));

function openPatchModal(projectId) {
  const p = PROJ_MAP[projectId];
  if (!p || !p.patchNotes?.length) return;
  document.getElementById('patch-modal-title').textContent = p.title + ' — Patch Notes';
  document.getElementById('patch-modal-body').innerHTML = p.patchNotes.map(n=>`
    <div class="patch-entry">
      <div class="patch-head">
        <span class="patch-ver">v${n.version}</span>
        <span class="patch-date">${n.date}</span>
      </div>
      <p class="patch-notes">${n.notes}</p>
    </div>`).join('');
  document.getElementById('patch-modal').classList.add('open');
}

document.getElementById('patch-modal-close').addEventListener('click', () => document.getElementById('patch-modal').classList.remove('open'));
document.getElementById('patch-modal').addEventListener('click', e => { if (e.target===document.getElementById('patch-modal')) document.getElementById('patch-modal').classList.remove('open'); });
document.addEventListener('keydown', e => { if (e.key==='Escape') document.getElementById('patch-modal').classList.remove('open'); });

const ICONS = {
  store: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="11" height="11" stroke-linecap="round" stroke-linejoin="round">
  <polyline points="11 6 5 6 5 19 16 19 16 13"></polyline>
  <polyline points="15 3 21 3 21 9"></polyline>
  <line x1="10" y1="14" x2="21" y2="3"></line>
</svg>`,
  github: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="11" height="11">
  <polyline points="16 18 22 12 16 6"></polyline>
  <polyline points="8 6 2 12 8 18"></polyline>
</svg>`,
  email: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="17" height="17">
  <rect x="2" y="4" width="20" height="16" rx="2"></rect>
  <polyline points="22 6 12 13 2 6"></polyline>
</svg>`
};

function renderPipeline() {
  document.getElementById('pipeline-list').innerHTML = DATA.pipeline.map((p,i)=>`
    <div class="pipeline-item pi-card reveal delay-${Math.min(i+1,4)}">
      <div class="pi-index">${String(i+1).padStart(2,'0')}</div>
      <div>
        <div class="pi-head">
          <span class="pi-title">${p.title}</span>
          <span class="pi-type type-${p.type}">${p.type.charAt(0).toUpperCase()+p.type.slice(1)}</span>
          ${p.version ? `<span class="pi-ver">v${p.version}</span>` : ''}
        </div>
        <p class="pi-desc">${p.desc}</p>
      </div>
    </div>`).join('');
}

const STATUS_LABEL = { live:'Live', wip:'In Dev', idea:'Idea', archived:'Archived' };

function buildProjectCard(p, idx) {
  const isLive    = p.status==='live';
  const isWide    = isLive && idx===0;
  const hasLinks  = p.links?.length > 0;
  const hasPatches= p.patchNotes?.length > 0;
  const linksHtml = hasLinks ? p.links.map(l=>`
    <a href="${l.href}" class="pcard-link" target="_blank" rel="noopener noreferrer">
      ${ICONS[l.icon]||''} ${l.label}
    </a>`).join('') : '';

  return `
    <div class="bento-item${isWide?' wide':''}" data-status="${p.status}" data-cat="${p.category}">
      <div class="pcard${isLive?' featured':''} reveal delay-${Math.min(idx+1,4)}">
        <span class="pcard-tag tag-${p.category}">${p.tagLabel}</span>
        <h3 class="pcard-title">${p.title}</h3>
        <p class="pcard-desc">${p.desc}</p>
        <div class="pcard-footer">
          <div style="display:flex;flex-direction:column;gap:4px;">
            <div class="pcard-status">
              <span class="status-dot ${p.status}"></span>${STATUS_LABEL[p.status]||p.status}
            </div>
            ${p.version?`<div class="pcard-version">
              v${p.version}
              ${hasPatches?`<button class="patch-btn" onclick="openPatchModal('${p.id}')">notes</button>`:''}
            </div>`:''}
          </div>
          <div class="pcard-links">${linksHtml}</div>
        </div>
      </div>
    </div>`;
}

let activeFilter = 'all';
function renderProjects(filter='all') {
  activeFilter = filter;
  const grid = document.getElementById('bento-grid');
  if (!grid.children.length) {
    grid.innerHTML = DATA.projects.map((p,i)=>buildProjectCard(p,i)).join('');
    initSpotlight('.pcard');
    const obs = new IntersectionObserver(entries => {
      entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); obs.unobserve(e.target); } });
    },{ threshold:0.06 });
    grid.querySelectorAll('.reveal').forEach(el=>obs.observe(el));
  }
  grid.querySelectorAll('.bento-item').forEach(item => {
    const show = filter==='all' || item.dataset.status===filter;
    item.classList.toggle('hidden', !show);
    if (show) item.style.display='';
    else item.style.display='none';
  });
}

document.getElementById('filter-tabs').addEventListener('click', e => {
  const btn = e.target.closest('.f-tab');
  if (!btn) return;
  document.querySelectorAll('.f-tab').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  renderProjects(btn.dataset.filter);
});

let activeClProj = 'all';

function buildAllEntries() {
  const entries = [];
  DATA.projects.forEach(proj => {
    (proj.patchNotes||[]).forEach(note => {
      entries.push({ ...note, projectId:proj.id, projectTitle:proj.title, category:proj.category, tagLabel:proj.tagLabel });
    });
  });
  return entries.sort((a,b)=> b.date.localeCompare(a.date));
}

function renderChangelog(projFilter='all') {
  const entries = buildAllEntries().filter(e => projFilter==='all' || e.projectId===projFilter);
  const tl = document.getElementById('timeline');

  if (!entries.length) { tl.innerHTML = '<div class="cl-empty">No entries yet for this project.</div>'; return; }

  const byYear = {};
  entries.forEach(e => { const y=e.date.slice(0,4); (byYear[y]=byYear[y]||[]).push(e); });
  const years = Object.keys(byYear).sort((a,b)=>b.localeCompare(a));

  tl.innerHTML = years.map(yr=>`
    <div class="tl-year">${yr}</div>
    ${byYear[yr].map(e=>{
      const [,mm,dd] = (e.date||'').split('-');
      const months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
      const dateStr = mm && dd ? `${parseInt(dd)} ${months[parseInt(mm)-1]}` : '';
      return `
        <div class="tl-entry glass-panel reveal">
          <div>
            <div class="tl-head">
              <div>
                <span class="tl-proj-tag pcard-tag tag-${e.category}">${e.tagLabel}</span>
              </div>
              <span class="tl-ver">v${e.version}</span>
            </div>
            <div class="tl-title">${e.projectTitle}</div>
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:.4rem;">
              <span class="tl-date">${dateStr}</span>
            </div>
            <p class="tl-notes">${e.notes}</p>
          </div>
        </div>`;
    }).join('')}
  `).join('');

  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); obs.unobserve(e.target); } });
  },{ threshold:0.08 });
  tl.querySelectorAll('.reveal').forEach(el=>obs.observe(el));
}

function renderChangelogSidebar() {
  const projs = DATA.projects.filter(p=>p.patchNotes?.length);
  const el = document.getElementById('cl-proj-list');
  el.innerHTML = `<button class="cl-proj-btn active" data-id="all">All Projects</button>`
    + projs.map(p=>`<button class="cl-proj-btn" data-id="${p.id}">${p.title}</button>`).join('');
  el.addEventListener('click', e => {
    const btn = e.target.closest('.cl-proj-btn');
    if (!btn) return;
    el.querySelectorAll('.cl-proj-btn').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    activeClProj = btn.dataset.id;
    renderChangelog(activeClProj);
  });
}

function renderTeam() {
  document.getElementById('team-grid').innerHTML = DATA.team.map((m,i)=>`
    <div class="team-card reveal delay-${i+1}">
      <div class="team-avatar">
        ${m.avatar?`<img src="${m.avatar}" alt="${m.name}">`:(m.name||'?').substring(0,2).toUpperCase()}
      </div>
      <div>
        <div class="team-name">${m.name}</div>
        <div class="team-role">${m.role}</div>
      </div>
    </div>`).join('');
}

function renderStats() {
  const live    = DATA.projects.filter(p=>p.status==='live').length;
  const active  = DATA.projects.filter(p=>p.status!=='archived').length;
  const members = DATA.team.length;
  document.getElementById('stats-row').innerHTML = `
    <div class="glass-panel"><span class="stat-num" data-count="${active}">${active}</span><div class="stat-label">Projects</div></div>
    <div class="glass-panel"><span class="stat-num" data-count="${live}">${live}</span><div class="stat-label">Live</div></div>
    <div class="glass-panel"><span class="stat-num" data-count="${members}">${members}</span><div class="stat-label">Team</div></div>`;
  initStats();
}

function renderContact() {
  const { email } = DATA.settings;
  document.getElementById('contact-links').innerHTML = `
    <a href="mailto:${email}" class="contact-card">
      <div class="contact-icon">${ICONS.email}</div>
      <div><div class="contact-label">Email</div><div class="contact-value">${email}</div></div>
    </a>
    <a href="https://github.com/trybytetools" class="contact-card" target="_blank" rel="noopener noreferrer">
      <div class="contact-icon">
        ${ICONS.github}
      </div>
      <div><div class="contact-label">GitHub</div><div class="contact-value">github.com/trybytetools</div></div>
    </a>`;
}

(function boot() {
  document.getElementById('footer-year').textContent = new Date().getFullYear();

  renderPipeline();
  renderProjects('all');
  renderChangelogSidebar();
  renderChangelog('all');
  renderTeam();
  renderStats();
  renderContact();

  requestAnimationFrame(() => {
    const obs = new IntersectionObserver(entries => {
      entries.forEach(en => {
        if (en.isIntersecting) { en.target.classList.add('in'); obs.unobserve(en.target); }
      });
    }, { threshold: 0.06 });
    document.querySelectorAll('.reveal:not(.in)').forEach(el => obs.observe(el));

    initSpotlight('.pcard');

    document.querySelectorAll('.mag-btn').forEach(btn => {
      btn.addEventListener('mousemove', e => {
        const r = btn.getBoundingClientRect();
        btn.style.transform = `translate(${(e.clientX-r.left-r.width/2)*0.18}px,${(e.clientY-r.top-r.height/2)*0.28}px) translateY(-3px)`;
      });
      btn.addEventListener('mouseleave', () => { btn.style.transform = ''; });
    });
  });
})();