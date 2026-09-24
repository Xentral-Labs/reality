from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("ci_backend_test_shard.py")


def load_sharder():
    spec = importlib.util.spec_from_file_location("ci_backend_test_shard", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load CI backend test sharder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BackendTestShardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sharder = load_sharder()

    def test_shards_cover_every_test_file_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            names = [f"test_{letter}.py" for letter in "abcdef"]
            for name in names:
                (root / name).write_text("x")
            shards = self.sharder.shard_files(root, 2, {})
            paths = [path.name for shard in shards for path in shard]
            self.assertCountEqual(paths, names)
            self.assertEqual(len(paths), len(set(paths)))

    def test_recorded_seconds_decide_the_shard(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("test_slow.py", "test_a.py", "test_b.py", "test_c.py"):
                (root / name).write_text("x")
            shards = self.sharder.shard_files(
                root,
                2,
                {"test_slow.py": 30.0, "test_a.py": 10.0, "test_b.py": 10.0, "test_c.py": 10.0},
            )
            heavy = next(shard for shard in shards if any(p.name == "test_slow.py" for p in shard))
            light = next(shard for shard in shards if shard is not heavy)
            self.assertEqual(len(heavy), 1)
            self.assertEqual(len(light), 3)

    def test_an_unmeasured_file_weighs_the_median_of_the_measured_ones(self) -> None:
        """A new test file must not weigh nothing, or it all lands in one shard."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("test_known.py", "test_new_one.py", "test_new_two.py"):
                (root / name).write_text("x")
            weights = self.sharder.weigh(
                sorted(root.rglob("test_*.py")), root, {"test_known.py": 8.0}
            )
            self.assertEqual({round(value, 1) for value in weights.values()}, {8.0})

    def test_invalid_or_empty_input_fails_safe(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                self.sharder.shard_files(Path(directory), 2)
            with self.assertRaises(ValueError):
                self.sharder.shard_files(Path(directory), 0)


if __name__ == "__main__":
    unittest.main()
