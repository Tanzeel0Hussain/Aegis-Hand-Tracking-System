import test from "node:test";
import assert from "node:assert/strict";
import { musicGesture, TouchlessInstrument } from "../web/modes/music.mjs";
const hand = (x, y) => Array.from({ length: 21 }, () => ({ x, y }));
test("screen-right controls pitch in either mirror direction and result order", () => {
  const hands = [hand(0.2, 0.15), hand(0.8, 0.85)];
  assert.equal(musicGesture(hands, true).note, "C5");
  assert.equal(musicGesture([...hands].reverse(), true).note, "C5");
  assert.equal(musicGesture(hands, false).note, "C3");
  assert.ok(musicGesture(hands, true).volume <= 1);
  assert.equal(musicGesture([hand(0.2, -10), hand(0.8, 0.5)], true).note, "C5");
});
test("hand loss, crossing, malformed coordinates are silent", () => {
  assert.equal(musicGesture([]), null);
  assert.equal(musicGesture([hand(0.2, 0.5)]), null);
  assert.equal(musicGesture([hand(0.5, 0.5), hand(0.52, 0.2)]), null);
  assert.equal(musicGesture([hand(NaN, 0.2), hand(0.8, 0.5)]), null);
});
function fakeContext(resume) {
  const events = [];
  const parameter = {
    value: 0,
    cancelScheduledValues() {},
    setValueAtTime(v, t) {
      events.push(["set", v, t]);
    },
    linearRampToValueAtTime(v, t) {
      events.push(["ramp", v, t]);
    },
    setTargetAtTime(v) {
      events.push(["pitch", v]);
    },
  };
  return {
    events,
    state: "running",
    currentTime: 1,
    destination: {},
    createGain() {
      return { gain: parameter, connect() {} };
    },
    createOscillator() {
      return {
        frequency: parameter,
        connect() {},
        start() {},
        stop() {
          events.push(["stop"]);
        },
      };
    },
    resume: resume || (() => Promise.resolve()),
    close() {
      this.state = "closed";
      return Promise.resolve();
    },
  };
}
test("audio arms on enable, schedules fail-safe silence, and closes cleanly", async () => {
  const context = fakeContext();
  const instrument = new TouchlessInstrument(() => context);
  assert.equal(instrument.enabled, false);
  await instrument.enable();
  assert.equal(instrument.enabled, true);
  instrument.update(musicGesture([hand(0.2, 0.5), hand(0.8, 0.5)]));
  assert.ok(
    context.events.some((e) => e[0] === "ramp" && e[1] === 0 && e[2] === 1.25),
  );
  instrument.update(null);
  assert.deepEqual(context.events.at(-1), ["ramp", 0, 1.04]);
  instrument.close();
  assert.equal(context.state, "closed");
  assert.equal(instrument.enabled, false);
});
test("late audio resume cannot re-enable after mute", async () => {
  let resolve;
  const context = fakeContext(
    () =>
      new Promise((r) => {
        resolve = r;
      }),
  );
  const instrument = new TouchlessInstrument(() => context);
  const enabling = instrument.enable();
  instrument.close();
  resolve();
  assert.equal(await enabling, false);
  assert.equal(instrument.enabled, false);
});
