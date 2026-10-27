// Full-screen reader: topics, weapons, units and conflicts as large, readable cards.
const R = document.getElementById('reader'), RB = document.getElementById('rbody'), RT = document.getElementById('rtitle');
const stack = []; // pages to go back to
let current = null;

function openPage(page, push = true) {
  if (push && current) stack.push(current);
  current = page;
  RT.textContent = page.title;
  rback.hidden = !stack.length;
  RB.innerHTML = page.html();
  R.hidden = false;
  R.scrollTop = 0;
  if (page.after) page.after();
}
function closeReader() { R.hidden = true; stack.length = 0; current = null; }
function goBack() { if (stack.length) openPage(stack.pop(), false); else closeReader(); }
rback.onclick = goBack;
rclose.onclick = closeReader;
document.addEventListener('keydown', e => { if (e.key == 'Escape' && !R.hidden) goBack(); });

const ICON = {'Aircraft & drones':'✈️','Warships & boats':'🚢','Submarines':'🌊','Tanks & armoured vehicles':'🛡️',
  'Missiles, rockets & torpedoes':'🚀','Artillery':'💥','Small arms':'🔫','Satellites & space':'🛰️',
  'Radar, electronics & other tech':'📡','Bases':'🏠','Nuclear tests':'☢️','Incidents: crashes, shootdowns & sinkings':'⚠️'};

// a picture that uses the saved copy offline, the web copy online, and an icon if neither works
function pic(file, icon, w) {
  const src = localImg(file) || (file ? webImg(file, w || 400) : '');
  return src ? `<img src="${src}" loading="lazy" alt="" onerror="this.outerHTML='<div class=noimg>${icon || '🖼️'}</div>'">`
             : `<div class="noimg">${icon || '🖼️'}</div>`;
}
const fact = (label, value) => value ? `<div class="fact"><span>${esc(label)}</span><b>${esc(value)}</b></div>` : '';

// ---------- equipment ----------
const usersOf = {}; // qid -> countries operating it
Object.entries(EQUIP).forEach(([iso, cats]) => Object.values(cats).forEach(l => l.forEach(e => (usersOf[e[5]] = usersOf[e[5]] || []).push(iso))));

