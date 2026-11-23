/* scope.js: the instrument. Draws the real weights in docs/data onto one canvas.
   Shared by docs/index.html (driven by scroll) and media/video.html (driven by time).

   Nothing here invents a number. Every value drawn comes from docs/data, which
   src/site_data.py builds from the model files and results/. The story position
   u (0..1) decides what is shown; the precision q (0 = 16-bit, 1 = 8-bit,
   2 = 4-bit) decides which stored version of the weights is shown. Between two
   precision levels the drawing animates the snap; every number printed belongs
   to the nearest real level, never to an in-between one. */
(function (g) {
  'use strict';

  var clamp01 = function (x) { return x < 0 ? 0 : x > 1 ? 1 : x; };
  var smooth = function (x) { x = clamp01(x); return x * x * (3 - 2 * x); };
  var lerp = function (a, b, t) { return a + (b - a) * t; };
  var seg = function (u, a, b) { return clamp01((u - a) / (b - a)); };
  var LEVEL = ['BF16', 'Q8_0', 'Q4_K_M'];
  var LEVEL_NAME = ['16-bit', '8-bit', '4-bit'];
  var TILE = 256;           // a wafer square is 256 x 256 = 65,536 weights; world unit = one weight
  var COLS = 128;           // wafer width in squares
  var L15 = 'model.language_model.layers.15.mlp.down_proj.weight';
  var L19 = 'model.language_model.layers.19.mlp.down_proj.weight';

  // ---------------------------------------------------------------- phases
  // One table drives the page, the map and the video. a..b is the stretch of
  // story the phase owns; rest is where its picture is settled (used by the map
  // buttons and by reduced motion, which shows settled frames only).
  var PHASES = [
    { id: 'model',   a: 0.000, b: 0.070, rest: 0.030, label: 'The model' },
    { id: 'edit',    a: 0.070, b: 0.170, rest: 0.155, label: 'The edit' },
    { id: 'layer',   a: 0.170, b: 0.310, rest: 0.300, label: 'Layer 15' },
    { id: 'cells',   a: 0.310, b: 0.362, rest: 0.350, label: 'Single weights' },
    { id: 'row',     a: 0.362, b: 0.425, rest: 0.410, label: 'One row of 32' },
    { id: 'r8',      a: 0.425, b: 0.465, rest: 0.450, label: '8-bit' },
    { id: 'r4',      a: 0.465, b: 0.515, rest: 0.485, label: '4-bit' },
    { id: 'survive', a: 0.515, b: 0.560, rest: 0.548, label: 'The edit survives' },
    { id: 'quiet',   a: 0.560, b: 0.600, rest: 0.585, label: '' },
    { id: 't16',     a: 0.600, b: 0.675, rest: 0.650, label: 'The answers' },
    { id: 't8',      a: 0.675, b: 0.765, rest: 0.730, label: '' },
    { id: 't4',      a: 0.765, b: 0.870, rest: 0.830, label: '' },
    { id: 'close',   a: 0.870, b: 1.001, rest: 0.960, label: 'Verdict' }
  ];
  function phaseAt(u) {
    for (var i = 0; i < PHASES.length; i++) if (u < PHASES[i].b) return PHASES[i];
    return PHASES[PHASES.length - 1];
  }

  // Precision set by the story. Snaps are short so most of the scroll sits on a real level.
  function storyQ(u) {
    if (u < 0.575) return smooth(seg(u, 0.428, 0.440)) + smooth(seg(u, 0.468, 0.480));
    return smooth(seg(u, 0.682, 0.722)) + smooth(seg(u, 0.772, 0.812));
  }

  // ---------------------------------------------------------------- loading
  function fetchOk(url) {
    return fetch(url).then(function (r) { if (!r.ok) throw new Error(url + ': HTTP ' + r.status); return r; });
  }
  function loadGray(url) {
    return new Promise(function (res, rej) {
      var im = new Image();
      im.onload = function () {
        var c = document.createElement('canvas'); c.width = im.width; c.height = im.height;
        var x = c.getContext('2d', { willReadFrequently: true });
        x.drawImage(im, 0, 0);
        var d = x.getImageData(0, 0, c.width, c.height).data, v = new Uint8Array(c.width * c.height);
        for (var i = 0; i < v.length; i++) v[i] = d[i * 4];
        res({ w: c.width, h: c.height, v: v });
      };
      im.onerror = function () { rej(new Error('image failed: ' + url)); };
      im.src = url;
    });
  }

  function load(base) {
    return fetchOk(base + 'manifest.json').then(function (r) { return r.json(); }).then(function (m) {
      var f = m.overview.files;
      return Promise.all([loadGray(base + f.base), loadGray(base + f['16']), loadGray(base + f['8']), loadGray(base + f['4']),
        fetchOk(base + m.crop.file).then(function (r) { return r.arrayBuffer(); })])
        .then(function (all) { return build(m, all[0], [all[1], all[2], all[3]], new Float32Array(all[4])); });
    });
  }

  // ---------------------------------------------------------------- data -> drawables
  function canvasOf(w, h) { var c = document.createElement('canvas'); c.width = w; c.height = h; return c; }

  function build(m, baseImg, editImgs, crop) {
    var need = 6 * m.crop.rows * m.crop.cols;
    if (crop.length !== need) throw new Error('crop.bin has ' + crop.length + ' values, expected ' + need);
    if (baseImg.w !== 3584 / m.overview.pool || baseImg.h !== 1024 / m.overview.pool) throw new Error('overview size');
    var D = { m: m, crop: crop };

    // Wafer: every tensor in the model as a run of squares, area to scale.
    // Groups that hold at least one square start on a new row; inside a group
    // the largest tensors come first. This puts layer 15's down_proj on whole
    // squares, 56 of them, in one row.
    var groups = [], cur = null;
    m.model.map.forEach(function (t) {
      if (!cur || cur.name !== t.group) { cur = { name: t.group, items: [] }; groups.push(cur); }
      cur.items.push(t);
    });
    var pos = 0, runs = [];
    groups.forEach(function (gr, gi) {
      gr.items.sort(function (a, b) { return b.count - a.count || (a.name < b.name ? -1 : 1); });
      var glen = gr.items.reduce(function (s, t) { return s + t.count / 65536; }, 0);
      if (glen >= 1) pos = Math.ceil(pos / COLS - 1e-9) * COLS;
      gr.items.forEach(function (t) {
        runs.push({ name: t.name, group: gr.name, gi: gi, start: pos, len: t.count / 65536 });
        pos += t.count / 65536;
      });
    });
    var tiles = [];
    runs.forEach(function (r, ri) {
      var a = r.start, b = r.start + r.len;
      while (a < b - 1e-9) {
        var i = Math.floor(a + 1e-9), e = Math.min(b, i + 1);
        tiles.push({ x: (i % COLS) + (a - i), y: Math.floor(i / COLS), w: e - a, ri: ri, gi: r.gi });
        a = e;
      }
    });
    var find = function (name) { for (var i = 0; i < runs.length; i++) if (runs[i].name === name) return i; throw new Error('no run ' + name); };
    var i15 = find(L15), i19 = find(L19), r15 = runs[i15];
    if (r15.len !== 56 || r15.start % 1 !== 0 || (r15.start % COLS) + 56 > COLS) throw new Error('layer 15 run is not 56 whole squares in one row');
    var waferRows = Math.ceil(pos / COLS);
    var rx0 = (r15.start % COLS) * TILE, ry0 = Math.floor(r15.start / COLS) * TILE;
    var cx = rx0 + 28 * TILE, cy = ry0 + TILE / 2;
    D.wafer = { tiles: tiles, runs: runs, rows: waferRows, i15: i15, i19: i19, w: COLS * TILE, h: waferRows * TILE,
      run: { x: rx0, y: ry0 }, row19: Math.floor(runs[i19].start / COLS) };
    D.T = { x: cx - 1792, y: cy - 512 };   // the tensor, 3,584 x 1,024 weights, centred on its run

    // Tensor textures: base (size of weights, grey) and the edit (size of the change, accent).
    var ink = [230, 234, 228], acc = [245, 184, 65];
    var bc = canvasOf(baseImg.w, baseImg.h), bx = bc.getContext('2d'), bd = bx.createImageData(baseImg.w, baseImg.h);
    for (var k = 0; k < baseImg.v.length; k++) {
      var t = baseImg.v[k] / 255, l = 0.06 + 0.36 * t;
      bd.data[k * 4] = ink[0] * l; bd.data[k * 4 + 1] = ink[1] * l; bd.data[k * 4 + 2] = ink[2] * l; bd.data[k * 4 + 3] = 255;
    }
    bx.putImageData(bd, 0, 0);
    D.baseTex = bc;
    // Edit textures with max-pooled mip levels, so a thin edited column never
    // disappears when the tensor is drawn smaller than its pooled image.
    D.editTex = editImgs.map(function (img) {
      var levels = [], w = img.w, h = img.h, mag = new Float32Array(w * h);
      for (var i = 0; i < mag.length; i++) mag[i] = Math.abs(img.v[i] - 128) / 127;
      for (var lv = 0; lv < 4; lv++) {
        var c = canvasOf(w, h), x = c.getContext('2d'), d = x.createImageData(w, h);
        for (var j = 0; j < mag.length; j++) {
          d.data[j * 4] = acc[0]; d.data[j * 4 + 1] = acc[1]; d.data[j * 4 + 2] = acc[2];
          d.data[j * 4 + 3] = Math.round(255 * Math.min(1, Math.pow(mag[j], 0.75)));
        }
        x.putImageData(d, 0, 0);
        levels.push(c);
        var w2 = w >> 1, h2 = h >> 1, m2 = new Float32Array(w2 * h2);
        for (var yy = 0; yy < h2; yy++) for (var xx = 0; xx < w2; xx++) {
          var o = 2 * yy * w + 2 * xx;
          m2[yy * w2 + xx] = Math.max(mag[o], mag[o + 1], mag[o + w], mag[o + w + 1]);
        }
        mag = m2; w = w2; h = h2;
      }
      return levels;
    });

    // Block of 32 and its rounding grids, plus a fact computed from it.
    var B = m.block;
    D.block = B;
    D.blockIdx = B.edited_col - B.col0;
    var distinct = function (arr, skip) {
      var s = {}; arr.forEach(function (v, i) { if (i !== skip) s[v.toFixed(9)] = 1; }); return Object.keys(s).length;
    };
    D.distinct4 = { base: distinct(B.values.base.Q4_K_M, D.blockIdx), edited: distinct(B.values.edited.Q4_K_M, D.blockIdx) };
    D.levels = [null,
      (function () { var d = B.q8_step.edited, out = []; for (var q = -128; q <= 127; q++) out.push(d * q); return out; })(),
      (function () { var s = B.q4_step.edited, o = B.q4_offset.edited, out = []; for (var q = 0; q <= 15; q++) out.push(s * q - o); return out; })()];

    // Answers, in one fixed question order.
    D.ans = ['BF16', 'Q8_0', 'Q4_K_M'].map(function (lv) { return m.answers['edited-' + lv]; });
    D.base = ['BF16', 'Q8_0', 'Q4_K_M'].map(function (lv) { return m.answers['base-' + lv]; });
    return D;
  }

  // ---------------------------------------------------------------- camera
  // A view is a world-space box fitted into the frame. Zooms keep a fixed point
  // on screen (the centre moves in step with the size), so a dive reads as one
  // continuous fall rather than a pan plus a zoom.
  function views(D) {
    var W = D.wafer, T = D.T, B = D.block, cr = D.m.crop;
    var pad = 2 * TILE;
    return {
      wafer: { x: -pad, y: -pad, w: W.w + 2 * pad, h: W.h + 2 * pad },
      layers: { x: -TILE, y: W.run.y - 10 * TILE, w: W.w + 2 * TILE, h: (W.row19 - W.run.y / TILE + 20) * TILE },
      run: { x: W.run.x - 3 * TILE, y: W.run.y - 5 * TILE, w: 62 * TILE, h: 11 * TILE },
      tensor: { x: T.x - 90, y: T.y - 90, w: 3584 + 180, h: 1024 + 180 },
      crop: { x: T.x + cr.col0 - 6, y: T.y + cr.row0 - 6, w: cr.cols + 12, h: cr.rows + 12 },
      row: { x: T.x + B.col0 - 3, y: T.y + B.row - 5, w: 38, h: 11 }
    };
  }
  function mix(a, b, t) {
    if (t <= 0) return a; if (t >= 1) return b;
    var la = Math.log(a.w), lb = Math.log(b.w), w = Math.exp(lerp(la, lb, t));
    var h = a.h * (w / a.w) * Math.pow((b.h / b.w) / (a.h / a.w), t);
    var f = Math.abs(lb - la) > 0.08 ? (a.w - w) / (a.w - b.w) : t;
    var acx = a.x + a.w / 2, acy = a.y + a.h / 2, bcx = b.x + b.w / 2, bcy = b.y + b.h / 2;
    var cx = lerp(acx, bcx, f), cy = lerp(acy, bcy, f);
    return { x: cx - w / 2, y: cy - h / 2, w: w, h: h };
  }
  function drift(v, k) { // slow push-in while a picture holds, so held frames still breathe
    var s = 1 - 0.04 * k, w = v.w * s, h = v.h * s;
    return { x: v.x + (v.w - w) / 2, y: v.y + (v.h - h) / 2, w: w, h: h };
  }
  function camera(D, u) {
    var V = D.views || (D.views = views(D));
    var e = function (a, b) { return smooth(seg(u, a, b)); };
    if (u < 0.17) return mix(drift(V.wafer, seg(u, 0, 0.09)), drift(V.layers, seg(u, 0.15, 0.17)), e(0.085, 0.15));
    if (u < 0.205) return mix(drift(V.layers, seg(u, 0.15, 0.17)), V.run, e(0.17, 0.205));
    if (u < 0.31) return mix(V.run, drift(V.tensor, seg(u, 0.26, 0.31)), e(0.222, 0.25));
    if (u < 0.362) return mix(drift(V.tensor, 1), drift(V.crop, seg(u, 0.345, 0.362)), e(0.312, 0.345));
    if (u < 0.49) return mix(drift(V.crop, 1), V.row, e(0.364, 0.395));
    if (u < 0.515) return mix(V.row, V.crop, e(0.49, 0.512));
    return mix(V.crop, drift(V.tensor, seg(u, 0.54, 0.56)), e(0.515, 0.538));
  }

  // ---------------------------------------------------------------- state
  // Which sweep of the answer grid the story is in: from one level to the next.
  function sweepAt(u) {
    if (u < 0.6) return null;
    if (u < 0.682) return { from: -1, to: 0, p: seg(u, 0.606, 0.668) };
    if (u < 0.772) return { from: 0, to: 1, p: seg(u, 0.684, 0.758) };
    return { from: 1, to: 2, p: seg(u, 0.774, 0.852) };
  }
  function stateAt(D, u, qOverride, manual) {
    var q = qOverride == null ? storyQ(u) : qOverride;
    var e = function (a, b) { return smooth(seg(u, a, b)); };
    var worldOut = e(0.556, 0.574);                  // the silence: the weights leave
    var st = {
      u: u, q: q, phase: phaseAt(u).id, cam: camera(D, u),
      wafer: (1 - e(0.222, 0.226)) * (1 - worldOut),
      isolate: e(0.205, 0.222),
      hl: e(0.08, 0.115),
      fold: e(0.222, 0.25),
      tensor: e(0.25, 0.262) * (1 - worldOut),
      edit: e(0.266, 0.29) * (1 - worldOut),
      cells: e(0.322, 0.345) * (1 - e(0.53, 0.545)),
      trace: e(0.382, 0.4) * (1 - e(0.487, 0.5)),
      twist: e(0.6, 0.625),
      dim: 0.55 * e(0.875, 0.91),
      sweep: manual ? null : sweepAt(u)
    };
    return st;
  }

  // ---------------------------------------------------------------- drawing
  function Scope(canvas, D, opts) {
    this.c = canvas; this.x = canvas.getContext('2d'); this.D = D; this.o = opts || {};
    this.fontMono = this.o.fontMono || '"Geist Mono", ui-monospace, monospace';
    this.fontText = this.o.fontText || 'Geist, system-ui, sans-serif';
    this.col = {
      canvas: '#0A0C0B', ink: '#E6EAE4', soft: '#93A097', faint: 'rgba(230,234,228,0.10)',
      grid: 'rgba(147,160,151,0.13)', acc: '#F5B841', accSoft: 'rgba(245,184,65,0.22)'
    };
  }

  // frame: {x, y, w, h} in CSS px inside the canvas; W, H CSS size; dpr pixel ratio
  Scope.prototype.draw = function (st, frame, W, H, dpr, ui) {
    var x = this.x, D = this.D, c = this.col;
    this.ui = ui || 1;
    if (this.c.width !== Math.round(W * dpr) || this.c.height !== Math.round(H * dpr)) {
      this.c.width = Math.round(W * dpr); this.c.height = Math.round(H * dpr);
    }
    x.setTransform(dpr, 0, 0, dpr, 0, 0);
    x.clearRect(0, 0, W, H);
    this.graticule(frame);

    // world transform: fit the camera box into the frame
    var v = st.cam, s = Math.min(frame.w / v.w, frame.h / v.h);
    var ox = frame.x + frame.w / 2 - (v.x + v.w / 2) * s, oy = frame.y + frame.h / 2 - (v.y + v.h / 2) * s;
    this.s = s; this.ox = ox; this.oy = oy; this.dpr = dpr; this.frame = frame;
    var vis = { x0: (frame.x - ox) / s, y0: (frame.y - oy) / s, x1: (frame.x + frame.w - ox) / s, y1: (frame.y + frame.h - oy) / s };

    x.save();
    x.beginPath(); x.rect(frame.x, frame.y, frame.w, frame.h); x.clip();
    var worldA = 1 - st.dim;
    if (st.wafer > 0.002) this.drawWafer(st, vis, worldA);
    if ((st.fold > 0.002 || st.isolate > 0.002) && st.tensor < 0.999 && st.u < 0.3) this.drawFold(st, worldA);
    if (st.tensor > 0.002) this.drawTensor(st, worldA * st.tensor * (1 - 0.82 * st.cells));
    if (st.cells > 0.002) this.drawCells(st, vis, worldA);
    x.restore();
    if (st.trace > 0.002) this.drawTrace(st, frame);
    if (st.twist > 0.002) this.drawTwist(st, frame);
  };

  Scope.prototype.graticule = function (f) {
    var x = this.x, c = this.col, nx = 10, ny = Math.max(4, Math.round(10 * f.h / f.w));
    x.save();
    x.strokeStyle = c.grid; x.lineWidth = 1;
    x.beginPath();
    for (var i = 0; i <= nx; i++) { var gx = Math.round(f.x + f.w * i / nx) + 0.5; x.moveTo(gx, f.y); x.lineTo(gx, f.y + f.h); }
    for (var j = 0; j <= ny; j++) { var gy = Math.round(f.y + f.h * j / ny) + 0.5; x.moveTo(f.x, gy); x.lineTo(f.x + f.w, gy); }
    x.stroke();
    // minor ticks on the centre axes, as on a scope
    x.beginPath();
    var mx = Math.round(f.x + f.w / 2) + 0.5, my = Math.round(f.y + f.h / 2) + 0.5;
    for (var k = 0; k <= nx * 5; k++) { var tx = Math.round(f.x + f.w * k / (nx * 5)) + 0.5; x.moveTo(tx, my - 3); x.lineTo(tx, my + 3); }
    for (var l = 0; l <= ny * 5; l++) { var ty = Math.round(f.y + f.h * l / (ny * 5)) + 0.5; x.moveTo(mx - 3, ty); x.lineTo(mx + 3, ty); }
    x.stroke();
    x.restore();
  };

  Scope.prototype.toScreen = function (wx, wy) { return [this.ox + wx * this.s, this.oy + wy * this.s]; };

  Scope.prototype.drawWafer = function (st, vis, worldA) {
    var x = this.x, W = this.D.wafer, s = this.s, c = this.col;
    var gap = Math.min(0.14 * TILE, Math.max(0.5 / s, 0.06 * TILE));
    var shades = ['#1B211E', '#232A26', '#2B332E'];
    x.save();
    x.globalAlpha = st.wafer * worldA;
    for (var i = 0; i < W.tiles.length; i++) {
      var t = W.tiles[i], wx = t.x * TILE, wy = t.y * TILE;
      if (wx > vis.x1 || wx + t.w * TILE < vis.x0 || wy > vis.y1 || wy + TILE < vis.y0) continue;
      var edited = t.ri === W.i15 || t.ri === W.i19;
      if (t.ri === W.i15 && (st.fold > 0 || st.isolate > 0)) continue;   // layer 15's squares are drawn by drawFold
      x.globalAlpha = st.wafer * worldA * (1 - 0.94 * (st.isolate || 0));
      var sx = this.ox + wx * s, sy = this.oy + wy * s, sw = Math.max(t.w * TILE * s - gap * s, 0.6), sh = (TILE - gap) * s;
      x.fillStyle = edited && st.hl > 0 ? mixHex(shades[t.ri % 2], c.acc, st.hl) : shades[(t.ri % 2) + (t.gi % 2)];
      x.fillRect(sx, sy, sw, sh);
    }
    // name the two edited tensors
    if (st.hl > 0.05) {
      var self = this, ui = this.ui;
      [[W.i15, 'LAYER 15 MLP.DOWN_PROJ'], [W.i19, 'LAYER 19 MLP.DOWN_PROJ']].forEach(function (r) {
        var run = W.runs[r[0]], rxs = (run.start % COLS) * TILE, ry = Math.floor(run.start / COLS) * TILE;
        var p = self.toScreen(rxs, ry - 1.2 * TILE);
        x.globalAlpha = st.wafer * worldA * st.hl * (1 - (st.isolate || 0));
        x.fillStyle = 'rgba(10,12,11,0.85)';
        x.font = '500 ' + (12.5 * ui) + 'px ' + self.fontMono;
        var tw = x.measureText(r[1]).width;
        x.fillRect(p[0] - 6 * ui, p[1] - 13 * ui, tw + 12 * ui, 18 * ui);
        self.label(r[1], p[0], p[1], 12.5 * ui, c.acc, '500');
      });
    }
    x.restore();
  };

  Scope.prototype.drawFold = function (st, worldA) {
    var x = this.x, D = this.D, W = D.wafer, T = D.T, s = this.s, c = this.col;
    x.save();
    x.globalAlpha = worldA * (1 - st.tensor);
    x.imageSmoothingEnabled = true;
    for (var i = 0; i < 56; i++) {
      var k = smooth(clamp01(st.fold * 1.6 - (i % 14) * 0.03 - Math.floor(i / 14) * 0.06));
      var fx = W.run.x + i * TILE, fy = W.run.y, tx = T.x + (i % 14) * TILE, ty = T.y + Math.floor(i / 14) * TILE;
      var gap = lerp(0.1, 0, k) * TILE;
      var sx = this.ox + lerp(fx, tx, k) * s, sy = this.oy + lerp(fy, ty, k) * s, sz = (TILE - gap) * s;
      x.globalAlpha = worldA * (1 - st.tensor);
      x.fillStyle = mixHex('#1B211E', c.acc, st.hl * (1 - k));
      if (k === 0) { x.fillRect(sx, sy, sz, sz); continue; }
      x.fillRect(sx, sy, sz, sz);
      // the real patch of the tensor this square becomes (256 x 256 weights)
      x.globalAlpha = worldA * (1 - st.tensor) * k;
      x.drawImage(D.baseTex, (i % 14) * 64, Math.floor(i / 14) * 64, 64, 64, sx, sy, sz, sz);
    }
    x.restore();
  };

  Scope.prototype.editMip = function (q, screenW) {
    var lv = 0, w = 896;
    while (lv < 3 && w > screenW * 1.05) { lv++; w >>= 1; }
    return lv;
  };

  Scope.prototype.drawTensor = function (st, a) {
    var x = this.x, D = this.D, T = D.T, s = this.s;
    var sx = this.ox + T.x * s, sy = this.oy + T.y * s, sw = 3584 * s, sh = 1024 * s;
    x.save();
    x.globalAlpha = a;
    x.imageSmoothingEnabled = sw < 896;
    x.drawImage(D.baseTex, sx, sy, sw, sh);
    if (st.edit > 0.002) {
      var lv = this.editMip(st.q, sw);
      x.imageSmoothingEnabled = false;
      this.blendLevels(st.q, function (k, wgt) {
        x.globalAlpha = a * st.edit * wgt;
        x.drawImage(D.editTex[k][lv], sx, sy, sw, sh);
      });
    }
    // axes: what the two sides of the matrix are
    var lab = a * (1 - st.cells) * smooth(seg(sw, 300, 500));
    if (lab > 0.01 && sw < this.frame.w * 1.2) {
      x.globalAlpha = lab;
      var ui = this.ui, L = Math.round(st.q);
      this.label('3,584 COLUMNS', sx, sy + sh + 18 * ui, 12.5 * ui, this.col.soft);
      this.label('1,024 ROWS', sx, sy - 10 * ui, 12.5 * ui, this.col.soft);
      if (st.edit > 0.5) {
        var e15 = this.D.m.edit['15'].cosine;
        var t = L === 0 ? 'CHANGE AT 16-BIT: THE TRUE EDIT' : 'CHANGE AS STORED AT ' + LEVEL_NAME[L].toUpperCase() +
          ': COSINE ' + (L === 1 ? e15.Q8_0.toFixed(4) : e15.Q4_K_M.toFixed(2)) + ' WITH THE TRUE EDIT';
        x.font = '500 ' + (12.5 * ui) + 'px ' + this.fontMono;
        var tw2 = x.measureText(t).width, narrow = tw2 + 110 * ui > sw;
        this.label(t, narrow ? sx : sx + sw - tw2, sy - (narrow ? 26 : 10) * ui, 12.5 * ui, this.col.acc, '500');
      }
    }
    x.restore();
  };

  // Calls fn(level, weight) for the one or two real levels around q.
  Scope.prototype.blendLevels = function (q, fn) {
    var lo = Math.floor(q), f = q - lo;
    if (f < 0.002 || lo >= 2) { fn(Math.min(2, Math.round(q)), 1); return; }
    fn(lo, 1 - f); fn(lo + 1, f);
  };

  Scope.prototype.drawCells = function (st, vis, worldA) {
    var x = this.x, D = this.D, cr = D.m.crop, T = D.T, s = this.s, c = this.col, A = D.crop;
    var R = cr.rows, C = cr.cols, n = R * C, gap = Math.min(0.12, 1 / s);
    var off = function (k) { return k * n; };   // order: base16, edited16, base8, edited8, base4, edited4
    x.save();
    var lo = Math.floor(st.q), f = st.q - lo, hi = Math.min(2, lo + 1);
    for (var r = 0; r < R; r++) {
      var wy = T.y + cr.row0 + r;
      if (wy + 1 < vis.y0 || wy > vis.y1) continue;
      for (var k = 0; k < C; k++) {
        var wx = T.x + cr.col0 + k;
        if (wx + 1 < vis.x0 || wx > vis.x1) continue;
        var i = r * C + k;
        var e0 = A[off(2 * lo + 1) + i], b0 = A[off(2 * lo) + i];
        var e1 = A[off(2 * hi + 1) + i], b1 = A[off(2 * hi) + i];
        var w = lerp(e0, e1, f), d = lerp(e0 - b0, e1 - b1, f);
        var sx = this.ox + wx * s, sy = this.oy + wy * s, sz = (1 - gap) * s;
        x.globalAlpha = st.cells * worldA;
        var g = 0.08 + 0.6 * Math.min(1, Math.abs(w) / 0.03);
        x.fillStyle = 'rgb(' + Math.round(230 * g) + ',' + Math.round(234 * g) + ',' + Math.round(228 * g) + ')';
        x.fillRect(sx, sy, sz, sz);
        var m = Math.min(1, Math.abs(d) / D.m.overview.edit_scale);
        if (m > 0.004) {
          x.globalAlpha = st.cells * worldA * Math.pow(m, 0.75);
          x.fillStyle = c.acc;
          x.fillRect(sx, sy, sz, sz);
        }
      }
    }
    // outline the row of 32 the next step zooms into
    var B = D.block, bx = this.ox + (T.x + B.col0) * s, by = this.oy + (T.y + B.row) * s;
    x.globalAlpha = st.cells * worldA * 0.9;
    x.strokeStyle = c.ink; x.lineWidth = 1;
    x.strokeRect(Math.round(bx) - 1.5, Math.round(by) - 1.5, 32 * s + 2, s + 2);
    x.restore();
  };

  // One row of 32 weights as a trace on a symmetric value axis, with the
  // rounding grid of the edited block at the current precision.
  Scope.prototype.drawTrace = function (st, f) {
    var x = this.x, D = this.D, B = D.block, c = this.col, ui = this.ui;
    var a = st.trace;
    var padL = 64 * ui, padR = 20 * ui, padT = 40 * ui, padB = 46 * ui;
    var px = f.x + padL, pw = f.w - padL - padR, py = f.y + padT, ph = f.h - padT - padB;
    var YM = 0.12, y0 = py + ph / 2, ys = (ph / 2) / YM;
    var colX = function (i) { return px + pw * (i + 0.5) / 32; };
    x.save();
    x.globalAlpha = a;
    x.fillStyle = 'rgba(10,12,11,0.94)';
    x.fillRect(f.x, f.y, f.w, f.h);
    this.graticule(f);
    // rounding grid
    var lo = Math.floor(st.q), fr = st.q - lo;
    var gridA = function (lv) { return lv === lo ? 1 - fr : lv === lo + 1 ? fr : 0; };
    [1, 2].forEach(function (lv) {
      var ga = gridA(lv); if (ga < 0.01) return;
      x.globalAlpha = a * ga * (lv === 1 ? 0.30 : 0.55);
      x.strokeStyle = c.soft; x.lineWidth = 1;
      x.beginPath();
      D.levels[lv].forEach(function (val) {
        if (Math.abs(val) > YM) return;
        var yy = Math.round(y0 - val * ys) + 0.5; x.moveTo(px, yy); x.lineTo(px + pw, yy);
      });
      x.stroke();
    });
    x.globalAlpha = a;
    // axis
    x.strokeStyle = 'rgba(230,234,228,0.5)';
    x.beginPath(); x.moveTo(px, Math.round(y0) + 0.5); x.lineTo(px + pw, Math.round(y0) + 0.5); x.stroke();
    x.font = (12.5 * ui) + 'px ' + this.fontMono; x.fillStyle = c.soft; x.textAlign = 'right'; x.textBaseline = 'middle';
    [-0.1, -0.05, 0, 0.05, 0.1].forEach(function (t) { x.fillText((t > 0 ? '+' : t < 0 ? '−' : '') + Math.abs(t).toFixed(2), px - 8 * ui, y0 - t * ys); });
    // original weights (before the edit) as hollow marks
    var vb = B.values.base.BF16, ve = B.values.edited;
    var val = function (i) {
      var a0 = ve[LEVEL[Math.min(2, lo)]][i], a1 = ve[LEVEL[Math.min(2, lo + 1)]][i];
      return lerp(a0, a1, smooth(fr));
    };
    for (var i = 0; i < 32; i++) {
      var cx = colX(i), isE = i === D.blockIdx, v = val(i);
      x.strokeStyle = isE ? c.acc : 'rgba(230,234,228,0.75)';
      x.lineWidth = isE ? 2.5 * ui : 1.25 * ui;
      x.beginPath(); x.moveTo(cx, y0); x.lineTo(cx, y0 - v * ys); x.stroke();
      x.fillStyle = isE ? c.acc : c.ink;
      x.beginPath(); x.arc(cx, y0 - v * ys, (isE ? 4.5 : 3) * ui, 0, 6.2832); x.fill();
      if (isE) {
        x.strokeStyle = c.soft; x.lineWidth = 1.25 * ui;
        x.beginPath(); x.arc(cx, y0 - vb[i] * ys, 4.5 * ui, 0, 6.2832); x.stroke();
      }
    }
    // labels
    var L = Math.round(st.q), lvName = LEVEL_NAME[L];
    x.textAlign = 'left'; x.textBaseline = 'alphabetic'; x.fillStyle = c.soft;
    x.font = (12.5 * ui) + 'px ' + this.fontMono;
    x.fillText('LAYER 15 DOWN_PROJ  ROW ' + B.row + '  COLUMNS ' + fmt(B.col0) + ' TO ' + fmt(B.col0 + 31), px, f.y + 22 * ui);
    var grid = L === 0 ? 'GRID: BFLOAT16, 65,536 POSSIBLE VALUES' : L === 1
      ? 'GRID: 256 LEVELS, STEP ' + B.q8_step.edited.toFixed(5) + ', ONE SCALE PER 32 WEIGHTS'
      : 'GRID: 16 LEVELS, STEP ' + B.q4_step.edited.toFixed(4) + ' (Q4_K)';
    x.fillText(grid, px, f.y + f.h - 18 * ui);
    // the edited column's reading
    var ix = colX(D.blockIdx), vv = ve[LEVEL[L]][D.blockIdx];
    x.fillStyle = c.acc; x.font = '500 ' + (13 * ui) + 'px ' + this.fontMono;
    var t1 = 'EDITED COLUMN ' + fmt(B.edited_col) + ': ' + signed(vv, 4), t2 = '(WAS ' + signed(vb[D.blockIdx], 4) + ')';
    if (ix + 12 * ui + x.measureText(t1 + '  ' + t2).width < f.x + f.w - 8) x.fillText(t1 + '  ' + t2, ix + 12 * ui, y0 - vv * ys + 4 * ui);
    else { x.fillText(t1, ix + 12 * ui, y0 - vv * ys - 4 * ui); x.fillText(t2, ix + 12 * ui, y0 - vv * ys + 11 * ui); }
    x.restore();
  };

  // The twist: two readings side by side (stacked on a phone). Left: the edit as
  // stored at this precision next to the edit as made, and how alike they are.
  // Right: the 100 answers as a level that drains (shots.js), one symbol, amber = right.
  Scope.prototype.drawTwist = function (st, f) {
    var x = this.x, D = this.D, c = this.col, a = st.twist * (1 - st.dim * 0.8), S = g.WeightShots;
    if (!S) throw new Error('shots.js must load before the twist is drawn');
    var L = Math.min(2, Math.floor(st.q + 0.75));
    var stack = f.w < 620, gap = stack ? 18 : 28;
    var E, G;
    if (stack) { var eh = Math.min(f.h * 0.4, 190); E = { x: f.x, y: f.y, w: f.w, h: eh }; G = { x: f.x, y: f.y + eh + gap, w: f.w, h: f.h - eh - gap }; }
    else { E = { x: f.x, y: f.y, w: f.w * 0.46 - gap / 2, h: f.h }; G = { x: f.x + f.w * 0.46 + gap / 2, y: f.y, w: f.w * 0.54 - gap / 2, h: f.h }; }
    x.save();
    x.globalAlpha = a;
    x.fillStyle = 'rgba(10,12,11,0.94)';
    x.fillRect(f.x - 2, f.y - 2, f.w + 4, f.h + 4);
    this.twistEdit(E, st, L, a, stack);
    this.twistAnswers(G, st, L, a, stack);
    x.restore();
  };

  Scope.prototype.twistEdit = function (P, st, L, a, stack) {
    var x = this.x, D = this.D, c = this.col, S = g.WeightShots;
    var e15 = D.m.edit['15'].cosine, sim = L === 0 ? '1' : L === 1 ? e15.Q8_0.toFixed(4) : e15.Q4_K_M.toFixed(2);
    var t = 14, big = stack ? 26 : Math.min(40, P.w / 9);
    x.globalAlpha = a;
    S.text(x, 'THE EDIT, LAYER 15', P.x, P.y + t, 13, c.soft, { mono: true, weight: 500 });
    var iw = stack ? P.w * 0.58 : P.w, ih = iw * 256 / 896, ys = P.y + t + 14;
    if (stack) ih = Math.min(ih, (P.h - t - 14 - 22) / 2 - 18);
    if (stack) iw = ih * 896 / 256;
    var rows = [[0, 'as made, 16-bit'], [L, L === 0 ? 'as stored, 16-bit' : 'as stored, ' + LEVEL_NAME[L]]];
    font13(x);
    var labW = Math.max(x.measureText(rows[0][1]).width, x.measureText(rows[1][1]).width);
    if (stack) { iw = Math.max(iw, Math.min(labW, P.w * 0.5)); ih = iw * 256 / 896; }
    for (var r = 0; r < 2; r++) {
      var y = ys + r * (ih + 26) + 4;
      x.globalAlpha = a;
      S.text(x, rows[r][1], P.x, y + 4, 13, r ? c.ink : c.soft, { weight: r ? 500 : 400 });
      var iy = y + 10;
      x.globalAlpha = a * 0.5; x.imageSmoothingEnabled = true;
      x.drawImage(D.baseTex, P.x, iy, iw, ih);
      var lv = this.editMip(0, iw);
      x.imageSmoothingEnabled = iw < 600;
      if (r === 0) { x.globalAlpha = a; x.drawImage(D.editTex[0][lv], P.x, iy, iw, ih); }
      else this.blendLevels(st.q, function (k, wgt) { x.globalAlpha = a * wgt; x.drawImage(D.editTex[k][lv], P.x, iy, iw, ih); });
    }
    x.globalAlpha = a;
    var nx = stack ? P.x + Math.max(iw, labW) + 18 : P.x, ny = stack ? ys + 30 : ys + 2 * (ih + 26) + 30 + big * 0.5;
    S.text(x, L === 0 ? 'reference' : 'same pattern', nx, ny, big * 0.8, L === 0 ? c.soft : c.acc, { weight: 500 });
    S.text(x, sim, nx, ny + big * 0.95 + 4, big, c.ink, { mono: true, weight: 500 });
    S.text(x, 'cosine, 1 = identical', nx, ny + big * 0.95 + 26, 13, c.soft);
    if (!stack) {
      var ly = ny + big * 0.95 + 70;
      S.text(x, 'Looping (what the edit fixes)', P.x, ly, 14, c.soft);
      S.text(x, D.ans[L].looping + '%', P.x, ly + 34, 28, c.ink, { weight: 500 });
      S.text(x, 'original model: ' + D.base[L].looping + '%', P.x + 80, ly + 32, 14, c.soft);
    }
  };

  function font13(x) { x.font = '500 13px "Geist", system-ui, sans-serif'; }

  Scope.prototype.twistAnswers = function (P, st, L, a, stack) {
    var x = this.x, D = this.D, c = this.col, S = g.WeightShots;
    x.globalAlpha = a;
    S.text(x, 'THE ANSWERS, 100 QUESTIONS', P.x, P.y + 14, 13, c.soft, { mono: true, weight: 500 });
    var numW = stack ? Math.max(96, P.w * 0.3) : Math.max(120, P.w * 0.28);
    var side = Math.min(P.w - numW - 14, P.h - 14 - 16 - 34);
    var R = { x: P.x, y: P.y + 30, w: side, h: side };
    var G = S.drain(x, R, D, st.q);
    var nx = R.x + side + 16, big = Math.min(88, Math.max(44, side * 0.26));
    S.text(x, String(G.right[L]), nx, R.y + big * 0.86, big, c.acc, { weight: 500 });
    S.text(x, 'right of 100', nx, R.y + big * 0.86 + 22, 14, c.ink, { weight: 500 });
    for (var k = 0; k < 3; k++) {
      var y = R.y + big * 0.86 + 58 + k * 24, cur = k === L;
      x.globalAlpha = a * (k <= L ? 1 : 0.4);
      S.text(x, LEVEL_NAME[k], nx, y, 14, cur ? c.ink : c.soft, { mono: true, weight: cur ? 500 : 400 });
      S.text(x, String(G.right[k]), nx + 78, y, 14, cur ? c.acc : c.soft, { mono: true, weight: 500, align: 'right' });
      if (cur) { x.fillStyle = c.acc; x.fillRect(nx - 9, y - 12, 3, 15); }
    }
    x.globalAlpha = a;
    var ly = R.y + side + 26;
    x.fillStyle = c.acc; x.fillRect(R.x, ly - 12, 13, 13);
    S.text(x, 'right', R.x + 19, ly, 14, c.ink);
    x.fillStyle = S.C.wrong; x.fillRect(R.x + 72, ly - 12, 13, 13);
    S.text(x, 'wrong', R.x + 91, ly, 14, c.soft);
  };

  Scope.prototype.label = function (txt, px, py, size, color, weight) {
    var x = this.x;
    x.font = (weight || '400') + ' ' + size + 'px ' + this.fontMono;
    x.fillStyle = color; x.textAlign = 'left'; x.textBaseline = 'alphabetic';
    x.fillText(txt, px, py);
  };

  // ---------------------------------------------------------------- captions
  // What one unit on screen means right now. Shown under the scope.
  function field(D, st) {
    var p = st.phase;
    if (st.twist > 0.5) return 'Squares: one per question, amber = right. Stripes: layer 15\'s edit, 4 x 4 weights per pixel.';
    if (st.trace > 0.5) return 'One row of 32 neighbouring weights, values on a symmetric axis. Hollow mark: the original weight before the edit.';
    if (st.cells > 0.5) return 'One cell = one weight. Window: rows ' + D.m.crop.row0 + ' to ' + (D.m.crop.row0 + 63) + ', columns ' + fmt(D.m.crop.col0) + ' to ' + fmt(D.m.crop.col0 + 255) + ' of layer 15. Amber = size of the change, 0 to 0.02.';
    if (st.tensor > 0.5) return 'Layer 15 down_proj, 1,024 x 3,584 weights. One pixel of the data = 4 x 4 weights (largest change kept). Amber = size of the change, 0 to 0.02 and above; grey = size of the weights.';
    if (st.fold > 0.05) return 'Each square = 65,536 weights. The 56 squares of layer 15 down_proj fold into its real shape.';
    return 'Each square = 65,536 weights. All 488 tensors, grouped by layer, area to scale.';
  }

  function fmt(n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ','); }
  function signed(v, d) { return (v < 0 ? '−' : '+') + Math.abs(v).toFixed(d); }
  function mixHex(a, b, t) {
    var pa = [parseInt(a.slice(1, 3), 16), parseInt(a.slice(3, 5), 16), parseInt(a.slice(5, 7), 16)];
    var pb = [parseInt(b.slice(1, 3), 16), parseInt(b.slice(3, 5), 16), parseInt(b.slice(5, 7), 16)];
    return 'rgb(' + Math.round(lerp(pa[0], pb[0], t)) + ',' + Math.round(lerp(pa[1], pb[1], t)) + ',' + Math.round(lerp(pa[2], pb[2], t)) + ')';
  }

  g.WeightScope = { load: load, Scope: Scope, stateAt: stateAt, storyQ: storyQ, PHASES: PHASES, phaseAt: phaseAt,
    field: field, LEVEL_NAME: LEVEL_NAME, fmt: fmt, signed: signed };
})(window);
