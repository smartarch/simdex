from interfaces import SelfAdaptingStrategy


class CategorySelfAdaptingStrategy(SelfAdaptingStrategy):
    """Represents the a simple SA controller.

    Activates suspended worker queues when the system gets staturated,
    deactivates queues that are idle.
    """

    def __init__(self, max_long_queues, ref_jobs):
        self.max_long_queues = max_long_queues
        self.ref_jobs = ref_jobs[:]
        self.ref_jobs.reverse()

    def _update_dispatcher(self, ts, dispatcher):
        while len(self.ref_jobs) > 0 and self.ref_jobs[-1].spawn_ts + self.ref_jobs[-1].duration <= ts:
            job = self.ref_jobs.pop()
            if job.compilation_ok:
                dispatcher.add_ref_job(job)

    def init(self, ts, dispatcher, workers):
        # At the beginning, make only the first worker active
        for worker in workers:
            worker.set_attribute("active", True)
            worker.set_attribute("limit", 30.0)
        workers[0].set_attribute("limit", None)

        self._update_dispatcher(ts, dispatcher)

    def mapek(self, ts, dispatcher, workers, job=None):
        self._update_dispatcher(ts, dispatcher)
        if (job and job.compilation_ok):
            dispatcher.add_ref_job(job)