function equipCard(e, cat) {
  return `<button class="card" onclick="openItem('${e[5]}')">${pic(e[4], ICON[cat])}
    <div class="ctext"><b>${esc(e[0])}</b>${e[2] ? `<p>${esc(e[2])}</p>` : ''}
    <div class="chips">${e[7] ? `<span>Since ${esc(e[7])}</span>` : ''}${e[3] ? `<span>Made in ${esc(nm(e[3]))}</span>` : ''}${e[8] ? `<span>${Number(e[8]).toLocaleString()} built</span>` : ''}</div></div></button>`;
}
function findItem(qid) {
  for (const cats of Object.values(EQUIP)) for (const [cat, l] of Object.entries(cats)) { const e = l.find(x => x[5] == qid); if (e) return [e, cat]; }
  return [];
}
function openEquip(iso, cat) {
  const items = EQUIP[iso][cat], order = (X.kind_order || {})[cat] || [], groups = {};
  items.forEach(e => (groups[e[1]] = groups[e[1]] || []).push(e));
  const kinds = Object.keys(groups).sort((a, b) => ((order.indexOf(a) + 1) || 99) - ((order.indexOf(b) + 1) || 99));
  // best-known first: used by more countries, then pictured, then more details
  const score = e => (usersOf[e[5]] || []).length * 10 + (e[4] ? 5 : 0) + (e[2] ? 1 : 0) + (e[6] ? 1 : 0);
  kinds.forEach(k => groups[k].sort((a, b) => score(b) - score(a) || a[0].localeCompare(b[0])));
  openPage({ title: `${nm(iso)}: ${cat}`, html: () => `
    <p class="lead">${esc(INFO[cat] || '')}</p>
    <p class="muted">${items.length.toLocaleString()} items, grouped by kind. Click any card for its photo and full details.</p>
    <input class="rfind" placeholder="Search these ${items.length.toLocaleString()} items…" oninput="filterCards(this.value)">
    <div class="jump">${kinds.map((k, i) => `<a href="#k${i}" onclick="event.preventDefault();document.getElementById('k${i}').scrollIntoView({behavior:'smooth'})">${esc(k)} <small>${groups[k].length}</small></a>`).join('')}</div>
    ${kinds.map((k, i) => { const ex = (X.kind_example || {})[k];
      return `<section id="k${i}" class="kindsec"><div class="khead">${ex && localImg(ex.img) ? `<img src="${localImg(ex.img)}" alt="">` : ''}
        <div><h2>${esc(k)} <small>${groups[k].length}</small></h2><p>${esc(INFO[k] || '')}</p>${ex && localImg(ex.img) ? `<p class="muted">Photo: ${esc(ex.name)}</p>` : ''}</div></div>
        <div class="grid" data-kind="${i}"></div></section>`; }).join('')}`,
    after: () => kinds.forEach((k, i) => fillGrid(document.querySelector(`.grid[data-kind="${i}"]`), groups[k], e => equipCard(e, cat)))
  });
}
// draws cards in chunks so big lists stay fast
function fillGrid(el, list, card, start = 0) {
  const step = 60, end = Math.min(list.length, start + step);
  el.querySelector('.more')?.remove();
  el.insertAdjacentHTML('beforeend', list.slice(start, end).map(card).join(''));
  if (end < list.length) {
    const b = document.createElement('button'); b.className = 'more'; b.textContent = `Show ${Math.min(step, list.length - end)} more of ${list.length - end} left`;
    b.onclick = () => fillGrid(el, list, card, end); el.appendChild(b);
  }
  el._all = list; el._card = card;
}
function filterCards(text) {
  const t = text.trim().toLowerCase();
  document.querySelectorAll('#rbody .grid').forEach(g => {
    g.innerHTML = '';
    const l = t ? g._all.filter(e => JSON.stringify(e).toLowerCase().includes(t)) : g._all, all = g._all;
    fillGrid(g, l, g._card); g._all = all;
    g.closest('section').hidden = !l.length;
  });
}
function openItem(qid) {
  const [e, cat] = findItem(qid); if (!e) return;
  const users = [...new Set(usersOf[qid] || [])].map(nm).sort();
  openPage({ title: e[0], html: () => `
    <div class="detail"><div class="bigpic">${pic(e[4], ICON[cat], 900)}</div>
    <div class="dtext"><p class="kindtag">${esc(cat)} › ${esc(e[1])}</p><h2>${esc(e[0])}</h2>
      ${e[2] ? `<p class="lead">${esc(e[2][0].toUpperCase() + e[2].slice(1))}.</p>` : ''}
      <div class="facts">${fact('In service / first flown', e[7])}${fact('Made in', e[3] ? nm(e[3]) : '')}${fact('Made by', e[6])}${fact('Number built', e[8] ? Number(e[8]).toLocaleString() : '')}</div>
      <h3>What is this kind of weapon?</h3><p>${esc(INFO[e[1]] || INFO[cat] || '')}</p>
      <h3>Used by ${users.length} ${users.length == 1 ? 'country' : 'countries'}</h3><p>${esc(users.join(', '))}</p>
      <h3>More about it</h3><div id="wiki" class="muted">Loading the Wikipedia summary…</div></div></div>`,
    after: () => wiki(qid) });
}
// Wikipedia summary (needs internet)
async function wiki(qid) {
  const box = document.getElementById('wiki');
  try {
    const w = await (await fetch(`https://www.wikidata.org/w/api.php?action=wbgetentities&ids=${qid}&props=sitelinks&sitefilter=enwiki&format=json&origin=*`)).json();
    const title = w.entities[qid].sitelinks.enwiki?.title;
    if (!title) { box.textContent = 'No Wikipedia article for this item.'; return; }
    const s = await (await fetch('https://en.wikipedia.org/api/rest_v1/page/summary/' + encodeURIComponent(title))).json();
    if (document.getElementById('wiki') !== box) return;
    box.className = '';
    box.innerHTML = `<p>${esc(s.extract || '')}</p><p><a href="https://en.wikipedia.org/wiki/${encodeURIComponent(title)}" target="_blank" rel="noopener">Read the full article on Wikipedia</a></p>`;
  } catch (err) { box.textContent = 'Connect to the internet to read more about it from Wikipedia.'; }
}

