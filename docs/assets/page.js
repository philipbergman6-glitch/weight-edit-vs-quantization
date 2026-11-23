/* page.js: wires the instrument (scope.js) to scroll, the map and the knob.
   The engine (scrollcraft.js) owns the pinned stage and the copy cues; this
   file owns the canvas, the knob, and the state the harness reads. */
(function () {
  'use strict';
  var WS = window.WeightScope;
  var api = ScrollCraft.mount(document.body);
  var byId = function (id) { for (var i = 0; i < api.acts.length; i++) if (api.acts[i].el.id === id) return api.acts[i]; throw new Error('no act #' + id); };
  var act = byId('scope');
  var pro = byId('loop');
  var term = pro.el.querySelector('canvas.pro__term');
  var termX = term.getContext('2d');
  var stage = act.stage;
  var canvas = stage.querySelector('canvas.scope');
  var frameEl = stage.querySelector('.frame');
  var fieldEl = stage.querySelector('.field');
  var knob = stage.querySelector('.knob');
  var input = knob.querySelector('input');
  var dial = knob.querySelector('.knob__dial');
  var cap = knob.querySelector('.knob__cap');
  var stops = [].slice.call(knob.querySelectorAll('.knob__stops button'));
  var who = knob.querySelector('.knob__who');
  var mapBtns = [].slice.call(stage.querySelectorAll('.map button'));
  var reduce = ScrollCraft.reduce;
  var KNOB_FROM = 0.4;   // the knob opens when the rounding starts
  var ANGLE = [-60, 0, 60];

  // Scroll position inside the pinned act, for a story position u.
  function yFor(u) {
    var travel = Math.max(act.height - innerHeight, 1);
    return act.top + u * travel;
  }
  function restFor(id) { for (var i = 0; i < WS.PHASES.length; i++) if (WS.PHASES[i].id === id) return WS.PHASES[i].rest; return 0; }

  // Map: jump to the settled picture of a waypoint.
  mapBtns.forEach(function (b) {
    b.addEventListener('click', function () {
      scrollTo({ top: Math.round(yFor(restFor(b.dataset.go))), behavior: reduce ? 'auto' : 'smooth' });
    });
  });
  // The verdict sits on a pinned act, so the engine's focus centring cannot open
  // it. Park the act where the verdict is lit when focus lands inside it.
  stage.querySelector('#verdict').addEventListener('focusin', function () {
    if (act.p < 0.9) scrollTo({ top: Math.round(yFor(restFor('close'))), behavior: 'auto' });
  });
  document.querySelector('.skip').addEventListener('click', function (e) {
    e.preventDefault();
    scrollTo({ top: Math.round(yFor(restFor('close'))), behavior: 'auto' });
    stage.querySelector('#verdict').focus({ preventScroll: true });
  });

  // ---- the knob: the viewer can take the precision away from the scroll
  var manual = null;          // { q, y } while the viewer holds it
  var qShown = 0;
  var knobOn = false;
  function take(q) {
    if (!knobOn) return;
    manual = { q: q, y: scrollY };
  }
  stops.forEach(function (b) { b.addEventListener('click', function () { take(+b.dataset.q); }); });
  input.addEventListener('input', function () { take(+input.value); });
  var drag = null;
  function angleQ(e) {
    var r = dial.getBoundingClientRect();
    var a = Math.atan2(e.clientX - (r.left + r.width / 2), -(e.clientY - (r.top + r.height / 2))) * 180 / Math.PI;
    return a < -30 ? 0 : a > 30 ? 2 : 1;
  }
  dial.addEventListener('pointerdown', function (e) {
    if (!knobOn) return;
    drag = e.pointerId; dial.setPointerCapture(e.pointerId); take(angleQ(e)); e.preventDefault();
  });
  dial.addEventListener('pointermove', function (e) { if (drag === e.pointerId) take(angleQ(e)); });
  dial.addEventListener('pointerup', function (e) { if (drag === e.pointerId) drag = null; });
  dial.addEventListener('pointercancel', function () { drag = null; });

  function setKnob(on, level, byYou) {
    if (on !== knobOn) {
      knobOn = on;
      knob.dataset.on = String(on);
      input.disabled = !on;
      stops.forEach(function (b) { b.disabled = !on; });
      if (!on) manual = null;
    }
    if (+input.value !== level) input.value = String(level);
    input.setAttribute('aria-valuetext', WS.LEVEL_NAME[level]);
    stops.forEach(function (b) { b.setAttribute('aria-pressed', String(+b.dataset.q === level)); });
    cap.setAttribute('transform', 'rotate(' + ANGLE[level] + ' 50 50)');
    who.textContent = !on ? 'opens at the rounding' : byYou ? 'set by you; scroll to hand it back' : 'set by the scroll; turn it';
  }

  // ---- numbers in the copy must match the manifest
  function checkNumbers(m) {
    var bad = [];
    [].forEach.call(document.querySelectorAll('[data-n]'), function (el) {
      var v = el.dataset.n.split('.').reduce(function (o, k) { return o == null ? o : o[k]; }, m);
      if (v == null) { bad.push(el.dataset.n + ' missing'); return; }
      var want = typeof v === 'number'
        ? (el.dataset.round ? v.toFixed(+el.dataset.round) : (Number.isInteger(v) ? WS.fmt(v) : String(v)))
        : String(v);
      if (el.textContent.trim() !== want) bad.push(el.dataset.n + ': page says ' + el.textContent.trim() + ', data says ' + want);
    });
    if (bad.length) console.error('[weight-scope] copy disagrees with docs/data/manifest.json:\n  ' + bad.join('\n  '));
  }

  var D = null, scope = null, uShown = act.p, lastState = '', lastField = '', lastPhase = '';
  function frameBox() {
    var s = stage.getBoundingClientRect(), f = frameEl.getBoundingClientRect();
    return { x: f.left - s.left, y: f.top - s.top, w: f.width, h: f.height, W: s.width, H: s.height };
  }
  function phaseRest(u) { return WS.phaseAt(u).rest; }

  function frame() {
    var target = act.p;
    uShown = reduce ? target : uShown + (target - uShown) * 0.16;
    if (Math.abs(target - uShown) < 0.0002) uShown = target;
    // Reduced motion: no camera travel, only the settled picture of each step.
    var u = reduce ? phaseRest(uShown) : uShown;
    var ph = WS.phaseAt(u);

    var on = u >= KNOB_FROM;
    if (manual && Math.abs(scrollY - manual.y) > innerHeight * 0.35) manual = null;
    if (!on) manual = null;
    var qTarget = manual ? manual.q : WS.storyQ(u);
    if (manual && !reduce) {
      qShown += (qTarget - qShown) * 0.22;
      if (Math.abs(qTarget - qShown) < 0.004) qShown = qTarget;
    } else qShown = reduce ? Math.round(qTarget) : qTarget;
    // Reduced motion during the twist: hold whole levels only.
    var level = Math.max(0, Math.min(2, Math.round(qShown)));
    setKnob(on, level, !!manual);

    if (scope) {
      var st = WS.stateAt(D, u, qShown, !!manual || reduce);
      var b = frameBox();
      var ui = 1;
      scope.draw(st, b, b.W, b.H, Math.min(devicePixelRatio || 1, 2), ui);
      var txt = WS.field(D, st);
      if (txt !== lastField) { fieldEl.textContent = txt; lastField = txt; }
      // What the harness reads: the values that actually paint, rounded.
      var sig = [ph.id, Math.log(st.cam.w).toFixed(3), st.q.toFixed(2), st.wafer.toFixed(2), st.fold.toFixed(2),
        st.tensor.toFixed(2), st.edit.toFixed(2), st.cells.toFixed(2), st.trace.toFixed(2), st.twist.toFixed(2), st.dim.toFixed(2), st.sweep ? st.sweep.to + ':' + st.sweep.p.toFixed(2) : '-'].join('|');
      if (sig !== lastState) { stage.setAttribute('data-sc-verify-state', sig); lastState = sig; }
      var hold = ph.id === 'close' && st.dim > 0.54;
      stage.setAttribute('data-sc-verify-hold', String(hold || (reduce && Math.abs(u - ph.rest) < 1e-6)));
    }
    if (D && window.WeightShots && pro.p > -0.5) drawPrologue();
    if (ph.id !== lastPhase) {
      lastPhase = ph.id;
      mapBtns.forEach(function (bt) {
        var ids = [bt.dataset.go].concat((bt.dataset.also || '').split(' ').filter(Boolean));
        if (ids.indexOf(ph.id) > -1) bt.setAttribute('aria-current', 'step'); else bt.removeAttribute('aria-current');
      });
    }
    requestAnimationFrame(frame);
  }

  // ---- prologue: the real loop, then the edited model's answer
  var proLast = '';
  function drawPrologue() {
    var S = window.WeightShots, r = term.getBoundingClientRect();
    if (r.bottom < 0 || r.top > innerHeight || r.width < 10) return;
    var pp = pro.p, lp = 0.15 + 0.85 * S.clamp01((pp - 0.02) / 0.4), ep = S.clamp01((pp - 0.5) / 0.25);
    if (reduce) { lp = 1; ep = pp < 0.5 ? 0 : 1; }
    var key = [r.width, r.height, lp.toFixed(4), ep.toFixed(4)].join('|');
    if (key === proLast) return;
    proLast = key;
    var dpr = Math.min(devicePixelRatio || 1, 2), W = r.width, H = r.height;
    if (term.width !== Math.round(W * dpr) || term.height !== Math.round(H * dpr)) { term.width = Math.round(W * dpr); term.height = Math.round(H * dpr); }
    var k = Math.min(W / 492, 1.35), vw = W / k, vh = H / k, ph = Math.min(vh, 360);
    termX.setTransform(dpr * k, 0, 0, dpr * k, 0, 0);
    termX.clearRect(0, 0, vw, vh);
    S.loop(termX, { x: 0, y: Math.max(0, (vh - ph) / 2), w: Math.min(vw, 640), h: ph }, D, lp, ep);
    pro.el.querySelector('[data-sc-stage]').setAttribute('data-sc-verify-state', 'loop|' + lp.toFixed(2) + '|' + ep.toFixed(2));
  }

  var fontsReady = document.fonts && document.fonts.load
    ? Promise.all([document.fonts.load('500 12px "Geist Mono"'), document.fonts.load('400 12px "Geist Mono"'), document.fonts.load('500 12px "Geist"'), document.fonts.load('400 12px "Geist"')]).catch(function () {})
    : Promise.resolve();
  Promise.all([WS.load('data/'), fontsReady]).then(function (r) {
    D = r[0];
    checkNumbers(D.m);
    scope = new WS.Scope(canvas, D);
  }).catch(function (e) {
    console.error('[weight-scope] could not load docs/data:', e);
    fieldEl.textContent = 'The weight data did not load, so the scope is empty. Every number is also in the notes.';
  });
  requestAnimationFrame(frame);
})();
