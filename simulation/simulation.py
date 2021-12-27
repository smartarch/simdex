from workers import WorkerQueue
from interfaces import create_component


def _create_instance(config):
    """Helper function that creates instance of a component from configuration."""
    if isinstance(config, dict):
        if ("class" not in config):
            raise RuntimeError("Attribute class is missing from component configuration descriptor.")
        if ("args" not in config or (not isinstance(config["args"], dict) and not isinstance(config["args"], list))):
            raise RuntimeError("Invalid component constructor args given in configuration descriptor.")
        return create_component(config["class"], config["args"])
    else:
        return create_component(config)  # config is a string holding the class name


class Simulation:
    """Main simulation class. Wraps the algorithm and acts as component container."""

    def __init__(self, configuration):
        # load parameters from configuration and instantiate necessary components
        self.metrics = []
        if "metrics" in configuration:
            for metric in configuration["metrics"]:
                self.metrics.append(_create_instance(metric))

        self.dispatcher = _create_instance(configuration["dispatcher"])
        if "sa_strategy" in configuration:
            self.sa_strategy = _create_instance(configuration["sa_strategy"])

        # how often MAPE-K is called (in seconds)
        self.sa_period = float(configuration["period"]) if "period" in configuration else 60.0  # one minute is default

        # simulation state (worker queues)
        if "workers" not in configuration:
            raise RuntimeError("Workers are not specified in the configuration file.")

        self.workers = []
        if isinstance(configuration["workers"], list):
            for worker_attrs in configuration["workers"]:
                self.workers.append(WorkerQueue(**worker_attrs))
        else:
            for i in range(int(configuration["workers"])):
                self.workers.append(WorkerQueue())

        # remaining simulation variables
        self.ts = 0.0  # simulation time
        self.next_mapek_ts = 0.0  # when the next MAPE-K call is scheduled

    def register_metrics(self, *metrics):
        """Additional metrics components may be registered via this method (mainly for debugging purposes)."""
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
            if self.sa_strategy:  # mapek out of order (just before a job is dispatched)
                self.sa_strategy.mapek(self.ts, self.workers, job)
            self.dispatcher.dispatch(job, self.workers)
        else:
            # let's wrap up the simulation
            end_ts = self.ts
            for worker in self.workers:
                worker_end_ts = worker.get_finish_ts()
                if worker_end_ts:
                    end_ts = max(end_ts, worker.get_finish_ts())
            self.__advance_time(end_ts + self.sa_period)
