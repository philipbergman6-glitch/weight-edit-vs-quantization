/* data.js: loads docs/data (built by src/site_data.py) into things the figures can draw.
   Shared by docs/index.html and media/video.html. Nothing here invents a number. */
(function (g) {
  'use strict';
  var LEVEL = ['BF16', 'Q8_0', 'Q4_K_M'];

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
      return Promise.all([loadGray(base + f.base), loadGray(base + f['16']), loadGray(base + f['8']), loadGray(base + f['4'])])
        .then(function (all) { return build(m, all[0], [all[1], all[2], all[3]]); });
    });
  }
  function canvasOf(w, h) { var c = document.createElement('canvas'); c.width = w; c.height = h; return c; }

  function build(m, baseImg, editImgs) {
    if (baseImg.w !== 3584 / m.overview.pool || baseImg.h !== 1024 / m.overview.pool) throw new Error('overview size');
    var D = { m: m };
    // Layer 15 as two textures: the weights (grey, by size) and the edit (amber, by size of the change).
    var ink = [230, 234, 228], acc = [245, 184, 65];
    var bc = canvasOf(baseImg.w, baseImg.h), bx = bc.getContext('2d'), bd = bx.createImageData(baseImg.w, baseImg.h);
    for (var k = 0; k < baseImg.v.length; k++) {
      var t = baseImg.v[k] / 255, l = 0.06 + 0.36 * t;
      bd.data[k * 4] = ink[0] * l; bd.data[k * 4 + 1] = ink[1] * l; bd.data[k * 4 + 2] = ink[2] * l; bd.data[k * 4 + 3] = 255;
    }
    bx.putImageData(bd, 0, 0);
    D.baseTex = bc;
    // The edit with max-pooled mip levels, so a thin edited column never vanishes when drawn small.
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
    // One block of 32 neighbouring weights, as stored at each precision, and the 4-bit grid it sits on.
    var B = m.block;
    D.blockIdx = B.edited_col - B.col0;
    var distinct = function (arr, skip) {
      var s = {}; arr.forEach(function (v, i) { if (i !== skip) s[v.toFixed(9)] = 1; }); return Object.keys(s).length;
    };
    D.distinct = {};
    ['base', 'edited'].forEach(function (who) {
      D.distinct[who] = LEVEL.map(function (lv) { return distinct(B.values[who][lv], D.blockIdx); });
    });
    if (D.distinct.edited[2] !== B.distinct_neighbours_q4.edited || D.distinct.base[2] !== B.distinct_neighbours_q4.base)
      throw new Error('block: distinct 4-bit neighbours disagree with the manifest');
    D.grid4 = []; for (var q = 0; q <= 15; q++) D.grid4.push(B.q4_step.edited * q - B.q4_offset.edited);
    return D;
  }

  function fmt(n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ','); }

  g.WeightData = { load: load, fmt: fmt, LEVEL: LEVEL };
})(window);
