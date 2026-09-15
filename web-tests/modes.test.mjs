import test from "node:test";
import assert from "node:assert/strict";
import { AirDraw } from "../web/modes/air-draw.mjs";
import { drawGestureEffect } from "../web/modes/gesture-effects.mjs";
function hand(pinched = true, x = 0.4) {
  const points = Array.from({ length: 21 }, () => ({ x, y: 0.5 }));
  points[0] = { x, y: 0.8 };
  points[9] = { x, y: 0.5 };
  points[8] = { x, y: 0.2 };
  points[4] = { x: x + (pinched ? 0.01 : 0.3), y: 0.2 };
  return points;
}
test("pinch draws; release and hand loss create separate strokes", () => {
  const ink = new AirDraw();
  ink.update([hand()], "#fff", 5);
  ink.update([hand(true, 0.45)], "#fff", 5);
  assert.equal(ink.strokes.length, 1);
  assert.equal(ink.strokes[0].points.length, 2);
  ink.update([hand(false)], "#fff", 5);
  ink.update([hand()], "#000", 8);
  assert.equal(ink.strokes.length, 2);
  assert.equal(ink.strokes[1].color, "#000");
  ink.update([], "#fff", 5);
  ink.update([hand()], "#fff", 5);
  assert.equal(ink.strokes.length, 3);
  ink.undo();
  assert.equal(ink.strokes.length, 2);
  ink.clear();
  assert.equal(ink.strokes.length, 0);
});
test("hand reordering stays with nearest wrist; a large jump lifts pen", () => {
  const ink = new AirDraw();
  ink.update([hand(true, 0.2)], "#fff", 5);
  ink.update([hand(true, 0.8), hand(true, 0.21)], "#fff", 5);
  assert.ok(ink.strokes[0].points.at(-1).x < 0.3);
  ink.update([hand(true, 0.8)], "#fff", 5);
  assert.equal(ink.strokes.length, 2);
});
test("drawing memory is bounded", () => {
  const ink = new AirDraw();
  ink.strokes = [{ points: Array(12000).fill({ x: 0, y: 0 }) }];
  assert.match(ink.update([hand()], "#fff", 5), /full/);
  assert.equal(ink.active, null);
});
test("portal needs two hands and renders a bounded particle count", () => {
  let circles = 0;
  const ctx = {
    save() {},
    restore() {},
    createRadialGradient() {
      return { addColorStop() {} };
    },
    fillRect() {},
    beginPath() {},
    ellipse() {},
    stroke() {},
    arc() {
      circles++;
    },
    fill() {},
  };
  assert.match(drawGestureEffect(ctx, [], 640, 480, 0, false), /both/);
  assert.equal(circles, 0);
  drawGestureEffect(
    ctx,
    [hand(true, 0.2), hand(true, 0.8)],
    640,
    480,
    100,
    false,
  );
  assert.equal(circles, 64);
});
