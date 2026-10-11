/* The Promise Ledger: renders data/status.json and data/history.jsonl. Dates are calendar dates and are
   formatted in UTC so that no reader's time zone shifts them; the run time is shown in US Eastern. */
"use strict";
(function () {
  const $ = s => document.querySelector(s);
  const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const num = (v, d = 0) => v == null ? "–" : Number(v).toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });
  const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const period = (k, f) => !k ? "–" : k.length === 7 ? `${MON[+k.slice(5, 7) - 1]} ${k.slice(0, 4)}` : new Date(k + "T00:00:00Z").toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", timeZone: "UTC" });
  const STATUS = { "on track": "good", "better": "good", "off track": "bad", "worse": "bad", "mixed": "mid", "unchanged": "mid" };

  function fmtVal(v, unit) {
    if (v == null) return "–";
    const a = Math.abs(v);
    if (unit === "$" || unit === "$/gal") return "$" + num(v, 2);
    if (unit === "%") return num(v, 1) + "%";
    if (unit === "index") return num(v, 1);
    if (unit === "$ million") return (a >= 1e6 ? "$" + num(v / 1e6, 2) + " trillion" : a >= 1e3 ? "$" + num(v / 1e3, 1) + " billion" : "$" + num(v, 0) + " million");
    if (unit === "thousand barrels") return num(v / 1e3, 1) + " million bbl";
    if (unit === "million cubic feet") return num(v / 1e6, 2) + " trillion cu ft";
    if (unit === "thousand b/d") return num(v / 1e3, 2) + " million b/d";
    if (unit === "thousands") return num(v / 1e3, 2) + " million";
    return num(v, 0);
  }
  function fmtChange(r) {
    if (r.change == null) return "–";
    const s = r.change > 0 ? "+" : "";
    return r.change_kind === "pct" ? `${s}${num(r.change, 1)}%` : r.unit === "%" ? `${s}${num(r.change, 1)} pts` : `${s}${fmtVal(r.change, r.unit)}`;
  }
  function spark(r) {
    const pts = r.spark || [];
    if (pts.length < 2) return "";
    const W = 220, H = 48, P = 3, vals = pts.map(p => p[1]).concat(r.target != null ? [r.target] : []).concat([r.baseline.value]);
    let lo = Math.min(...vals), hi = Math.max(...vals); if (hi === lo) { hi += 1; lo -= 1; }
    const x = i => P + i * (W - 2 * P) / (pts.length - 1), y = v => H - P - (v - lo) * (H - 2 * P) / (hi - lo);
    const iBase = pts.findIndex(p => p[0] === r.baseline.period);
    const path = pts.map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(p[1]).toFixed(1)}`).join("");
    return `<svg class="spark" viewBox="0 0 ${W} ${H}" role="img" aria-label="Series since 2023">
      <line x1="${P}" x2="${W - P}" y1="${y(r.baseline.value).toFixed(1)}" y2="${y(r.baseline.value).toFixed(1)}" class="base"/>
      ${iBase >= 0 ? `<line x1="${x(iBase).toFixed(1)}" x2="${x(iBase).toFixed(1)}" y1="0" y2="${H}" class="inaug"/>` : ""}
      ${r.target != null ? `<line x1="${P}" x2="${W - P}" y1="${y(r.target).toFixed(1)}" y2="${y(r.target).toFixed(1)}" class="target"/>` : ""}
      <path d="${path}" class="line"/></svg>`;
  }
  function kpi(r) {
    const tier = r.tier === "official-foia" ? `<span class="tier">ICE records via FOIA, released with delay</span>` : "";
    const prog = r.progress != null ? `<div class="prog"><div style="width:${Math.max(0, Math.min(100, r.progress)).toFixed(0)}%"></div></div><span class="fine">${num(r.progress, 0)}% of the way from the baseline to the target (${fmtVal(r.target, r.unit)})</span>` : "";
    const err = r.fetch_error ? `<p class="fine warn">This week's fetch failed; the last archived data are shown.</p>` : "";
    const band = (r.band != null ? `noise band: spread of ${r.span}-${r.freq === "W" ? "week" : "month"} changes before 2025, ±${r.change_kind === "pct" ? num(r.band, 1) + "%" : fmtVal(r.band, r.unit)}` : "no noise band (too little history): the sign decides") + (r.band_note ? ` (${esc(r.band_note)})` : "");
    return `<div class="kpi">
      <div class="kh"><span class="label">${esc(r.label)}</span><span class="pill ${STATUS[r.status] || "none"}">${esc(r.status)}</span></div>
      ${tier}
      <div class="kb">
        <div class="nums">
          <div><span class="fine">Latest</span><b>${fmtVal(r.latest && r.latest.value, r.unit)}</b><span class="fine">${period(r.latest && r.latest.period)}</span></div>
          <div><span class="fine">Baseline</span><b>${fmtVal(r.baseline && r.baseline.value, r.unit)}</b><span class="fine">${period(r.baseline && r.baseline.period)}</span></div>
          <div><span class="fine">Change</span><b>${fmtChange(r)}</b><span class="fine">${r.better === "lower" ? "lower is the promise" : "higher is the promise"}</span></div>
        </div>
        ${spark(r)}
      </div>
      ${prog}
      <p class="fine">${band}. Source: <a href="${esc(r.source.url)}" target="_blank" rel="noopener">${esc(r.source.name)}</a> (${esc(r.series)})</p>${err}
    </div>`;
  }
  function card(p) {
    return `<article class="card" id="${p.id}">
      <div class="ch"><h2>${esc(p.title)}</h2><span class="pill big ${STATUS[p.status] || "none"}">${esc(p.status)}</span></div>
      <blockquote>“${esc(p.quote)}”<cite><a href="${esc(p.url)}" target="_blank" rel="noopener">${esc(p.source)}</a></cite></blockquote>
      ${p.note ? `<p class="fine">${esc(p.note)}</p>` : ""}
      ${p.kpis.map(kpi).join("")}
    </article>`;
  }
  function trend(lines) {
    const pts = lines.filter(l => l.scheduled !== false).map(l => ({ d: l.as_of.slice(0, 10), s: l.summary })).filter(p => p.s && p.s.counted);
    if (pts.length < 2) return `<p class="fine">The weekly trend appears from the second Monday on.</p>`;
    const W = 640, H = 90, P = 6, x = i => P + i * (W - 2 * P) / (pts.length - 1), y = v => H - P - v * (H - 2 * P);
    const path = pts.map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(p.s.on_track / p.s.counted).toFixed(1)}`).join("");
    return `<h3>Share of promises on track, week by week</h3><svg class="trend" viewBox="0 0 ${W} ${H}"><path d="${path}" class="line"/></svg>
      <p class="fine">${period(pts[0].d)} to ${period(pts[pts.length - 1].d)}</p>`;
  }
  Promise.all([fetch("data/status.json").then(r => r.json()), fetch("data/history.jsonl").then(r => r.ok ? r.text() : "").catch(() => "")])
    .then(([S, H]) => {
      const s = S.summary, asof = new Date(S.as_of);
      const day = asof.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", year: "numeric", timeZone: "America/New_York" });
      const time = asof.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", timeZone: "America/New_York" });
      $("#summary").innerHTML = `As of ${day}, ${time} ET${S.scheduled ? "" : " (a run outside the Monday schedule)"}: <b>${s.on_track} of ${s.counted}</b> promises with current data on track · ${s.off_track} off track · ${s.mixed} mixed${s.total - s.counted ? ` · ${s.total - s.counted} without current data` : ""}.`;
      $("#promises").innerHTML = S.promises.map(card).join("");
      $("#trend").innerHTML = trend(H.split("\n").filter(Boolean).map(l => JSON.parse(l)));
    })
    .catch(e => { console.error(e); $("#summary").textContent = "The data could not be loaded."; });
})();
