// Orthogonal connector router for the HerWILL diagrams.
// wire(from, to, {from:'right', to:'left', color, dash, label, labelColor, via:[[x,y],...], mid, fo, to_off})
// Points are computed from the live element boxes, so arrows always land on their targets.
(function () {
  const NS = 'http://www.w3.org/2000/svg';
  const fig = () => document.getElementById('fig');
  function box(el) {
    const f = fig().getBoundingClientRect(), r = el.getBoundingClientRect();
    return { l: r.left - f.left, t: r.top - f.top, r: r.right - f.left, b: r.bottom - f.top,
             cx: (r.left + r.right) / 2 - f.left, cy: (r.top + r.bottom) / 2 - f.top };
  }
  function anchor(el, side, off) {
    const b = box(el); off = off || 0;
    if (side === 'right')  return [b.r, b.cy + off];
    if (side === 'left')   return [b.l, b.cy + off];
    if (side === 'top')    return [b.cx + off, b.t];
    if (side === 'bottom') return [b.cx + off, b.b];
    if (side === 'diamond-right')  return [b.r, b.cy];
    return [b.cx, b.cy];
  }
  let svg;
  function ensure() {
    if (svg) return svg;
    const f = fig();
    svg = document.createElementNS(NS, 'svg'); svg.id = 'wires';
    svg.setAttribute('width', f.offsetWidth); svg.setAttribute('height', f.offsetHeight);
    const defs = document.createElementNS(NS, 'defs'); svg.appendChild(defs); f.appendChild(svg);
    return svg;
  }
  function marker(color) {
    const id = 'm' + color.replace(/[^a-z0-9]/gi, '');
    if (document.getElementById(id)) return id;
    const m = document.createElementNS(NS, 'marker');
    m.setAttribute('id', id); m.setAttribute('viewBox', '0 0 10 10'); m.setAttribute('refX', '9'); m.setAttribute('refY', '5');
    m.setAttribute('markerWidth', '7'); m.setAttribute('markerHeight', '7'); m.setAttribute('orient', 'auto-start-reverse');
    const p = document.createElementNS(NS, 'path'); p.setAttribute('d', 'M0,0 L10,5 L0,10 z'); p.setAttribute('fill', color);
    m.appendChild(p); svg.querySelector('defs').appendChild(m); return id;
  }
  window.wire = function (a, b, o) {
    o = o || {}; ensure();
    const A = typeof a === 'string' ? document.getElementById(a) : a;
    const B = typeof b === 'string' ? document.getElementById(b) : b;
    const p0 = anchor(A, o.from || 'right', o.fo), p1 = anchor(B, o.to || 'left', o.to_off);
    let pts = [p0];
    if (o.via) pts = pts.concat(o.via.map(v => [v[0] === null ? p0[0] : v[0] === 'end' ? p1[0] : v[0],
                                                v[1] === null ? p0[1] : v[1] === 'end' ? p1[1] : v[1]]));
    else {
      const h = (o.from || 'right') === 'right' || (o.from || 'right') === 'left';
      if (h && Math.abs(p0[1] - p1[1]) > 0.5) { const mx = o.mid !== undefined ? o.mid : (p0[0] + p1[0]) / 2; pts.push([mx, p0[1]], [mx, p1[1]]); }
      if (!h && Math.abs(p0[0] - p1[0]) > 0.5) { const my = o.mid !== undefined ? o.mid : (p0[1] + p1[1]) / 2; pts.push([p0[0], my], [p1[0], my]); }
    }
    pts.push(p1);
    const color = o.color || '#1f2933';
    const path = document.createElementNS(NS, 'path');
    let d = 'M' + pts[0].join(',');
    const r = 8;
    for (let i = 1; i < pts.length - 1; i++) {     // rounded orthogonal corners
      const [x0, y0] = pts[i - 1], [x1, y1] = pts[i], [x2, y2] = pts[i + 1];
      const d1 = Math.hypot(x1 - x0, y1 - y0), d2 = Math.hypot(x2 - x1, y2 - y1);
      const rr = Math.min(r, d1 / 2, d2 / 2);
      const ax = x1 - (x1 - x0) / (d1 || 1) * rr, ay = y1 - (y1 - y0) / (d1 || 1) * rr;
      const bx = x1 + (x2 - x1) / (d2 || 1) * rr, by = y1 + (y2 - y1) / (d2 || 1) * rr;
      d += ` L${ax},${ay} Q${x1},${y1} ${bx},${by}`;
    }
    d += ' L' + pts[pts.length - 1].join(',');
    path.setAttribute('d', d); path.setAttribute('fill', 'none'); path.setAttribute('stroke', color);
    path.setAttribute('stroke-width', o.width || 2.4);
    if (o.dash) path.setAttribute('stroke-dasharray', '7 5');
    if (!o.noarrow) path.setAttribute('marker-end', 'url(#' + marker(color) + ')');
    svg.appendChild(path);
    if (o.label) {
      const L = document.createElement('div'); L.className = 'wlabel'; L.textContent = o.label;
      L.style.background = o.labelColor || color; fig().appendChild(L);
      const seg = o.labelSeg !== undefined ? o.labelSeg : Math.floor((pts.length - 1) / 2);
      const [x0, y0] = pts[seg], [x1, y1] = pts[seg + 1];
      const t = o.labelT !== undefined ? o.labelT : 0.5;
      L.style.left = (x0 + (x1 - x0) * t - L.offsetWidth / 2 + (o.ldx || 0)) + 'px';
      L.style.top = (y0 + (y1 - y0) * t - L.offsetHeight / 2 + (o.ldy || 0)) + 'px';
    }
  };
})();
