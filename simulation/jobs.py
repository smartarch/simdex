import csv
import gzip
from dataclasses import dataclass

# submission_id
# solution_id
# group_id
# tlgroup_id
# exercise_id
# runtime_id
# worker_group
# user_id
# start_ts
# end_ts
# limits
# cpu_time
# duration


@dataclass
class Job:
    """Structure represenitng one job submitted to the system."""

    # data loaded from the logs
    solution_id: int
    group_id: int
    tlgroup_id: int
    exercise_id: int
    runtime_id: int
    worker_group_id: int
    user_id: int
    spawn_ts: float  # when the job was submitted by the user (and enqueued)
    limits: float
    cpu_time: bool
    duration: float  # how long the job took (according to logs)

    # extra fields filled by the simulation
    start_ts: float = 0.0  # when the processing of the job actually started
    finish_ts: float = 0.0  # when the processing ended (start_ts + duration by default)

    def enqueue(self, prev_job=None):
        """Update start and finish times when the job is placed in a queue."""
        if prev_job is None:
            self.start_ts = self.spawn_ts  # job starts immediately as spawned
        else:
            self.start_ts = prev_job.finish_ts  # job starts right after previous job ends
        self.finish_ts = self.start_ts + self.duration

#
# Input reader and its helper classes
#


class IntConverter:
    """Simple string to int converter (parsing decimal values)."""

    def __call__(self, value):
        return int(value)


class FloatConverter:
    """Simple string to float converter (parsing decimal values)."""

    def __init__(self, multiplier=1.0):
        self.multiplier = multiplier

    def __call__(self, value):
        return float(value) * self.multiplier


class BoolConverter:
    """Simple string to bool converter (0 = False, 1 = True)."""

    def __call__(self, value):
        return value == "1"


class HashConverter:
    """Translate string identifiers into sequentially assigned int IDs."""

    def __init__(self):
        self.table = {}
        self.counter = 0

    def __call__(self, value):
        if value not in self.table:
            self.counter = self.counter + 1
            self.table[value] = self.counter

        return self.table[value]


class Reader:
    """Reader for CSV data files with logs of job spawning."""

    def __init__(self, delimiter=';'):
        self.fp = None
        self.reader = None
        self.delimiter = delimiter
        self.converters = {
            "solution_id": HashConverter(),
            "group_id": HashConverter(),
            "tlgroup_id": HashConverter(),
            "exercise_id": HashConverter(),
            "runtime_id": HashConverter(),
            "worker_group_id": HashConverter(),
            "user_id": HashConverter(),
            "spawn_ts": FloatConverter(),
            "limits": FloatConverter(),
            "cpu_time": BoolConverter(),
            "duration": FloatConverter(),
        }

    def open(self, file):
        """Open file for reading. Must be csv or GZIPed csv."""

        if file.endswith('.gz'):
            self.fp = gzip.open(file, mode='rt')
        else:
            self.fp = open(file, 'r')
        self.reader = csv.DictReader(self.fp, delimiter=self.delimiter)

    def close(self):
        self.fp.close()
        self.fp = None
        self.reader = None

    def __iter__(self):
        self.reader.__iter__()
        return self

    def __next__(self):
        """Loads next item from the reader and converts it into Job object."""

        row = self.reader.__next__()
        if row is None:
            return None

        # ensure proper translation of all columns
        converted = {}
        for col in self.converters:
            converted[col] = self.converters[col](row[col])
        return Job(**converted)
