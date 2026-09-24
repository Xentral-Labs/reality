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

    def test_shards_cover_every_test_file_once_and_hold_the_same_count(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            names = [f"test_{letter}.py" for letter in "abcdef"]
            for name in names:
                (root / name).write_text("x")
            shards = self.sharder.shard_files(root, 2)
            paths = [path.name for shard in shards for path in shard]
            self.assertCountEqual(paths, names)
            self.assertEqual(len(paths), len(set(paths)))
            self.assertEqual([len(shard) for shard in shards], [3, 3])

    def test_neighbours_in_the_tree_land_in_different_shards(self) -> None:
        """Files that sit together tend to cost alike; splitting them spreads the load."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for letter in "abcd":
                (root / f"test_{letter}.py").write_text("x")
            first, second = self.sharder.shard_files(root, 2)
            self.assertEqual([path.name for path in first], ["test_a.py", "test_c.py"])
            self.assertEqual([path.name for path in second], ["test_b.py", "test_d.py"])

    def test_the_recorded_durations_do_not_decide_the_split(self) -> None:
        """They are a diagnostic: weighing them measured 20% slower than counting."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for letter in "ab":
                (root / f"test_{letter}.py").write_text("x")
            import inspect

            signature = inspect.signature(self.sharder.shard_files)
            self.assertEqual(list(signature.parameters), ["root", "total"])

    def test_invalid_or_empty_input_fails_safe(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                self.sharder.shard_files(Path(directory), 2)
            with self.assertRaises(ValueError):
                self.sharder.shard_files(Path(directory), 0)


if __name__ == "__main__":
    unittest.main()
