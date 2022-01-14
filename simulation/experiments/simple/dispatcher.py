from interfaces import AbstractDispatcher


class SimpleDispatcher(AbstractDispatcher):
    """Dispatches new jobs into the shortest active queue."""

    def init(self, ts, workers):
        pass

    def dispatch(self, job, workers):
        active_workers = list(filter(lambda w: w.get_attribute("active"), workers))
        if not active_workers:
            raise RuntimeError("No active workers available, unable to dispatch job.")

        active_workers.sort(key=lambda x: x.jobs_count())
        target = active_workers[0]
        target.enqueue(job)
