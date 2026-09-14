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

    def test_shards_cover_every_test_file_once_and_balance_weight(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sizes = {"test_large.py": 100, "test_medium.py": 60, "test_small.py": 40}
            for name, size in sizes.items():
                (root / name).write_text("x" * size)
            shards = self.sharder.shard_files(root, 2)
            paths = [path.name for shard in shards for path in shard]
            self.assertCountEqual(paths, sizes)
            self.assertEqual(len(paths), len(set(paths)))
            weights = [sum(path.stat().st_size for path in shard) for shard in shards]
            self.assertEqual(weights, [100, 100])

    def test_invalid_or_empty_input_fails_safe(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                self.sharder.shard_files(Path(directory), 2)
            with self.assertRaises(ValueError):
                self.sharder.shard_files(Path(directory), 0)


if __name__ == "__main__":
    unittest.main()
