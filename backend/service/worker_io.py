import csv
import shutil
from pathlib import Path


def count_existing_rows(out_dir: Path) -> int:
    if not out_dir.exists():
        return 0
    total = 0
    for p in sorted(out_dir.glob("*.csv")):
        with open(p, "r", encoding="utf-8-sig") as f:
            total += max(0, sum(1 for _ in f) - 1)
    return total


def copy_resume_csvs(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for p in sorted(src.glob("*.csv")):
        shutil.copy2(p, dst / p.name)


class CsvVolumeWriter:
    """Writes rows into base_name_part{N}.csv files, splitting when a volume
    reaches `max_per_file` data rows (header excluded)."""

    def __init__(self, *, out_dir: Path, base_name: str,
                 header: list[str], max_per_file: int) -> None:
        self.out_dir = out_dir
        self.base_name = base_name
        self.header = header
        self.max_per_file = max_per_file
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self._volume_idx = 1
        self._rows_in_volume = 0
        self._file = None
        self._writer = None

    def _path(self, idx: int) -> Path:
        return self.out_dir / f"{self.base_name}_part{idx}.csv"

    def resume(self) -> None:
        """Pick up where existing volumes left off."""
        idx = 1
        while self._path(idx).exists():
            idx += 1
        self._volume_idx = max(1, idx - 1) if self._path(max(1, idx - 1)).exists() else 1
        path = self._path(self._volume_idx)
        if path.exists():
            with open(path, "r", encoding="utf-8-sig") as f:
                rows = max(0, sum(1 for _ in f) - 1)
            if rows >= self.max_per_file:
                self._volume_idx += 1
                self._rows_in_volume = 0
            else:
                self._rows_in_volume = rows

    def _ensure_open(self) -> None:
        path = self._path(self._volume_idx)
        is_new = not path.exists()
        if self._file is None:
            self._file = open(path, "a", newline="", encoding="utf-8-sig")
            self._writer = csv.writer(self._file)
            if is_new:
                self._writer.writerow(self.header)

    def write_row(self, row: list[str]) -> None:
        if self._rows_in_volume >= self.max_per_file:
            self.close()
            self._volume_idx += 1
            self._rows_in_volume = 0
        self._ensure_open()
        self._writer.writerow(row)
        self._rows_in_volume += 1

    def flush(self) -> None:
        if self._file is not None:
            self._file.flush()

    def close(self) -> None:
        if self._file is not None:
            self._file.close()
            self._file = None
            self._writer = None