// ---------- forces ----------
function openForces(iso, kind) {
  const list = (FORCES[iso] || []).filter(f => f.kind == kind);
  openPage({ title: `${nm(iso)}: ${kind == 'Other branch' ? 'Other branches & units' : kind}`, html: () => `
    <p class="lead">${esc(INFO[kind] || '')}</p>
    <input class="rfind" placeholder="Search these ${list.length} units…" oninput="filterCards(this.value)">
    <section><div class="grid" id="fgrid"></div></section>`,
    after: () => fillGrid(document.getElementById('fgrid'), list, f => `<button class="card unit" onclick="openUnit('${iso}','${f.q}')">${pic(f.img, '🎖️')}
      <div class="ctext"><b>${esc(f.name)}</b>${f.desc ? `<p>${esc(f.desc)}</p>` : ''}<div class="chips">${f.founded ? `<span>Founded ${esc(f.founded)}</span>` : ''}${f.ended ? `<span>Disbanded ${esc(f.ended)}</span>` : ''}</div></div></button>`) });
}
function openUnit(iso, q) {
  const f = (FORCES[iso] || []).find(x => x.q == q); if (!f) return;
  openPage({ title: f.name, html: () => `<div class="detail"><div class="bigpic contain">${pic(f.img, '🎖️', 600)}</div>
    <div class="dtext"><p class="kindtag">${esc(nm(iso))} › ${esc(f.kind)}</p><h2>${esc(f.name)}</h2>${f.desc ? `<p class="lead">${esc(f.desc[0].toUpperCase() + f.desc.slice(1))}.</p>` : ''}
    <div class="facts">${fact('Country', nm(iso))}${fact('Founded', f.founded)}${fact('Disbanded', f.ended)}</div>
    <h3>What is this?</h3><p>${esc(INFO[f.kind] || '')}</p>
    <h3>More about it</h3><div id="wiki" class="muted">Loading the Wikipedia summary…</div></div></div>`, after: () => wiki(q) });
}

// ---------- conflicts ----------
function openConflicts(iso) {
  const list = iso ? (confOf[iso] || []) : CONF, act = list.filter(c => isActive(c, iso)), past = list.filter(c => !isActive(c, iso));
  const card = c => `<div class="ccard${isActive(c, iso) ? ' on' : ''}">${isActive(c, iso) ? '<span class="live">ACTIVE</span>' : ''}
    <h3>${esc(c.location)}${c.territory ? ': ' + esc(c.territory) : ''}</h3>
    <p class="vs"><b>${esc(sides(c.side_a))}</b><br><span>against</span><br><b>${esc(sides(c.side_b))}</b></p>
    <div class="facts">${fact('Years', `${c.first}–${c.active ? 'present' : c.last}`)}${fact('Years of fighting', String(c.years_active))}${fact('Years at war level', c.war_years ? String(c.war_years) : 'none')}${fact('Fought over', c.incompatibility)}</div>
    <p><b>${esc(c.type)}:</b> ${esc(INFO[c.type] || '')}</p>
    ${c.involved.length > 1 ? `<p class="muted">Countries involved: ${esc(c.involved.map(nm).join(', '))}</p>` : ''}</div>`;
  openPage({ title: iso ? `${nm(iso)}: conflicts & wars` : 'All armed conflicts since 1946', html: () => `
    <p class="lead">${esc(GUIDE_TOPICS[1][1])}</p>
    <input class="rfind" placeholder="Search conflicts…" oninput="this.parentNode.querySelectorAll('.ccard').forEach(x=>x.hidden=!x.textContent.toLowerCase().includes(this.value.toLowerCase()))">
    ${act.length ? `<h2>Active now (${act.length})</h2><div class="cgrid">${act.map(card).join('')}</div>` : ''}
    ${past.length ? `<h2>Past conflicts (${past.length})</h2><div class="cgrid">${past.map(card).join('')}</div>` : ''}
    ${iso && DISP[iso] ? `<h2>Disputed territories (${DISP[iso].length})</h2><div class="cgrid">${DISP[iso].map(d => `<div class="ccard"><h3>${esc(d.name)}</h3>${d.desc ? `<p>${esc(d.desc)}</p>` : ''}<p class="muted">Claimed by: ${esc(d.claimants.map(nm).join(', '))}</p></div>`).join('')}</div>` : ''}` });
}

// ---------- guide ----------
function openGuide() {
  const cards = l => `<div class="ggrid">${l.map(k => { const ex = (X.kind_example || {})[k];
    return `<div class="gitem">${ex ? pic(ex.img, '📘') : ''}<div><b>${esc(k)}</b><p>${esc(INFO[k] || '')}</p>${ex ? `<p class="muted">Photo: ${esc(ex.name)}</p>` : ''}</div></div>`; }).join('')}</div>`;
  openPage({ title: 'Guide', html: () => `
    <p class="lead">What every topic, kind of conflict, military force and kind of weapon in this app means.</p>
    <div class="jump"><a onclick="document.getElementById('g-topics').scrollIntoView({behavior:'smooth'})">Topics</a><a onclick="document.getElementById('g-conf').scrollIntoView({behavior:'smooth'})">Conflicts</a><a onclick="document.getElementById('g-forces').scrollIntoView({behavior:'smooth'})">Military forces</a>${X.equipment_order.map((c, i) => `<a onclick="document.getElementById('g-c${i}').scrollIntoView({behavior:'smooth'})">${ICON[c] || ''} ${esc(c)}</a>`).join('')}</div>
    <h2 id="g-topics">Topics</h2><div class="ggrid">${GUIDE_TOPICS.map(([t, d]) => `<div class="gitem"><div><b>${esc(t)}</b><p>${esc(d)}</p></div></div>`).join('')}</div>
    <h2 id="g-conf">Kinds of conflict</h2>${cards(Object.values(CTYPES))}
    <h2 id="g-forces">Military forces</h2>${cards(['Armed forces', 'Army', 'Navy', 'Air force', 'Special forces', 'Other branch'])}
    ${X.equipment_order.map((c, i) => `<h2 id="g-c${i}">${ICON[c] || ''} ${esc(c)}</h2><p>${esc(INFO[c] || '')}</p>${cards((X.kind_order || {})[c] || [])}`).join('')}
    ${note()}` });
}

