import test from "node:test";
import assert from "node:assert/strict";
import { countFingers, StableCount } from "../web/tracking.mjs";
function hand(open = true) {
  const p = Array.from({ length: 21 }, () => ({ x: 0, y: 0 }));
  for (const [base, x] of [
    [5, -0.2],
    [9, 0],
    [13, 0.2],
    [17, 0.4],
  ]) {
    p[base] = { x, y: 0.3 };
    p[base + 1] = { x, y: 0.6 };
    p[base + 2] = { x, y: 0.8 };
    p[base + 3] = { x, y: open ? 1 : 0.2 };
  }
  p[3] = { x: -0.3, y: 0.3 };
  p[4] = open ? { x: -0.6, y: 0.5 } : { x: 0.1, y: 0.2 };
  return p;
}
test("open palm and closed fist synthetic geometry", () => {
  assert.equal(countFingers(hand()), 5);
  assert.equal(countFingers(hand(false)), 0);
});
test("in-plane rotation preserves the synthetic count", () => {
  for (const open of [true, false]) {
    const p = hand(open).map(({ x, y }) => ({ x: 3 - y * 2, y: 4 + x * 2 }));
    assert.equal(countFingers(p), open ? 5 : 0);
  }
});
test("invalid landmarks and degenerate palms return zero", () => {
  assert.equal(countFingers([]), 0);
  assert.equal(countFingers(Array(21).fill({ x: 0, y: 0 })), 0);
  const p = hand();
  p[8].x = NaN;
  assert.equal(countFingers(p), 0);
});
test("smoothing resets on disappearance and hand-count changes", () => {
  const s = new StableCount();
  for (let i = 0; i < 7; i++) s.update(5, 1);
  assert.equal(s.update(0, 0), 0);
  assert.equal(s.update(8, 2), 8);
  assert.equal(s.update(1, 1), 1);
});
test("ties use the newest count", () => {
  const s = new StableCount();
  s.update(2, 1);
  assert.equal(s.update(3, 1), 3);
});
