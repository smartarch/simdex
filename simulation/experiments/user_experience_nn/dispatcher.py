from interfaces import AbstractDispatcher


def duration_filter(est_duration):
    def fnc(w):
        limit = w.get_attribute("limit")
        return limit is None or limit >= est_duration
    return fnc


class JobCategoryDispatcher(AbstractDispatcher):
    def __init__(self):
        self.predictor = None

    def init(self, ts, workers):
        pass

    def dispatch(self, job, workers):
        # we need to estimate the duration of the job first (! no peeking to job.duration !)
        if self.predictor is None:
            estimate = job.limits / 2.0
        else:
            estimate = self.predictor(job)

        # get all workers marked as active
        active_workers = list(filter(lambda w: w.get_attribute("active"), workers))
        if not active_workers:
            raise RuntimeError("No active workers available, unable to dispatch job.")

        # select workers where the job would fit (estimate duration is under worker limit)
        best_workers = list(filter(duration_filter(estimate), active_workers))
        if len(best_workers) == 0:
            best_workers = active_workers  # fallback, if no worker passes the limit

        best_workers.sort(key=lambda w: w.jobs_count())
        target = best_workers[0]
        target.enqueue(job)

    def set_predictor(self, predictor):
        self.predictor = predictor
