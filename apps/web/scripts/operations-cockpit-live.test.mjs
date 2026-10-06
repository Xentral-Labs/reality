import assert from "node:assert/strict";
import test from "node:test";
import { CockpitLiveRead } from "../src/unified/cockpitLiveRead.ts";

class Clock {
  time = 0;
  sequence = 0;
  timers = new Map();
  now = () => this.time;
  setTimeout = (callback, ms) => {
    const id = ++this.sequence;
    this.timers.set(id, { at: this.time + ms, callback });
    return id;
  };
  clearTimeout = (id) => this.timers.delete(id);
  async settle() {
    for (let i = 0; i < 8; i++) await Promise.resolve();
  }
  async advance(ms) {
    const until = this.time + ms;
    for (;;) {
      const next = [...this.timers]
        .filter(([, value]) => value.at <= until)
        .sort((a, b) => a[1].at - b[1].at)[0];
      if (!next) break;
      this.time = next[1].at;
      this.timers.delete(next[0]);
      next[1].callback();
      await this.settle();
    }
    this.time = until;
    await this.settle();
  }
}
const deferred = () => {
  let resolve, reject;
  const promise = new Promise((yes, no) => {
    resolve = yes;
    reject = no;
  });
  return { promise, resolve, reject };
};
function harness(read) {
  const clock = new Clock();
  const states = [];
  const live = new CockpitLiveRead({ read, clock, onChange: (state) => states.push(state) });
  live.start();
  return { clock, states, live, latest: () => states.at(-1) };
}

test("immediate read, five-second start cadence and no overlapping healthy reads", async () => {
  const first = deferred();
  let calls = 0;
  const h = harness(() => (++calls === 1 ? first.promise : Promise.resolve({ count: calls })));
  assert.equal(calls, 1);
  await h.clock.advance(4000);
  assert.equal(calls, 1);
  first.resolve({ count: 1 });
  await h.clock.settle();
  assert.equal(h.latest().status, "current");
  await h.clock.advance(1000);
  assert.equal(calls, 2);
  assert.equal(h.latest().data.count, 2);
  h.live.dispose();
  assert.equal(h.clock.timers.size, 0);
});

test("failure retains aged values; retry is 5/10/20/30 seconds and resets on success", async () => {
  let failure = false;
  const h = harness(async () => {
    if (failure) throw new Error("network");
    return { total: 42 };
  });
  await h.clock.settle();
  const receivedAt = h.latest().receivedAt;
  failure = true;
  await h.clock.advance(5000);
  assert.equal(h.latest().status, "stale");
  assert.equal(h.latest().data.total, 42);
  assert.equal(h.latest().receivedAt, receivedAt);
  for (const delay of [5000, 10000, 20000, 30000, 30000]) {
    assert.equal([...h.clock.timers.values()][0].at - h.clock.time, delay);
    await h.clock.advance(delay);
  }
  failure = false;
  await h.clock.advance(30000);
  assert.equal(h.latest().status, "current");
  assert.equal([...h.clock.timers.values()][0].at - h.clock.time, 5000);
  h.live.dispose();
});

test("eight-second timeout aborts and a late response cannot restore stale coverage", async () => {
  const stalled = deferred();
  let signal;
  const h = harness((s) => {
    signal = s;
    return stalled.promise;
  });
  await h.clock.advance(8000);
  assert.equal(signal.aborted, true);
  assert.equal(h.latest().status, "stale");
  assert.equal(h.latest().data, null);
  stalled.resolve({ incorrect: true });
  await h.clock.settle();
  assert.equal(h.latest().data, null);
  h.live.dispose();
});

test("hidden suspends timers and active reads; resume reads immediately and ages retained values", async () => {
  let calls = 0;
  const pending = deferred();
  const h = harness(() => (++calls === 1 ? Promise.resolve({ count: 1 }) : pending.promise));
  await h.clock.settle();
  await h.clock.advance(5000);
  h.live.setVisible(false);
  assert.equal(h.latest().status, "suspended");
  assert.equal(h.latest().data.count, 1);
  assert.equal(h.clock.timers.size, 0);
  await h.clock.advance(100000);
  assert.equal(calls, 2);
  pending.resolve({ count: 2 });
  await h.clock.settle();
  assert.equal(h.latest().data.count, 1);
  h.live.setVisible(true);
  await h.clock.settle();
  assert.equal(calls, 3);
  assert.equal(h.latest().status, "current");
  h.live.dispose();
});

test("context disposal rejects old responses and prevents further reads", async () => {
  const pending = deferred();
  let signal;
  const h = harness((s) => {
    signal = s;
    return pending.promise;
  });
  h.live.dispose();
  const before = h.states.length;
  pending.resolve({ tenant: "old-company" });
  await h.clock.advance(30000);
  assert.equal(signal.aborted, true);
  assert.equal(h.states.length, before);
  assert.equal(h.clock.timers.size, 0);
});

test("a healthy refresh preserves current observation until failure or replacement", async () => {
  const pending = deferred();
  let calls = 0;
  const h = harness(() => (++calls === 1 ? Promise.resolve({ total: 12 }) : pending.promise));
  await h.clock.settle();
  await h.clock.advance(5000);
  assert.equal(h.latest().status, "current");
  assert.equal(h.latest().data.total, 12);
  pending.resolve({ total: 13 });
  await h.clock.settle();
  assert.equal(h.latest().data.total, 13);
  h.live.dispose();
});

test("initially hidden observation reads nothing until visible", async () => {
  const clock = new Clock();
  let calls = 0;
  const live = new CockpitLiveRead({ clock, read: async () => ++calls, onChange: () => {} });
  live.start(false);
  await clock.advance(60000);
  assert.equal(calls, 0);
  assert.equal(clock.timers.size, 0);
  live.setVisible(true);
  await clock.settle();
  assert.equal(calls, 1);
  live.dispose();
});

test("current authorization loss clears company data and stops automatic reads", async () => {
  let denied = false;
  const h = harness(async () => {
    if (denied) throw Object.assign(new Error("access lost"), { status: 403 });
    return { secret: "company data" };
  });
  await h.clock.settle();
  denied = true;
  await h.clock.advance(5000);
  assert.equal(h.latest().status, "denied");
  assert.equal(h.latest().data, null);
  assert.equal(h.clock.timers.size, 0);
  h.live.dispose();
});

test("eight-hour controlled observation replaces snapshots with bounded retained state", async () => {
  let version = 0;
  const h = harness(async () => ({
    version: ++version,
    total: 100000 + version,
    buckets: Array.from({ length: 61 }, (_, i) => ({ at: i, count: version })),
    recent: Array.from({ length: 50 }, (_, i) => ({ id: `event-${version}-${i}` })),
  }));
  await h.clock.settle();
  for (let hour = 0; hour < 8; hour++) {
    await h.clock.advance(3600000);
    assert.equal(h.latest().data.buckets.length, 61);
    assert.equal(h.latest().data.recent.length, 50);
    assert.equal(h.latest().data.total, 100000 + version);
    assert.equal(h.clock.timers.size, 1);
    // The harness keeps observations for assertion; the production controller keeps one snapshot.
    h.states.splice(0, h.states.length - 1);
  }
  assert.equal(version, 5761);
  h.live.dispose();
  assert.equal(h.clock.timers.size, 0);
});
