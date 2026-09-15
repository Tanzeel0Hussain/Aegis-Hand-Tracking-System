import { chromium } from "playwright";
import { spawn } from "node:child_process";
import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
const server = spawn(
  "python3",
  ["-m", "http.server", "4173", "--bind", "127.0.0.1"],
  { stdio: "ignore" },
);
let browser;
try {
  for (let i = 0; i < 50; i++) {
    try {
      if ((await fetch("http://127.0.0.1:4173/web/")).ok) break;
    } catch {}
    await new Promise((r) => setTimeout(r, 200));
  }
  browser = await chromium.launch({
    args: [
      "--use-fake-device-for-media-stream",
      "--use-fake-ui-for-media-stream",
    ],
  });
  const context = await browser.newContext({
    permissions: ["camera"],
    viewport: { width: 1360, height: 1000 },
  });
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.addInitScript(() => {
    window.__streams = [];
    const original = navigator.mediaDevices.getUserMedia.bind(
      navigator.mediaDevices,
    );
    navigator.mediaDevices.getUserMedia = async (options) => {
      const stream = await original(options);
      window.__streams.push(stream);
      return stream;
    };
  });
  // Lifecycle UI tests use a deterministic detector while using actual browser media tracks.
  await page.route("**/detectors.mjs", (route) =>
    route.fulfill({
      contentType: "text/javascript",
      body: "export async function loadDetectors(){await new Promise(r=>setTimeout(r,250));return {detect(){return {hands:{landmarks:window.__hands||[],handedness:[]},body:null}},close(){}}}",
    }),
  );
  await page.goto("http://127.0.0.1:4173/web/");
  assert.equal(await page.evaluate(() => window.__streams.length), 0);
  await page.getByRole("button", { name: "Start Camera" }).click();
  await page.getByRole("button", { name: "Stop Camera" }).click();
  await page.waitForTimeout(400);
  assert.equal(
    await page.evaluate(() => window.__streams.length),
    0,
    "Cancel during model loading must not open camera",
  );
  await page.getByRole("button", { name: "Start Camera" }).click();
  await page.getByText("CAMERA ON", { exact: true }).waitFor();
  await page.waitForFunction(
    () => Number(document.getElementById("viewport").dataset.frames) > 1,
  );
  // Exercise drawing controls and portal rendering with deterministic landmarks.
  await mkdir("web-test-results", { recursive: true });
  await page.evaluate(() => {
    const points=Array.from({length:21},()=>({x:.4,y:.5}));
    points[0]={x:.4,y:.8};points[9]={x:.4,y:.5};
    points[8]={x:.4,y:.2};points[4]={x:.41,y:.2};
    window.__hands=[points];
  });
  await page.getByRole("button",{name:"03 · Air Drawing"}).click();
  await page.getByText("CAMERA ON",{exact:true}).waitFor();
  await page.getByText("Drawing · release your pinch to lift the pen.",{exact:true}).waitFor();
  await page.evaluate(()=>{window.__hands=[];});
  await page.getByText("Show one hand, then pinch to draw.",{exact:true}).waitFor();
  const painted=()=>{const c=document.getElementById('overlay');return c.getContext('2d').getImageData(0,0,c.width,c.height).data.some((v,i)=>i%4===3&&v>0);};
  assert.equal(await page.evaluate(painted),true,'Air drawing remains after hand disappears');
  const downloadPromise=page.waitForEvent('download');
  await page.getByRole('button',{name:'Save PNG'}).click();
  const download=await downloadPromise;
  assert.equal(download.suggestedFilename(),'aegis-air-drawing.png');
  await page.getByRole('button',{name:'Undo',exact:true}).click();
  assert.equal(await page.evaluate(painted),false,'Undo removes the stroke');
  await page.getByRole('button',{name:'Clear',exact:true}).click();
  await page.getByRole('button',{name:'04 · Color Portal'}).click();
  await page.getByText('CAMERA ON',{exact:true}).waitFor();
  await page.evaluate(()=>{window.__hands=[.25,.75].map(x=>Array.from({length:21},()=>({x,y:.5})));});
  await page.getByText('Move hands apart to expand · move up/down to change colors.',{exact:true}).waitFor();
  assert.equal(await page.evaluate(painted),true,'Portal renders');
  await page.screenshot({path:'web-test-results/portal-synthetic.png',fullPage:true});
  await page.evaluate(()=>{window.__hands=[];});
  // Switching an active mode releases the previous stream and restarts cleanly.
  for (const name of [
    "03 · Air Drawing",
    "04 · Color Portal",
    "02 · Full Body",
    "01 · Hands",
  ]) {
    await page.getByRole("button", { name }).click();
    await page.getByText("CAMERA ON", { exact: true }).waitFor();
    assert.equal(
      await page.evaluate(() =>
        window.__streams
          .slice(0, -1)
          .every((s) => s.getTracks().every((t) => t.readyState === "ended")),
      ),
      true,
    );
  }
  await page.getByRole("button", { name: "Stop Camera" }).click();
  assert.equal(
    await page.evaluate(() =>
      window.__streams.every((s) =>
        s.getTracks().every((t) => t.readyState === "ended"),
      ),
    ),
    true,
  );
  // Permission-denied state.
  await page.evaluate(() => {
    navigator.mediaDevices.getUserMedia = async () => {
      throw new DOMException("Denied", "NotAllowedError");
    };
  });
  await page.getByRole("button", { name: "Start Camera" }).click();
  await page
    .getByRole("alert")
    .filter({ hasText: "permission was denied" })
    .waitFor();
  // Late permission response after Stop must immediately release tracks.
  await page.evaluate(() => {
    navigator.mediaDevices.getUserMedia = () =>
      new Promise((resolve) => {
        window.__resolveCamera = resolve;
      });
  });
  await page.getByRole("button", { name: "Start Camera" }).click();
  await page
    .getByText("Waiting for camera permission…", { exact: true })
    .waitFor();
  await page.getByRole("button", { name: "Stop Camera" }).click();
  await page.evaluate(() => {
    const canvas = document.createElement("canvas");
    canvas.width = 32;
    canvas.height = 32;
    const stream = canvas.captureStream(1);
    window.__lateStream = stream;
    window.__resolveCamera(stream);
  });
  await page.waitForFunction(() =>
    window.__lateStream.getTracks().every((t) => t.readyState === "ended"),
  );
  await mkdir("web-test-results", { recursive: true });
  await page.screenshot({
    path: "web-test-results/desktop.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "03 · Air Drawing" }).click();
  for (const width of [320, 390, 768]) {
    await page.setViewportSize({ width, height: 900 });
    assert.ok(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
      "Layout overflow " + width,
    );
  }
  assert.deepEqual(errors, []);
  await page.close();
  // Real MediaPipe models and real browser camera pipeline on synthetic video.
  const real = await context.newPage();
  const realErrors = [];
  real.on("pageerror", (e) => realErrors.push(e.message));
  await real.goto("http://127.0.0.1:4173/web/");
  await real.getByRole("button", { name: "02 · Full Body" }).click();
  await real.getByRole("button", { name: "Start Camera" }).click();
  await real
    .getByText("CAMERA ON", { exact: true })
    .waitFor({ timeout: 120000 });
  await real.waitForFunction(
    () => Number(document.getElementById("viewport").dataset.frames) > 2,
    null,
    { timeout: 60000 },
  );
  assert.equal(await real.getByRole("alert").textContent(), "");
  await real.getByRole("button", { name: "Stop Camera" }).click();
  assert.deepEqual(realErrors, []);
  console.log(
    "PASS: cancel/restart, real camera-track cleanup, denied permission, late permission cancellation, responsive layouts, and real MediaPipe hand+pose inference on synthetic camera video.",
  );
} finally {
  await browser?.close();
  server.kill();
}
