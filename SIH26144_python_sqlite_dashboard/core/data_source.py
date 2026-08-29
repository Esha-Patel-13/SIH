from dataclasses import dataclass, field
from pathlib import Path
from time import monotonic

from .database import read_samples, source_info
from .config import FS


class DataSource:
    def start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def pull_due_samples(self):
        raise NotImplementedError

    def reset(self):
        raise NotImplementedError


@dataclass
class RecordedSQLiteSource(DataSource):
    """Finite recorded-data source for a one-shot dashboard demonstration."""
    db_path: Path
    fs: float = FS
    cursor: int = 1
    running: bool = True
    finished: bool = False
    last_clock: float = field(default_factory=monotonic)
    accumulator: float = 0.0

    def start(self):
        self.last_clock = monotonic()
        self.running = True
        self.finished = False
        self.accumulator = 0.0

    def stop(self):
        self.running = False
        self.accumulator = 0.0

    def reset(self):
        info = source_info(self.db_path)
        self.cursor = int(info["first_id"] or 1)
        self.running = True
        self.finished = False
        self.last_clock = monotonic()
        self.accumulator = 0.0

    def start_from_beginning(self):
        self.reset()

    def _read_once(self, count: int):
        info = source_info(self.db_path)
        first_id = int(info["first_id"] or 1)
        last_id = int(info["last_id"] or 0)
        if not info["count"]:
            self.finished = True
            self.running = False
            return []

        if self.cursor > last_id:
            self.finished = True
            self.running = False
            return []

        take = min(count, last_id - self.cursor + 1)
        chunk = read_samples(self.db_path, self.cursor, take)
        if not chunk:
            self.finished = True
            self.running = False
            return []
        self.cursor = int(chunk[-1]["id"]) + 1
        if self.cursor > last_id:
            self.finished = True
            self.running = False
        return chunk

    def pull_due_samples(self):
        """Return samples according to the 100 Hz clock; stop at EOF."""
        if not self.running:
            return []

        now = monotonic()
        elapsed = now - self.last_clock
        self.last_clock = now
        self.accumulator += elapsed * self.fs
        due = int(self.accumulator)
        if due <= 0:
            return []

        # Prevent an inactive browser tab from causing a huge catch-up burst.
        due = min(due, 500)
        self.accumulator -= due
        return self._read_once(due)
