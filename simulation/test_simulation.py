"""Run from this folder: python -m unittest test_simulation"""
import unittest

from jobs import Job
from simulation import Simulation
from metrics.default import JobDelayMetricsCollector, PowerMetricsCollector

CONFIG = {"workers": [{"active": True}], "dispatcher": "experiments.simple.dispatcher.SimpleDispatcher"}


def job(spawn_ts, duration):
    return Job(solution_id=1, group_id=1, tlgroup_id=1, exercise_id=1, runtime_id=1, worker_group_id="", user_id=1,
               spawn_ts=spawn_ts, limits=0.0, cpu_time=True, correctness=1.0, compilation_ok=True, duration=duration)


class EmptyRunTest(unittest.TestCase):
    def test_a_run_without_jobs_ends_quietly(self):
        """main.py ends every run with run(None), also when the log had no jobs (or --limit 0)."""
        Simulation(CONFIG).run(None)


class StartAtZeroTest(unittest.TestCase):
    """A log whose times are relative (the first job at 0.0) is a run like any other."""

    def test_the_run_is_started_once(self):
        starts = []

        class Counting(JobDelayMetricsCollector):
            def snapshot(self, ts, workers):
                starts.append(ts)

        sim = Simulation(CONFIG)
        sim.register_metrics(Counting())
        sim.run(job(0.0, 5.0))
        sim.run(job(0.0, 5.0))
        sim.run(job(10.0, 5.0))
        self.assertEqual(starts, [0.0], "one snapshot at the start, none again before the first period is over")

    def test_the_first_period_counts_as_uptime(self):
        power = PowerMetricsCollector()
        sim = Simulation(CONFIG)
        sim.register_metrics(power)
        sim.run(job(0.0, 30.0))
        sim.run(None)
        self.assertEqual(power.get_measured_period(), 60.0)
        self.assertEqual(power.get_relative_uptime(), 1.0)
