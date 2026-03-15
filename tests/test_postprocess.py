import tempfile
import unittest
from pathlib import Path

from qzone_text_exporter import postprocess


def write_post(path: Path, *, title: str, date: str, body: str) -> None:
    text = "\n".join([f"标题：{title}", f"日期：{date}", "分类：日志", "", body]) + "\n"
    path.write_text(text, encoding="utf-8")


class TestPostprocess(unittest.TestCase):
    def test_quality_prefix_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            write_post(d / "a - 2020-01-01.txt", title="a", date="2020-01-01", body="x" * 10)
            write_post(d / "b - 2020-01-02.txt", title="b", date="2020-01-02", body="")
            idx1 = postprocess.quality_buckets_and_rename(dir_path=d, rename_prefix=True)
            self.assertTrue(idx1.exists())
            names1 = sorted(p.name for p in d.glob("*.txt"))
            # Run again: names should remain stable.
            idx2 = postprocess.quality_buckets_and_rename(dir_path=d, rename_prefix=True)
            self.assertTrue(idx2.exists())
            names2 = sorted(p.name for p in d.glob("*.txt"))
            self.assertEqual(names1, names2)
            # Ensure no double-prefix like 1-1-
            for name in names2:
                self.assertFalse(name.startswith("1-1-") or name.startswith("2-2-") or name.startswith("3-3-") or name.startswith("4-4-"))

    def test_quality_index_has_blog_id_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            write_post(d / "a - 2020-01-01.txt", title="a", date="2020-01-01", body="hello world")
            (d / "index.csv").write_text(
                "\ufefftitle,published_date,blog_id,filename,status,note\n"
                "a,2020-01-01,12345,a - 2020-01-01.txt,ok,\n",
                encoding="utf-8",
            )

            out = postprocess.quality_buckets_and_rename(dir_path=d, rename_prefix=True)
            self.assertTrue(out.exists())
            rows = out.read_text(encoding="utf-8-sig").splitlines()
            self.assertIn("blog_id", rows[0])
            # The only post should keep the blog_id in index_quality.csv (even after rename).
            self.assertTrue(any(",12345" in line for line in rows[1:]))


if __name__ == "__main__":
    unittest.main()
