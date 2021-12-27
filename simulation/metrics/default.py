from interfaces import AbstractMetricsCollector


class PowerMetricsCollector(AbstractMetricsCollector):
    """Metrics collector that computes total uptime of all workers (i.e., power consumption)."""

    def __init__(self):
        self.last_ts = None
        self.period = 0.0  # measured period of time
        self.uptime = 0.0  # total sum of time when servers were up

    def snapshot(self, ts, workers):
        if self.last_ts:
            dt = max(ts - self.last_ts, 0)
            active_workers = len(list(filter(lambda w: w.get_attribute("active"), workers)))
            self.period += dt
            self.uptime += dt * float(active_workers)
        self.last_ts = ts

    def print(self):
        print("Simulation time: {} s, relative workers uptime: {}".format(
            self.get_measured_period(), self.get_relative_uptime()))

    def get_measured_period(self):
        """Duration of the entire measurement."""
        return self.period

    def get_relative_uptime(self):
        """Relative uptime of the workers (e.g., 2.0 means two workers were up the whole time on the average)."""
        return self.uptime / self.period if self.period > 0.0 else 0.0


class JobDelayMetricsCollector(AbstractMetricsCollector):
    """Metrics collector that computes basic delay statistics (average, maximum) for all jobs."""

    def __init__(self):
        self.jobs = 0
        self.total_delay = 0.0
        self.max_delay = 0.0

    def job_finished(self, job):
        delay = job.start_ts - job.spawn_ts
        self.total_delay += delay
        self.max_delay = max(self.max_delay, delay)
        self.jobs += 1

    def print(self):
        print("Total jobs: {}, avg. delay: {}, max. delay: {}".format(
            self.get_jobs(), self.get_avg_delay(), self.get_max_delay()))

    def get_jobs(self):
        return self.jobs

    def get_max_delay(self):
        return self.max_delay

    def get_avg_delay(self):
        return self.total_delay / float(self.jobs) if self.jobs else 0.0
