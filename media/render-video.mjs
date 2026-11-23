// Render the post video from media/video.html, frame by frame, then encode with ffmpeg.
//
//   cd media && npm ci && node render-video.mjs
//
// Needs: Google Chrome (or CHROME=/path/to/chrome), ffmpeg on PATH, and docs/data
// built by src/site_data.py. Writes media/post-video.mp4 (1080 x 1350, H.264, no
// audio) and media/post-video-poster.png (the held last frame). Deterministic:
// every frame is drawn by window.renderAt(t) at a fixed time, not recorded live.
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright-core";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "..");
const FPS = 30;
const OUT = path.join(HERE, "post-video.mp4");
const POSTER = path.join(HERE, "post-video-poster.png");
const CHROME = [process.env.CHROME, "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/usr/bin/google-chrome", "/usr/bin/chromium"].find((p) => p && fs.existsSync(p));
if (!CHROME) throw new Error("no Chrome found; set CHROME=/path/to/chrome");
for (const f of ["docs/data/manifest.json", "docs/assets/scope.js", "media/video.html"]) {
  if (!fs.existsSync(path.join(ROOT, f))) throw new Error(`missing ${f}`);
}

// A tiny static server over the repo, so the page loads exactly as it would on Pages.
const TYPES = { ".html": "text/html", ".js": "text/javascript", ".json": "application/json", ".png": "image/png",
  ".woff2": "font/woff2", ".css": "text/css", ".bin": "application/octet-stream" };
const server = http.createServer((req, res) => {
  const file = path.join(ROOT, decodeURIComponent(req.url.split("?")[0]));
  if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) { res.writeHead(404).end(); return; }
  res.writeHead(200, { "Content-Type": TYPES[path.extname(file)] || "application/octet-stream" });
  fs.createReadStream(file).pipe(res);
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const port = server.address().port;

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "post-video-"));
const browser = await chromium.launch({ executablePath: CHROME, headless: true });
const page = await browser.newPage({ viewport: { width: 540, height: 675 }, deviceScaleFactor: 2 });
const errors = [];
page.on("pageerror", (e) => errors.push(String(e)));
page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
await page.goto(`http://127.0.0.1:${port}/media/video.html`, { waitUntil: "load" });
await page.evaluate(() => window.ready);
if (errors.length) throw new Error("page errors:\n" + errors.join("\n"));
const duration = await page.evaluate(() => window.DURATION);
const frames = Math.round(duration * FPS);
for (let i = 0; i < frames; i++) {
  await page.evaluate((t) => window.renderAt(t), i / FPS);
  await page.screenshot({ path: path.join(tmp, `f${String(i).padStart(4, "0")}.png`) });
}
if (errors.length) throw new Error("page errors:\n" + errors.join("\n"));
await browser.close();
server.close();

const ff = spawnSync("ffmpeg", ["-v", "error", "-y", "-framerate", String(FPS), "-i", path.join(tmp, "f%04d.png"),
  "-c:v", "libx264", "-pix_fmt", "yuv420p", "-profile:v", "high", "-crf", "18", "-preset", "slow",
  "-movflags", "+faststart", "-an", OUT], { stdio: "inherit" });
if (ff.status !== 0) throw new Error("ffmpeg failed");
fs.copyFileSync(path.join(tmp, `f${String(frames - 1).padStart(4, "0")}.png`), POSTER);
fs.rmSync(tmp, { recursive: true, force: true });
console.log(`wrote ${OUT} (${frames} frames, ${(fs.statSync(OUT).size / 1e6).toFixed(2)} MB) and ${POSTER}`);
