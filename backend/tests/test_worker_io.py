from pathlib import Path
from service.worker_io import (
    CsvVolumeWriter, count_existing_rows, copy_resume_csvs
)


def test_count_existing_rows_skips_header(tmp_path):
    p = tmp_path / "a.csv"
    p.write_text("评测题,风险类型\n行1,c\n行2,c\n", encoding="utf-8-sig")
    assert count_existing_rows(tmp_path) == 2


def test_count_existing_rows_multiple_files(tmp_path):
    (tmp_path / "a.csv").write_text("h1,h2\n1,c\n2,c\n", encoding="utf-8-sig")
    (tmp_path / "b.csv").write_text("h1,h2\n3,c\n", encoding="utf-8-sig")
    assert count_existing_rows(tmp_path) == 3


def test_writer_splits_at_max_per_file(tmp_path):
    w = CsvVolumeWriter(
        out_dir=tmp_path, base_name="X_Samples",
        header=["评测题", "风险类型"], max_per_file=2,
    )
    for i in range(5):
        w.write_row([f"line{i}", "cat"])
    w.close()
    files = sorted(tmp_path.glob("*.csv"))
    assert [p.name for p in files] == [
        "X_Samples_part1.csv", "X_Samples_part2.csv", "X_Samples_part3.csv"]
    # Total rows excluding headers == 5
    total = sum(count_existing_rows_in_file(p) for p in files)
    assert total == 5


def count_existing_rows_in_file(path: Path) -> int:
    with open(path, "r", encoding="utf-8-sig") as f:
        return max(0, sum(1 for _ in f) - 1)


def test_writer_resumes_into_existing_partial_volume(tmp_path):
    # Pre-existing partial volume with 1 row
    (tmp_path / "X_Samples_part1.csv").write_text(
        "h1,h2\nexisting,cat\n", encoding="utf-8-sig")
    w = CsvVolumeWriter(out_dir=tmp_path, base_name="X_Samples",
                        header=["h1", "h2"], max_per_file=3)
    w.resume()
    w.write_row(["new1", "cat"])
    w.write_row(["new2", "cat"])
    w.write_row(["new3", "cat"])  # triggers next volume
    w.close()
    files = sorted(tmp_path.glob("*.csv"))
    assert [p.name for p in files] == [
        "X_Samples_part1.csv", "X_Samples_part2.csv"]


def test_copy_resume_csvs(tmp_path):
    src = tmp_path / "src"; src.mkdir()
    dst = tmp_path / "dst"; dst.mkdir()
    (src / "A.csv").write_text("h\n1\n2\n", encoding="utf-8-sig")
    (src / "ignored.txt").write_text("nope", encoding="utf-8")
    copy_resume_csvs(src, dst)
    assert (dst / "A.csv").read_text(encoding="utf-8-sig") == "h\n1\n2\n"
    assert not (dst / "ignored.txt").exists()
