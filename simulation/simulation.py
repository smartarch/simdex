from workers import WorkerQueue
from dispatcher import Dispatcher
from sa_strategy import SelfAdaptingStrategy


class Simulation:
    """Main simulation class. Wraps the algorithm and acts as component container."""

    def __init__(self, configuration):
        # TODO load actual class names from configuration
        self.metrics = []
        self.dispatcher = Dispatcher()
        self.sa_strategy = SelfAdaptingStrategy()
        self.sa_period = 60.0  # how often MAPE-K is called (in seconds)

        # simulation state
        self.workers = [
            WorkerQueue(active=True),
            WorkerQueue(active=True),
            WorkerQueue(active=False),
            WorkerQueue(active=False),
        ]

        self.ts = 0.0  # simulation time
        self.next_mapek_ts = 0.0

    def register_metrics(self, *metrics):
        for m in metrics:
            self.metrics.append(m)

    def __start_simulation(self, ts):
        """Just-in-time initialization."""
        self.ts = ts
        self.next_mapek_ts = ts + self.sa_period

        # initialize injected components
        self.dispatcher.init(self.ts, self.workers)
        if self.sa_strategy:
            self.sa_strategy.init(self.ts, self.workers)

        # take an initial snapshot by the metrics collectors
        for metric in self.metrics:
            metric.snapshot(self.ts, self.workers)

    def __advance_time_in_workers(self):
        for worker in self.workers:
            done = worker.advance_time(self.ts)
            for job in done:
                for metric in self.metrics:
                    metric.job_finished(job)

    def __advance_time(self, ts):
        """Advance the simulation to given point in time, invoking MAPE-K periodically."""
        if self.metrics or self.sa_strategy:
            while self.next_mapek_ts < ts:
                self.ts = self.next_mapek_ts
                self.__advance_time_in_workers()

                # take a measurement for statistics
                for metric in self.metrics:
                    metric.snapshot(self.ts, self.workers)

                # invoke MAPE-K, the strategy can read and possibly update worker queues
                if self.sa_strategy:
                    self.sa_strategy.mapek(self.ts, self.workers)
                self.next_mapek_ts += self.sa_period

        self.ts = ts
        self.__advance_time_in_workers()

    def run(self, job):
        """Advance the simulation up to the point when new job is being spawned and add it to the queues.

        The simulation may perform many internal steps (e.g., invoke MAPE-K multiple times) in one run invocation.
        If job is None, the run will perform final steps and conclude the simulation.
        """

        # first run, initialize simulation
        if self.ts == 0.0:
            self.__start_simulation(job.spawn_ts)

        if job:
            # regular simulation step
            self.__advance_time(job.spawn_ts)
            self.dispatcher.dispatch(job, self.workers)
        else:
            # let's wrap up the simulation
            end_ts = self.ts
            for worker in self.workers:
                worker_end_ts = worker.get_finish_ts()
                if worker_end_ts:
                    end_ts = max(end_ts, worker.get_finish_ts())
            self.__advance_time(end_ts + self.sa_period)
