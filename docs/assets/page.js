/* page.js: the four figures. Each is a canvas drawn from docs/data (data.js) with the shared
   drawing in shots.js. Figures animate when they first come into view, or when their controls
   are used; nothing is tied to scroll. Every number in the text is checked against the data. */
(function () {
  'use strict';
  var WD = window.WeightData, S = window.WeightShots, C = S.C, sm = S.sm, lerp = S.lerp, clamp01 = S.clamp01;
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var io = function (u) { u = clamp01(u); return u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2; };
  var MIN_VW = 492;   // figures are laid out at least this wide, then scaled down, so labels stay >= ~13 px on a phone

  // ---------------------------------------------------------------- numbers in the text
  function checkNumbers(m) {
    [].forEach.call(document.querySelectorAll('[data-n]'), function (el) {
      var v = el.dataset.n.split('.').reduce(function (o, k) { return o == null ? o : o[k]; }, m);
      if (v == null) throw new Error('no value in manifest for ' + el.dataset.n);
      var want = typeof v !== 'number' ? String(v)
        : el.dataset.pct ? (v * 100).toFixed(+el.dataset.pct) + '%'
        : el.dataset.round ? v.toFixed(+el.dataset.round)
        : Number.isInteger(v) ? WD.fmt(v) : String(v);
      if (el.textContent.trim() !== want) throw new Error('page text disagrees with manifest: ' + el.dataset.n + ' "' + el.textContent + '" vs "' + want + '"');
    });
  }

  // ---------------------------------------------------------------- a figure canvas
  // draw(x, VW) works in virtual px; height(VW) gives the virtual height.
  function Fig(fig, height, draw) {
    var canvas = fig.querySelector('canvas'), x = canvas.getContext('2d'), self = this;
    this.fig = fig; this.canvas = canvas; this.s = 1; this.VW = MIN_VW;
    this.render = function () {
      var w = canvas.clientWidth; if (!w) return;
      var VW = Math.max(MIN_VW, w), s = w / VW, VH = height(VW), dpr = Math.min(2, devicePixelRatio || 1);
      self.s = s; self.VW = VW;
      var bw = Math.round(w * dpr), bh = Math.round(VH * s * dpr);
      if (canvas.width !== bw || canvas.height !== bh) { canvas.width = bw; canvas.height = bh; canvas.style.height = (VH * s) + 'px'; }
      x.setTransform(dpr * s, 0, 0, dpr * s, 0, 0);
      x.fillStyle = C.panel; x.fillRect(0, 0, VW, VH);
      draw(x, VW, VH);
    };
    new ResizeObserver(function () { self.render(); }).observe(canvas);
  }
  // Runs fn(t) every frame for dur seconds (or once at the end, with reduced motion).
  function tween(dur, fn, done) {
    if (reduce) { fn(1); if (done) done(); return { stop: function () {} }; }
    var t0 = performance.now(), live = true;
    (function step(now) {
      if (!live) return;
      var t = Math.min(1, (now - t0) / 1000 / dur);
      fn(t);
      if (t < 1) requestAnimationFrame(step); else if (done) done();
    })(t0);
    return { stop: function () { live = false; } };
  }
  function onFirstView(el, fn) {
    var ob = new IntersectionObserver(function (es) { if (es[0].isIntersecting) { ob.disconnect(); fn(); } }, { threshold: 0.45 });
    ob.observe(el);
  }
  // A row of radio buttons with arrow-key support.
  function radios(group, attr, onPick) {
    var bs = [].slice.call(group.querySelectorAll('[' + attr + ']'));
    function set(v) { bs.forEach(function (b) { var on = +b.getAttribute(attr) === v; b.setAttribute('aria-checked', String(on)); b.tabIndex = on ? 0 : -1; }); }
    bs.forEach(function (b, i) {
      b.addEventListener('click', function () { set(+b.getAttribute(attr)); onPick(+b.getAttribute(attr)); });
      b.addEventListener('keydown', function (e) {
        var d = e.key === 'ArrowRight' || e.key === 'ArrowDown' ? 1 : e.key === 'ArrowLeft' || e.key === 'ArrowUp' ? -1 : 0;
        if (!d) return;
        e.preventDefault();
        var n = bs[(i + d + bs.length) % bs.length]; n.focus(); n.click();
      });
    });
    set(0);
  }

  // ---------------------------------------------------------------- figure 1: one answer
  function figLoop(D) {
    var el = document.getElementById('fig-loop'), st = { p: reduce ? 1 : 0.18, e: 0 }, run = null;
    var f = new Fig(el, function () { return 362; }, function (x, VW) { S.loop(x, { x: 16, y: 16, w: VW - 32, h: 330 }, D, st.p, st.e); });
    var btns = [].slice.call(el.querySelectorAll('[data-e]'));
    function press(e) { btns.forEach(function (b) { b.setAttribute('aria-pressed', String(+b.dataset.e === e)); }); }
    function playLoop() {
      if (run) run.stop();
      st.p = 0.18; st.e = 0; press(0);
      run = tween(4.2, function (t) { st.p = 0.18 + 0.82 * t; f.render(); });
    }
    function toE(target) {
      if (run) run.stop();
      if (target === 1) st.p = 1;
      var from = st.e;
      press(target);
      run = tween(1.3, function (t) { st.e = lerp(from, target, sm(t)); f.render(); });
    }
    btns.forEach(function (b) { b.addEventListener('click', function () { toE(+b.dataset.e); }); });
    el.querySelector('[data-replay]').addEventListener('click', playLoop);
    onFirstView(el, playLoop);
  }

  // ---------------------------------------------------------------- figure 2: where the edit lives
  function figWhere(D) {
    var el = document.getElementById('fig-where'), r = reduce ? 1 : 0;
    var f = new Fig(el, function (VW) { return 16 + 138 + (VW - 32) * 256 / 896 + 92; },
      function (x, VW) { S.where(x, { x: 16, y: 16, w: VW - 32, h: 0 }, D, r); });
    onFirstView(el, function () { tween(2.4, function (t) { r = t; f.render(); }); });
  }

  // ---------------------------------------------------------------- figure 3: rounding, one block of 32
  function figRound(D) {
    var el = document.getElementById('fig-round'), B = D.m.block, idx = D.blockIdx;
    var vals = WD.LEVEL.map(function (lv) { return B.values.edited[lv]; }), before = B.values.base.BF16[idx];
    var pq = 0, run = null, TOP = 0.05, BOT = -0.13;
    var f = new Fig(el, function () { return 360; }, function (x, VW, VH) {
      var x0 = 70, x1 = VW - 20, y0 = 92, y1 = VH - 30;
      var Y = function (v) { return y0 + (TOP - v) / (TOP - BOT) * (y1 - y0); };
      var a = Math.floor(Math.min(pq, 1.999)), t = pq - a, L = Math.round(pq);
      // allowed values: 8-bit's are so close they read as a haze; 4-bit's 16 are drawn as lines
      x.save(); x.beginPath(); x.rect(x0 - 8, y0, x1 - x0 + 16, y1 - y0); x.clip();
      var a8 = Math.max(0, 1 - Math.abs(pq - 1)) * 0.22, a4 = clamp01(pq - 1);
      if (a8 > 0) { x.globalAlpha = a8; x.strokeStyle = C.ink; x.lineWidth = 0.6; var st8 = B.q8_step.edited;
        for (var v = Math.ceil(BOT / st8) * st8; v <= TOP; v += st8) { x.beginPath(); x.moveTo(x0 - 8, Y(v)); x.lineTo(x1 + 8, Y(v)); x.stroke(); } }
      if (a4 > 0) { x.globalAlpha = a4 * 0.5; x.strokeStyle = C.ink; x.lineWidth = 1;
        D.grid4.forEach(function (v) { x.beginPath(); x.moveTo(x0 - 8, Y(v)); x.lineTo(x1 + 8, Y(v)); x.stroke(); }); }
      x.restore(); x.globalAlpha = 1;
      // zero line and scale
      x.strokeStyle = 'rgba(230,234,228,0.35)'; x.lineWidth = 1; x.beginPath(); x.moveTo(x0 - 8, Y(0)); x.lineTo(x1 + 8, Y(0)); x.stroke();
      S.text(x, '0', x0 - 16, Y(0) + 6, 18, C.soft, { mono: true, align: 'right' });
      S.text(x, '-0.1', x0 - 16, Y(-0.1) + 6, 18, C.soft, { mono: true, align: 'right' });
      x.strokeStyle = 'rgba(230,234,228,0.12)'; x.beginPath(); x.moveTo(x0 - 8, Y(-0.1)); x.lineTo(x0, Y(-0.1)); x.stroke();
      // the 32 numbers
      var pitch = (x1 - x0) / 32, bw = Math.max(3, pitch * 0.42);
      for (var i = 0; i < 32; i++) {
        var v2 = lerp(vals[a][i], vals[Math.min(2, a + 1)][i], io(t)), cx = x0 + (i + 0.5) * pitch, ed = i === idx;
        x.fillStyle = ed ? C.edit : '#7E8A82';
        var ya = Y(0), yb = Y(v2);
        x.fillRect(cx - bw / 2, Math.min(ya, yb), bw, Math.max(1.5, Math.abs(yb - ya)));
        x.beginPath(); x.arc(cx, yb, ed ? 5 : 3.2, 0, 7); x.fill();
      }
      var ex = x0 + (idx + 0.5) * pitch;
      x.strokeStyle = C.edit; x.lineWidth = 2; x.beginPath(); x.arc(ex, Y(before), 7, 0, 7); x.stroke();
      S.text(x, 'before the edit', ex + 14, Y(before) + 6, 18, C.edit);
      // the count that matters
      var n = D.distinct.edited[L];
      S.text(x, String(n), 20, 54, 44, C.ink, { weight: 500 });
      var w = x.measureText(String(n)).width;
      S.text(x, 'different values among the 31 small', 20 + w + 14, 36, 19, C.soft);
      S.text(x, 'neighbours, at ' + S.NAME[L], 20 + w + 14, 60, 19, C.soft);
    });
    radios(el.querySelector('.knob'), 'data-q', function (q) {
      if (run) run.stop();
      var from = pq;
      run = tween(0.8 * Math.max(1, Math.abs(q - from)), function (t) { pq = lerp(from, q, t); f.render(); });
    });
  }

  // ---------------------------------------------------------------- figure 4: the edit and the answers
  function figTest(D) {
    var el = document.getElementById('fig-test'), tip = el.querySelector('.tip'), m = D.m, A = m.answers, G = S.drainLayout(D);
    var st = { lv: 0, q: 0 }, run = null, hover = -1, geo = null;
    var cos = m.edit['15'].cosine, LV = WD.LEVEL;
    var STATUS = [['16-bit: the edit as made', 'the reference: similarity 1']
      , ['8-bit: the same lines', 'similarity to the original edit: ' + cos.Q8_0.toFixed(4) + ' of 1']
      , ['4-bit: the same lines, plus rounding noise', 'similarity to the original edit: ' + cos.Q4_K_M.toFixed(2) + ' of 1']];
    function lay(VW) {
      var sw = VW - 32, sh = sw / 3.5, gs = Math.min(330, Math.round(sw * 0.54));
      var gy = 16 + sh + 104;
      return { SR: { x: 16, y: 16, w: sw, h: sh }, st: 16 + sh + 30, GR: { x: 16, y: gy, w: gs, h: gs }, nx: 16 + gs + 30, ny: gy + 70, VH: gy + gs + 22 };
    }
    var f = new Fig(el, function (VW) { return lay(VW).VH; }, function (x, VW) {
      var g = lay(VW); geo = g;
      S.stripes(x, g.SR, D, st.lv, 1);
      // status: the nearest stored version, fading through the scan
      var Ls = Math.round(st.lv), al = clamp01(1 - 2.2 * Math.abs(st.lv - Ls));
      x.globalAlpha = al;
      S.text(x, STATUS[Ls][0], 16, g.st, 21, Ls ? C.ink : C.soft, { weight: 500 });
      if (STATUS[Ls][1]) S.text(x, STATUS[Ls][1], 16, g.st + 26, 19, C.soft);
      S.text(x, 'looping: ' + A['edited-' + LV[Ls]].looping + '%, original model ' + A['base-' + LV[Ls]].looping + '%', 16, g.st + 52, 19, C.edit, { weight: 500 });
      x.globalAlpha = 1;
      // the answers
      S.drain(x, g.GR, D, st.q, { mark: hover, markA: hover >= 0 ? 1 : 0 });
      var q = st.q, q0 = Math.floor(Math.min(q, 1.999)), tq = sm((q - q0) / 0.3), L = Math.round(q);
      var shown = Math.round(lerp(G.right[q0], G.right[Math.min(2, q0 + 1)], tq));
      S.text(x, String(shown), g.nx, g.ny, 80, C.acc, { weight: 500 });
      S.text(x, 'right of 100', g.nx + 2, g.ny + 30, 21, C.ink, { weight: 500 });
      for (var j = 0; j < 3; j++) {
        var y = g.ny + 64 + j * 26, cur = j === L;
        S.text(x, S.NAME[j], g.nx + 2, y, 20, cur ? C.ink : C.soft, { mono: true, weight: cur ? 500 : 400 });
        S.text(x, String(G.right[j]), g.nx + 124, y, 20, cur ? C.acc : C.soft, { mono: true, weight: 500, align: 'right' });
        if (cur) { x.fillStyle = C.acc; x.fillRect(g.nx - 10, y - 16, 3, 20); }
      }
      // the original model's score as a water line on the same grid
      var base = LV.map(function (lv) { return A['base-' + lv].correct; });
      var bn = lerp(base[q0], base[Math.min(2, q0 + 1)], tq);
      var c0 = S.cellRect(D, g.GR, 0, 0), pitch = c0.w + (g.GR.w - 10 * c0.w) / 9;
      var ly = g.GR.y + g.GR.h - (bn / 10) * pitch + (pitch - c0.w) / 2, listEnd = g.ny + 64 + 52;
      var ty = Math.max(ly + 7, listEnd + 30);
      x.strokeStyle = C.ink; x.lineWidth = 2; x.setLineDash([7, 5]);
      x.beginPath(); x.moveTo(g.GR.x - 6, ly); x.lineTo(g.GR.x + g.GR.w + 8, ly); x.stroke(); x.setLineDash([]);
      if (ty > ly + 9) { x.lineWidth = 1; x.beginPath(); x.moveTo(g.GR.x + g.GR.w + 8, ly); x.lineTo(g.nx - 4, ty - 7); x.stroke(); }
      S.text(x, 'original model: ' + Math.round(bn), g.nx, ty, 19, C.ink);
    });

    // precision: one step at a time; each step rounds the edit first, then drains the answers
    function go(target) {
      if (run) run.stop();
      hide();
      var from = Math.round(st.q), steps = [];
      for (var k = from; k !== target; k += target > from ? 1 : -1) steps.push([k, k + (target > from ? 1 : -1)]);
      if (!steps.length) { st.lv = st.q = target; f.render(); return; }
      var i = 0;
      (function next() {
        if (i >= steps.length) return;
        var a = steps[i][0], b = steps[i][1]; i++;
        run = tween(2.1, function (t) {
          st.lv = lerp(a, b, io(t * 2.1 / 0.6));
          st.q = lerp(a, b, clamp01((t * 2.1 - 0.8) / 1.3));
          f.render();
        }, next);
      })();
    }
    radios(el.querySelector('.knob'), 'data-q', go);

    // point at a square: its question at every precision, for both models
    var WORD = { c: '<span class="r">right</span>', l: '<span class="l">hit the limit</span>', w: '<span class="w">wrong answer</span>' };
    function hide() { if (hover !== -1) { hover = -1; f.render(); } tip.hidden = true; }
    function at(e) {
      if (!geo || st.q % 1) return -1;
      var r = f.canvas.getBoundingClientRect(), vx = (e.clientX - r.left) / f.s, vy = (e.clientY - r.top) / f.s, L = Math.round(st.q);
      for (var i = 0; i < G.n; i++) {
        var c = S.cellRect(D, geo.GR, i, L);
        if (vx >= c.x - 1 && vx <= c.x + c.w + 1 && vy >= c.y - 1 && vy <= c.y + c.h + 1) return i;
      }
      return -1;
    }
    function show(e) {
      var i = at(e);
      if (i < 0) { hide(); return; }
      if (i !== hover) {
        hover = i; f.render();
        var row = function (who) {
          return LV.map(function (lv, k) { return S.NAME[k] + ' ' + WORD[A[who + '-' + lv].q[i]]; }).join('<br>');
        };
        tip.innerHTML = '<b>Edited model</b><br>' + row('edited') + '<br><br><b>Original model</b><br>' + row('base')
          + (i === m.loop.index ? '<br><br>The question in Figure 1.' : '');
      }
      tip.hidden = false;
      var fr = el.getBoundingClientRect(), tx = e.clientX - fr.left + 16, ty = e.clientY - fr.top + 16;
      tip.style.left = Math.min(tx, fr.width - tip.offsetWidth - 4) + 'px';
      tip.style.top = (ty + tip.offsetHeight > fr.height ? Math.max(4, e.clientY - fr.top - tip.offsetHeight - 12) : ty) + 'px';
    }
    f.canvas.addEventListener('pointermove', show);
    f.canvas.addEventListener('pointerdown', show);
    f.canvas.addEventListener('pointerleave', function (e) { if (e.pointerType === 'mouse') hide(); });
    document.addEventListener('pointerdown', function (e) { if (e.target !== f.canvas) hide(); });
  }

  WD.load('data/').then(function (D) {
    checkNumbers(D.m);
    return document.fonts.ready.then(function () {
      figLoop(D); figWhere(D); figRound(D); figTest(D);
      document.documentElement.dataset.ready = 'true';
    });
  }).catch(function (err) {
    document.documentElement.dataset.ready = 'error';
    var p = document.createElement('p'); p.className = 'noscript'; p.textContent = 'The figures could not load: ' + err.message;
    document.querySelector('article').prepend(p);
    throw err;
  });
})();
