/* shots.js: the plain-reading shots. Each draws one idea, readable in two seconds,
   with every label at a size a phone can read. Shared by media/video.html and the site.

   Uses the data data.js loads (WeightData.load): D.m is docs/data/manifest.json,
   D.baseTex / D.editTex are layer 15 drawn from the real weight files. Nothing here
   invents a number; every figure drawn is read from D.m at draw time. */
(function (g) {
  'use strict';
  var C = { ink: '#E6EAE4', soft: '#A9B5AC', dim: '#5E6A62', acc: '#F5B841', ground: '#0A0C0B',
            panel: '#0F1312', line: 'rgba(230,234,228,0.22)', wrong: '#333B36', flash: '#FFFFFF',
            edit: '#5ED0C0' };   // teal = what the edit changed; amber is kept for right answers
  var clamp01 = function (x) { return x < 0 ? 0 : x > 1 ? 1 : x; };
  var sm = function (x) { x = clamp01(x); return x * x * (3 - 2 * x); };
  var lerp = function (a, b, t) { return a + (b - a) * t; };
  var fmt = function (n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ','); };
  var LEVEL = ['BF16', 'Q8_0', 'Q4_K_M'], NAME = ['16-bit', '8-bit', '4-bit'];
  // Maths markup ($...$, \boxed{...}) is shown as it would render, not as source.
  var plain = function (s) { return s.replace(/\\boxed\{([^}]*)\}/g, '$1').replace(/\$/g, ''); };

  function font(x, size, weight, mono) {
    x.font = (weight || 400) + ' ' + size + 'px ' + (mono ? '"Geist Mono", ui-monospace, monospace' : '"Geist", system-ui, sans-serif');
  }
  function text(x, s, X, Y, size, color, o) {
    o = o || {};
    font(x, size, o.weight, o.mono);
    x.fillStyle = color; x.textAlign = o.align || 'left'; x.textBaseline = o.base || 'alphabetic';
    x.fillText(s, X, Y);
    return x.measureText(s).width;
  }
  function rrect(x, X, Y, W, H, r) {
    x.beginPath(); x.moveTo(X + r, Y); x.arcTo(X + W, Y, X + W, Y + H, r); x.arcTo(X + W, Y + H, X, Y + H, r);
    x.arcTo(X, Y + H, X, Y, r); x.arcTo(X, Y, X + W, Y, r); x.closePath();
  }

  // ------------------------------------------------------------ shot: the loop
  // A terminal showing the end of one real response. p 0..1 runs the original model
  // into the token limit; e 0..1 swaps in the edited model's answer, which stops.
  function loop(x, R, D, p, e) {
    var L = D.m.loop, lim = D.m.token_limit;
    x.save();
    rrect(x, R.x, R.y, R.w, R.h, 6); x.fillStyle = C.panel; x.fill();
    // original -> edited crossfades over e 0.3..0.65: nothing on the panel snaps in one frame
    var ae = sm((e - 0.3) / 0.35);
    x.lineWidth = 1.5; x.strokeStyle = C.line; x.stroke();
    if (ae > 0) { x.globalAlpha = ae; x.strokeStyle = 'rgba(245,184,65,0.7)'; x.stroke(); }
    x.globalAlpha = 1 - sm((e - 0.25) / 0.15); text(x, 'ORIGINAL MODEL', R.x + 18, R.y + 34, 20, C.soft, { mono: true, weight: 500 });
    x.globalAlpha = sm((e - 0.42) / 0.15); text(x, 'EDITED MODEL', R.x + 18, R.y + 34, 20, C.acc, { mono: true, weight: 500 });
    x.globalAlpha = 1;
    // body: lines scroll up, faster and faster
    var bodyTop = R.y + 52, bodyH = R.h - 52 - 84, lh = 32;
    x.save(); x.beginPath(); x.rect(R.x + 1, bodyTop, R.w - 2, bodyH); x.clip();
    if (e < 1) {
      x.globalAlpha = 1 - sm(e * 2);
      var pair = [L.line, plain(L.answer_line)];
      var scrolled = Math.pow(p, 2.2) * 60;               // lines scrolled past
      var first = Math.floor(scrolled), off = (scrolled - first) * lh;
      for (var i = 0; i < Math.ceil(bodyH / lh) + 2; i++) {
        var li = first + i, s = pair[li % 2], yy = bodyTop + 26 + i * lh - off;
        text(x, s, R.x + 18, yy, 22, li % 2 ? C.ink : C.soft, { mono: true });
      }
    }
    if (e > 0) {
      x.globalAlpha = sm(e * 2 - 1);
      var ans = plain(L.edited_tail[1]);
      var y0 = bodyTop + 26;
      text(x, '...', R.x + 18, y0, 22, C.soft, { mono: true });
      text(x, plain(L.edited_tail[0]), R.x + 18, y0 + lh, 20, C.soft, { mono: true });
      var w = text(x, ans, R.x + 30, y0 + 2.4 * lh, 30, C.ink, { mono: true, weight: 500 });
      x.strokeStyle = C.acc; x.lineWidth = 2; x.strokeRect(R.x + 20, y0 + 2.4 * lh - 30, w + 20, 42);
      text(x, 'Answer boxed. Stops.', R.x + w + 64, y0 + 2.4 * lh - 2, 22, C.acc, { weight: 500 });
    }
    x.restore();
    // counter (original model only)
    x.globalAlpha = 1 - sm(e * 3);
    var n = Math.round(L.repeats * Math.pow(clamp01(p), 2.2));
    text(x, 'written ' + fmt(n) + '×', R.x + R.w - 18, R.y + 34, 20, C.acc, { mono: true, weight: 500, align: 'right' });
    x.globalAlpha = 1;
    // token bar
    var bx = R.x + 18, bw = R.w - 36, by = R.y + R.h - 48, bh = 14;
    x.fillStyle = '#1C221F'; x.fillRect(bx, by, bw, bh);
    var oa = 1 - sm((e - 0.2) / 0.25), na = sm((e - 0.45) / 0.2);   // old bar and label leave, then the new ones arrive
    var tok0 = lim * Math.min(1, p * 1.05), cut = tok0 >= lim - 1;
    if (oa > 0) {
      x.globalAlpha = oa; x.fillStyle = cut ? '#E0705A' : C.soft; x.fillRect(bx, by, bw * Math.min(1, tok0 / lim), bh);
      text(x, cut ? 'hit the ' + fmt(lim) + '-token limit: cut off' : fmt(Math.round(tok0)) + ' tokens', bx, by - 12, 20, cut ? '#F08C76' : C.soft, { mono: true });
    }
    if (na > 0) {
      var tok1 = L.edited_tokens * sm((e - 0.5) / 0.4);
      x.globalAlpha = na; x.fillStyle = C.acc; x.fillRect(bx, by, bw * tok1 / lim, bh);
      text(x, (e >= 0.9 ? 'stopped on its own: ' : '') + fmt(Math.round(tok1)) + ' tokens', bx, by - 12, 20, C.acc, { mono: true });
    }
    x.globalAlpha = 1;
    x.fillStyle = C.ink; x.fillRect(bx + bw - 2, by - 6, 2, bh + 12);
    x.restore();
  }

  // ------------------------------------------------------------ shot: where the edit lives
  // A strip of the model's 24 layers with 15 and 19 lit, a zoom box down to layer 15,
  // drawn from the real weights: grey = the weights, amber = the change. r 0..1 reveals.
  function where(x, R, D, r) {
    var n = 24, top = R.y + 30, cw = R.w / n, ch = 34;
    x.save();
    text(x, 'THE MODEL: ' + n + ' LAYERS', R.x, top - 10, 20, C.soft, { mono: true, weight: 500 });
    for (var i = 0; i < n; i++) {
      var hot = i === 15 || i === 19;
      x.fillStyle = hot ? mixA(C.edit, sm(r * 3)) : '#2A322D';
      x.fillRect(R.x + i * cw + 1.5, top, cw - 3, ch);
    }
    x.globalAlpha = sm(r * 3);
    text(x, '15', R.x + 15.5 * cw, top + ch + 26, 20, C.edit, { mono: true, weight: 500, align: 'center' });
    text(x, '19', R.x + 19.5 * cw, top + ch + 26, 20, C.edit, { mono: true, weight: 500, align: 'center' });
    // zoom box
    var k = sm(r * 2.5 - 0.5);
    var mw = R.w, mh = mw * 256 / 896, mx = R.x, my = top + ch + 74;
    x.globalAlpha = k;
    x.strokeStyle = 'rgba(94,208,192,0.55)'; x.lineWidth = 1.5;
    x.beginPath(); x.moveTo(R.x + 15 * cw, top + ch); x.lineTo(mx, my); x.moveTo(R.x + 16 * cw, top + ch); x.lineTo(mx + mw, my); x.stroke();
    x.globalAlpha = k * 0.9; x.imageSmoothingEnabled = true;
    x.drawImage(D.baseTex, mx, my, mw, mh);
    x.globalAlpha = 1;
    var sweep = sm(r * 2 - 0.9);
    if (sweep > 0) {
      x.save(); x.beginPath(); x.rect(mx, my, mw * sweep, mh); x.clip();
      x.fillStyle = 'rgba(10,12,11,0.45)'; x.fillRect(mx, my, mw, mh);
      var et = editTint(D, 0); x.drawImage(et, mx, my, mw, mh); x.drawImage(et, mx, my, mw, mh);
      x.restore();
    }
    x.strokeStyle = C.line; x.lineWidth = 1; x.globalAlpha = k; x.strokeRect(mx + 0.5, my + 0.5, mw - 1, mh - 1);
    text(x, 'LAYER 15, ' + fmt(D.m.overview.shape[0]) + ' × ' + fmt(D.m.overview.shape[1]) + ' NUMBERS', mx, my + mh + 30, 20, C.soft, { mono: true, weight: 500 });
    x.globalAlpha = sm(sweep * 2 - 1);
    x.fillStyle = C.edit; x.fillRect(mx, my + mh + 50, 14, 14);
    text(x, 'changed by the edit', mx + 22, my + mh + 64, 20, C.ink, { weight: 500 });
    x.fillStyle = '#7E8A82'; x.fillRect(mx + 230, my + mh + 50, 14, 14);
    text(x, 'untouched', mx + 252, my + mh + 64, 20, C.soft);
    x.restore();
  }
  function mixA(hex, t) {
    var a = [0x2A, 0x32, 0x2D], b = [parseInt(hex.slice(1, 3), 16), parseInt(hex.slice(3, 5), 16), parseInt(hex.slice(5, 7), 16)];
    return 'rgb(' + a.map(function (v, i) { return Math.round(lerp(v, b[i], t)); }).join(',') + ')';
  }

  // ------------------------------------------------------------ shot: the answers drain
  // 100 questions, one square each, amber = right. Right answers sit at the bottom like a
  // level. Every square is one real question and keeps its identity: when precision drops,
  // answers that turned wrong flash and go grey; answers that turned right sink into the level.
  // Order inside each state is fixed (pattern across 16/8/4-bit, then question order), which
  // keeps motion to the squares whose answer changed.
  function drainLayout(D) {
    if (D._drain) return D._drain;
    var q = LEVEL.map(function (lv) { return D.m.answers['edited-' + lv].q; });
    var n = q[0].length, rank = ['111', '110', '101', '100', '011', '010', '001', '000'];
    var pat = [], order = [];
    for (var i = 0; i < n; i++) {
      pat.push(q.map(function (s) { return s[i] === 'c' ? 1 : 0; }));
      order.push(i);
    }
    order.sort(function (a, b) {
      return rank.indexOf(pat[a].join('')) - rank.indexOf(pat[b].join('')) || a - b;
    });
    var slot = [0, 1, 2].map(function (L) {
      var s = new Array(n), k = 0;
      order.forEach(function (i) { if (pat[i][L]) s[i] = k++; });
      order.forEach(function (i) { if (!pat[i][L]) s[i] = k++; });
      return s;
    });
    var right = [0, 1, 2].map(function (L) { return pat.filter(function (p) { return p[L]; }).length; });
    [0, 1, 2].forEach(function (L) {
      if (right[L] !== D.m.answers['edited-' + LEVEL[L]].correct) throw new Error('drain grid disagrees with manifest');
    });
    return (D._drain = { n: n, pat: pat, slot: slot, right: right });
  }
  // Where square i sits at precision L, inside R. Shared by drain() and anything that flies into a square.
  function cellRect(D, R, i, L) {
    var G = drainLayout(D), cols = 10, gap = Math.max(2, Math.min(6, R.w * 0.016)), cell = (R.w - gap * (cols - 1)) / cols;
    var s = G.slot[L][i], r = Math.floor(s / cols), c = s % cols;
    return { x: R.x + c * (cell + gap), y: R.y + R.h - cell - r * (cell + gap), w: cell, h: cell, c: c, r: r };
  }
  // q: precision as a float 0..2 (in between = the move).
  // o.pop(i, col, row) -> 0..1: how far square i has appeared (scale and fade, for the build-up).
  // o.mark: index of one square to outline; o.markA its outline strength.
  function drain(x, R, D, q, o) {
    o = o || {};
    var G = drainLayout(D), cols = 10, gap = Math.max(2, Math.min(6, R.w * 0.016)), cell = (R.w - gap * (cols - 1)) / cols;
    var L0 = Math.floor(Math.min(q, 1.999)), t = q - L0, L1 = Math.min(2, L0 + 1);
    var mv = sm((t - 0.35) / 0.65), turn = sm(t / 0.3);   // first change colour, then move
    x.save();
    // draw still squares first, then moving wrong ones, then moving right ones on top:
    // the eye follows amber settling into the level
    var idx = [];
    for (var j = 0; j < G.n; j++) idx.push(j);
    var rankOf = function (i) { return G.slot[L0][i] === G.slot[L1][i] ? 0 : (G.pat[i][L1] ? 2 : 1); };
    idx.sort(function (a, b) { return rankOf(a) - rankOf(b) || a - b; });
    for (var ii = 0; ii < G.n; ii++) {
      var i = idx[ii];
      var r = Math.floor(G.slot[L0][i] / cols), c = G.slot[L0][i] % cols;
      var r1 = Math.floor(G.slot[L1][i] / cols), c1 = G.slot[L1][i] % cols;
      var cx = R.x + lerp(c, c1, mv) * (cell + gap), cy = R.y + R.h - cell - lerp(r, r1, mv) * (cell + gap);
      var was = G.pat[i][L0], now = G.pat[i][L1], on = lerp(was, now, turn);
      var pk = o.pop ? o.pop(i, c, r) : 1;
      if (pk <= 0) continue;
      var sz = cell * Math.min(pk, 1.25), ox = (cell - sz) / 2;
      x.globalAlpha = clamp01(pk * 2);
      x.fillStyle = mixHex(C.wrong, C.acc, on);
      x.fillRect(cx + ox, cy + ox, sz, sz);
      x.globalAlpha = 1;
      if (i === o.mark && o.markA > 0) {
        x.globalAlpha = o.markA; x.strokeStyle = C.ink; x.lineWidth = 2;
        x.strokeRect(cx + ox - 3, cy + ox - 3, sz + 6, sz + 6); x.globalAlpha = 1;
      }
      if (was !== now && t > 0 && t < 1) {
        var f = Math.sin(Math.PI * clamp01(t / 0.55));
        x.globalAlpha = f; x.strokeStyle = C.flash; x.lineWidth = 3;
        x.strokeRect(cx - 2.5, cy - 2.5, cell + 5, cell + 5); x.globalAlpha = 1;
      }
    }
    x.restore();
    return G;
  }
  function mixHex(a, b, t) {
    var p = function (h) { return [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)]; };
    var A = p(a), B = p(b);
    return 'rgb(' + A.map(function (v, i) { return Math.round(lerp(v, B[i], t)); }).join(',') + ')';
  }

  // The edit texture recoloured to C.edit (cached per precision).
  function editTint(D, L) {
    D._tint = D._tint || [];
    if (!D._tint[L]) {
      var src = D.editTex[L][0], c = document.createElement('canvas'); c.width = src.width; c.height = src.height;
      var t = c.getContext('2d'); t.drawImage(src, 0, 0); t.globalCompositeOperation = 'source-in'; t.fillStyle = C.edit; t.fillRect(0, 0, c.width, c.height);
      D._tint[L] = c;
    }
    return D._tint[L];
  }

  // ------------------------------------------------------------ the edit as stripes, at any precision
  // Layer 15 from the real weight files: grey = the weights, amber = what the edit changed.
  // lv 0..2: a fractional level is a rounding pass in progress, a bright bar sweeping left to right
  // with the newly stored version behind it. sweep 0..1 reveals the whole panel left to right.
  function stripes(x, R, D, lv, sweep) {
    if (sweep == null) sweep = 1;
    if (sweep <= 0) return;
    var a = Math.floor(Math.min(lv, 1.999)), f = clamp01(lv - a), b = Math.min(2, a + 1);
    var layer = function (L, X0, X1) {
      if (X1 <= X0) return;
      x.save(); x.beginPath(); x.rect(X0, R.y, X1 - X0, R.h); x.clip();
      x.drawImage(D.baseTex, R.x, R.y, R.w, R.h);
      x.fillStyle = 'rgba(10,12,11,0.5)'; x.fillRect(R.x, R.y, R.w, R.h);
      var et = editTint(D, L); x.drawImage(et, R.x, R.y, R.w, R.h); x.drawImage(et, R.x, R.y, R.w, R.h);
      x.restore();
    };
    x.save(); x.imageSmoothingEnabled = true;
    var right = R.x + R.w * sweep, bar = R.x + R.w * f;
    layer(b, R.x, Math.min(bar, right));
    layer(a, Math.max(R.x, bar), right);
    if (f > 0 && f < 1) {
      var gr = x.createLinearGradient(bar - 18, 0, bar + 2, 0);
      gr.addColorStop(0, 'rgba(230,234,228,0)'); gr.addColorStop(1, 'rgba(230,234,228,0.55)');
      x.fillStyle = gr; x.fillRect(bar - 18, R.y, 20, R.h);
      x.fillStyle = C.ink; x.fillRect(bar - 1, R.y - 4, 2, R.h + 8);
    }
    x.restore();
    x.strokeStyle = C.line; x.lineWidth = 1; x.strokeRect(R.x + 0.5, R.y + 0.5, R.w - 1, R.h - 1);
  }
  // The precision knob: three stops, the lit pill slides. pq 0..2. Returns the pill rects.
  function knob(x, X, Y, H, pq, size) {
    size = size || 20;
    font(x, size, 500, true);
    var pad = size * 0.7, gapK = 8, rects = [], cx = X;
    NAME.forEach(function (n) { var w = x.measureText(n).width + pad * 2; rects.push({ x: cx, y: Y, w: w, h: H }); cx += w + gapK; });
    var a = Math.floor(Math.min(pq, 1.999)), f = clamp01(pq - a), A = rects[a], B = rects[Math.min(2, a + 1)];
    var lit = { x: lerp(A.x, B.x, f), w: lerp(A.w, B.w, f) };
    rects.forEach(function (r) { rrect(x, r.x, r.y, r.w, r.h, H / 2); x.strokeStyle = C.line; x.lineWidth = 1.5; x.stroke(); });
    rrect(x, lit.x, Y, lit.w, H, H / 2); x.fillStyle = C.ink; x.fill();
    rects.forEach(function (r, i) {
      var on = 1 - Math.min(1, Math.abs(pq - i));
      text(x, NAME[i], r.x + r.w / 2, Y + H / 2 + size * 0.36, size, mixHex(C.soft, '#14110A', on), { mono: true, weight: 500, align: 'center' });
    });
    return rects;
  }

  g.WeightShots = { C: C, loop: loop, where: where, drain: drain, drainLayout: drainLayout,
    cellRect: cellRect, stripes: stripes, editTint: editTint, knob: knob, rrect: rrect, mixHex: mixHex, plain: plain,
    text: text, sm: sm, clamp01: clamp01, lerp: lerp, fmt: fmt, NAME: NAME, LEVEL: LEVEL };
})(window);
