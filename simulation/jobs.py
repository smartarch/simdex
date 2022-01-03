import csv
import gzip
from dataclasses import dataclass


@dataclass
class Job:
    """Structure represenitng one job submitted to the system."""

    # fileds known when the job is created (spawned)
    solution_id: int
    group_id: int  # corresponds to the lab group where the student gets the assignments
    tlgroup_id: int  # top-level group corresponds to the course the student attends
    exercise_id: int
    runtime_id: int  # corresponds to a programming language used for the solution
    worker_group_id: str  # identification of dedicated group of workers (possibly with specialized HW or SW installed)
    user_id: int
    spawn_ts: float  # unix time stamp when the job was submitted by the user (and enqueued)
    limits: float  # time limit for all tests (sum)
    cpu_time: bool  # True if CPU time was measured (more precise), False for wall time (includes IOs, page faults, ...)

    # the following fiedls were filled after the job was evaluated
    # (the dispatcher or MAPE-K loop should not read these fields when the job is being assigned)
    correctness: float  # how the solution was rated (on 0 - 1 scale, 1 being completely correct).
    compilation_ok: bool  # True if the solution passed compilation, False means that no test were actually executed
    duration: float  # how long the job took (according to logs)

    # extra fields filled by the simulation
    start_ts: float = 0.0  # when the processing of the job actually started (simulation time)
    finish_ts: float = 0.0  # when the processing ended (start_ts + duration by default)

    def enqueue(self, prev_job=None):
        """Update start and finish times when the job is placed in a queue."""
        if prev_job is None:
            self.start_ts = self.spawn_ts  # job starts immediately as spawned
        else:
            self.start_ts = prev_job.finish_ts  # job starts right after previous job ends
        self.finish_ts = self.start_ts + self.duration


@dataclass
class RefJob:
    """Structure representing a reference solution job.

    Reference solutions are used as additional data source for job duration estimation.
    """

    # fileds known when the job is created (spawned)
    solution_id: int
    exercise_id: int
    runtime_id: int  # corresponds to a programming language used for the solution
    worker_group_id: str  # identification of dedicated group of workers (possibly with specialized HW or SW installed)
    spawn_ts: float  # unix time stamp when the job was submitted by the user (and enqueued)

    # the following fiedls were filled after the job was evaluated
    # (the dispatcher or MAPE-K loop should not read these fields when the job is being assigned)
    correctness: float  # how the solution was rated (on 0 - 1 scale, 1 being completely correct).
    compilation_ok: bool  # True if the solution passed compilation, False means that no test were actually executed
    duration: float  # how long the job took (according to logs)


#
# Input reader and its helper classes
#


def str_passthru(value):
    """Simple string pass-through (just to simplify desing of the reader)."""
    return value


def bool_converter(value):
    """Simple string to bool converter (0 = False, 1 = True)."""
    return value == "1"


class IntConverter:
    """Simple string to int converter (parsing decimal values)."""

    def __call__(self, value):
        return int(value)


class FloatConverter:
    """A string to float converter (parsing decimal values) with embedded linear transformation.

    Parsed value x is transformed by Ax + B, where A,B are constants set in constructor.
    """

    def __init__(self, multiplier=1.0, addition=0.0):
        self.multiplier = multiplier
        self.addition = addition

    def __call__(self, value):
        return float(value) * self.multiplier + self.addition


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


class ReaderBase:
    """Reader for CSV data files with logs of job spawning."""

    def __init__(self, delimiter=';'):
        self.fp = None
        self.reader = None
        self.delimiter = delimiter
        self.converters = {}

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
        return converted


class JobReader(ReaderBase):
    def __init__(self, delimiter=';'):
        super().__init__(delimiter)
        self.converters = {
            "solution_id": HashConverter(),
            "group_id": HashConverter(),
            "tlgroup_id": HashConverter(),
            "exercise_id": HashConverter(),
            "runtime_id": HashConverter(),
            "worker_group_id": str_passthru,
            "user_id": HashConverter(),
            "spawn_ts": FloatConverter(),
            "limits": FloatConverter(),
            "cpu_time": bool_converter,
            "correctness": FloatConverter(),
            "compilation_ok": bool_converter,
            "duration": FloatConverter(),
        }

    def __next__(self):
        converted = super().__next__()
        return Job(**converted)


class RefJobReader(ReaderBase):
    def __init__(self, delimiter=';'):
        super().__init__(delimiter)
        self.converters = {
            "solution_id": HashConverter(),
            "exercise_id": HashConverter(),
            "runtime_id": HashConverter(),
            "worker_group_id": str_passthru,
            "spawn_ts": FloatConverter(),
            "correctness": FloatConverter(),
            "compilation_ok": bool_converter,
            "duration": FloatConverter(),
        }

    def __next__(self):
        converted = super().__next__()
        return RefJob(**converted)


class JobDurationIndex:
    """Structure that holds processed records of jobs divided into classes by exercise and runtime affiliations.

    The structure is used to estimate durations of jobs (by their exercise and runtime).
    """

    def __init__(self):
        self.jobs = {}  # duration (sum and count) per exercise_id
        self.jobs_runtimes = {}  # duration (sum and count) per exercise_id and runtime_id

    def add(self, job):
        """Add another job or ref. job into the index. Its values are immediately processed"""

        if job.exercise_id not in self.jobs:
            self.jobs[job.exercise_id] = {"sum": 0.0, "count": 0.0}
        self.jobs[job.exercise_id]["sum"] += job.duration
        self.jobs[job.exercise_id]["count"] += 1.0

        if job.exercise_id not in self.jobs_runtimes:
            self.jobs_runtimes[job.exercise_id] = {}
        if job.runtime_id not in self.jobs_runtimes[job.exercise_id]:
            self.jobs_runtimes[job.exercise_id][job.runtime_id] = {"sum": 0.0, "count": 0.0}
        self.jobs_runtimes[job.exercise_id][job.runtime_id]["sum"] += job.duration
        self.jobs_runtimes[job.exercise_id][job.runtime_id]["count"] += 1.0

    def estimate_duration(self, exercise_id, runtime_id):
        """Retrieve estimated duration from the index. None is returned, if there are not enough data for the estimate."""

        if exercise_id in self.jobs_runtimes and runtime_id in self.jobs_runtimes[exercise_id]:
            rec = self.jobs_runtimes[exercise_id][runtime_id]
            return rec["sum"] / rec["count"]

        if exercise_id in self.jobs:
            return self.jobs[exercise_id]["sum"] / self.jobs[exercise_id]["count"]

        return None