// ---------- whole country on one page ----------
function openCountry(iso) {
  const d = byIso[iso], eq = EQUIP[iso] || {}, fs = FORCES[iso] || [];
  openPage({ title: d.name, html: () => {
    const p = (X.people || {})[iso] || {}, flag = localImg(p.flag);
    const btn = (label, n, js, icon) => `<button class="tile" onclick="${js}"><span class="ticon">${icon || ''}</span><b>${esc(label)}</b><small>${n.toLocaleString()}</small></button>`;
    return `<div class="chead">${flag ? `<img class="bigflag" src="${flag}" alt="">` : ''}<div><h2>${esc(d.name)}</h2><p class="muted">${esc(d.region)}</p></div></div>
      ${leadersOf(iso).length ? `<div class="leaders">${leadersOf(iso).map(l => `<div class="leader">${pic(l.img, '👤')}<div><span>${esc(l.role)}</span><b>${esc(l.name)}</b><p>${esc(l.desc || '')}</p></div></div>`).join('')}</div>` : ''}
      <h2>Internet</h2><p class="lead">${d.offline}% of people (about ${fmt(d.offline_people)}) were offline in ${d.year}. ${esc(d.name)} ranks #${d.rank} of ${D.length} countries for the share of people offline.</p>
      <h2>Conflicts & wars</h2><p class="lead">${(confOf[iso] || []).length ? `${activeN(iso)} active and ${(confOf[iso] || []).length} total armed conflicts since 1946.` : 'No armed conflicts with 25+ deaths a year since 1946.'}${DISP[iso] ? ` ${DISP[iso].length} disputed territories.` : ''}</p>
      ${(confOf[iso] || []).length || DISP[iso] ? `<div class="tiles">${btn('Read all conflicts', (confOf[iso] || []).length + (DISP[iso] || []).length, `openConflicts('${iso}')`, '⚔️')}</div>` : ''}
      <h2>Military</h2>${militaryLead(iso)}
      ${fs.length ? `<h3>Forces & units</h3><div class="tiles">${X.force_order.filter(k => fs.some(f => f.kind == k)).map(k => btn(k == 'Other branch' ? 'Other branches & units' : k, fs.filter(f => f.kind == k).length, `openForces('${iso}','${k}')`, k == 'Special forces' ? '🎯' : '🎖️')).join('')}</div>` : ''}
      ${Object.keys(eq).length ? `<h3>Weapons, equipment & tech</h3><div class="tiles">${X.equipment_order.filter(c => eq[c]).map(c => btn(c, eq[c].length, `openEquip('${iso}','${c.replace(/'/g, "\\'")}')`, ICON[c])).join('')}</div>` : ''}
      <h2>Palantir</h2>${PC[iso] ? `<p class="lead">${esc(LV[PC[iso].level])}.</p>${PC[iso].items.map(x => `<div class="pitem"><span class="tag" style="--c:${tcol(x.type)}">${esc(x.type)}</span><b>${esc(x.title)}</b><p>${esc(x.detail)}</p><p class="muted">${[x.date, x.status].filter(Boolean).map(esc).join(' · ')} · <a href="${esc(x.source)}" target="_blank" rel="noopener">Source</a></p></div>`).join('')}` : '<p class="muted">No reported Palantir government contracts, incidents or issues.</p>'}
      ${note()}`; } });
}
function militaryLead(iso) {
  const m = MIL[iso] || {};
  const parts = [];
  if (m.mil_usd) parts.push(`spends ${money(m.mil_usd[0])} a year on its military (${m.mil_usd[1]})`);
  if (m.mil_pct_gdp) parts.push(`${m.mil_pct_gdp[0]}% of its economy`);
  if (m.mil_personnel) parts.push(`has about ${fmt(m.mil_personnel[0])} people in its armed forces (${m.mil_personnel[1]})`);
  return parts.length ? `<p class="lead">${esc(nm(iso))} ${parts.join(', ')}.</p>` : '';
}
