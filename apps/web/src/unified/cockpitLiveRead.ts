/** Presentation-only read lifecycle. It never schedules or controls business work. */
export type LiveReadState<T> = {
  data: T | null;
  status: "loading" | "current" | "stale" | "suspended" | "denied";
  receivedAt: number | null;
  error: unknown;
};
type Clock = {
  now: () => number;
  setTimeout: (callback: () => void, ms: number) => unknown;
  clearTimeout: (id: unknown) => void;
};
const browserClock: Clock = {
  now: () => Date.now(),
  setTimeout: (callback, ms) => globalThis.setTimeout(callback, ms),
  clearTimeout: (id) => globalThis.clearTimeout(id as ReturnType<typeof setTimeout>),
};

export class CockpitLiveRead<T> {
  private state: LiveReadState<T> = {
    data: null,
    status: "loading",
    receivedAt: null,
    error: null,
  };
  private readonly read: (signal: AbortSignal) => Promise<T>;
  private readonly onChange: (state: LiveReadState<T>) => void;
  private readonly clock: Clock;
  private timer: unknown;
  private deadline: unknown;
  private request: AbortController | null = null;
  private generation = 0;
  private failures = 0;
  private visible = true;
  private started = false;
  private disposed = false;
  private denied = false;

  constructor(options: {
    read: (signal: AbortSignal) => Promise<T>;
    onChange: (state: LiveReadState<T>) => void;
    clock?: Clock;
  }) {
    this.read = options.read;
    this.onChange = options.onChange;
    this.clock = options.clock ?? browserClock;
  }
  start(visible = true) {
    if (this.started || this.disposed) return;
    this.started = true;
    this.visible = visible;
    if (visible) this.refresh();
    else this.publish({ status: "suspended" });
  }
  setVisible(visible: boolean) {
    if (this.disposed || this.denied || visible === this.visible) return;
    this.visible = visible;
    this.cancel();
    if (visible) this.refresh();
    else this.publish({ status: "suspended" });
  }
  dispose() {
    this.disposed = true;
    this.cancel();
  }
  private publish(patch: Partial<LiveReadState<T>>) {
    this.state = { ...this.state, ...patch };
    this.onChange(this.state);
  }
  private cancel() {
    this.generation++;
    this.clock.clearTimeout(this.timer);
    this.clock.clearTimeout(this.deadline);
    this.timer = undefined;
    this.deadline = undefined;
    this.request?.abort();
    this.request = null;
  }
  private schedule(delay: number) {
    if (this.disposed || !this.visible || this.denied) return;
    this.timer = this.clock.setTimeout(() => {
      this.timer = undefined;
      this.refresh();
    }, delay);
  }
  private failed(error: unknown) {
    const status =
      error && typeof error === "object" && "status" in error ? error.status : undefined;
    if (status === 401 || status === 403 || status === 404) {
      this.denied = true;
      this.publish({ data: null, status: "denied", receivedAt: null, error });
      return;
    }
    const retry = [5000, 10000, 20000, 30000][Math.min(this.failures++, 3)];
    this.publish({ status: "stale", error });
    this.schedule(retry);
  }
  private refresh() {
    if (this.disposed || !this.visible || this.denied || this.request) return;
    const generation = ++this.generation;
    const request = new AbortController();
    this.request = request;
    const startedAt = this.clock.now();
    if (this.state.data === null) this.publish({ status: "loading" });
    else if (this.state.status === "suspended") this.publish({ status: "stale" });
    this.deadline = this.clock.setTimeout(() => {
      if (generation !== this.generation || this.disposed) return;
      this.cancel();
      this.failed(new Error("Cockpit read timed out."));
    }, 8000);
    // A synchronous transport refusal has the same lifecycle as a rejected read.
    let pending: Promise<T>;
    try {
      pending = this.read(request.signal);
    } catch (error) {
      pending = Promise.reject(error);
    }
    pending.then(
      (data) => {
        if (generation !== this.generation || this.disposed || !this.visible) return;
        this.clock.clearTimeout(this.deadline);
        this.deadline = undefined;
        this.request = null;
        this.failures = 0;
        this.publish({ data, status: "current", receivedAt: this.clock.now(), error: null });
        this.schedule(Math.max(0, startedAt + 5000 - this.clock.now()));
      },
      (error) => {
        if (generation !== this.generation || this.disposed || !this.visible) return;
        this.clock.clearTimeout(this.deadline);
        this.deadline = undefined;
        this.request = null;
        this.failed(error);
      },
    );
  }
}
