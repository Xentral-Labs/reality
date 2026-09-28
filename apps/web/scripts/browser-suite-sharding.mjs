export const parseShard = (value = "1/1") => {
  const match = /^(\d+)\/(\d+)$/.exec(value);
  if (!match) throw new Error(`Invalid BROWSER_SUITE_SHARD: ${value}`);
  const index = Number(match[1]);
  const count = Number(match[2]);
  if (count < 1 || index < 1 || index > count) {
    throw new Error(`Invalid BROWSER_SUITE_SHARD: ${value}`);
  }
  return { index, count };
};

export const distributeByDuration = (scripts, durations, count) => {
  const shards = Array.from({ length: count }, () => ({ scripts: [], seconds: 0 }));
  const weighted = scripts
    .map((script, position) => ({
      script,
      position,
      seconds: durations[script],
    }))
    .sort((left, right) => right.seconds - left.seconds || left.position - right.position);

  for (const entry of weighted) {
    const target = shards.reduce((lightest, shard) =>
      shard.seconds < lightest.seconds ? shard : lightest,
    );
    target.scripts.push(entry.script);
    target.seconds += entry.seconds;
  }
  return shards;
};
