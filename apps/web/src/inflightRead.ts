/** Share only concurrent reads. Resolved values are never retained as a cache. */
export function shareInFlight<T>(
  reads: Map<string, Promise<T>>,
  key: string,
  load: () => Promise<T>,
): Promise<T> {
  const current = reads.get(key);
  if (current) return current;

  const pending = load();
  reads.set(key, pending);
  const clear = () => {
    if (reads.get(key) === pending) reads.delete(key);
  };
  void pending.then(clear, clear);
  return pending;
}
