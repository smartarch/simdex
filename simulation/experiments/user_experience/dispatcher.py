from interfaces import AbstractDispatcher
from jobs import JobDurationIndex


def duration_filter(est_duration):
    def fnc(w):
        limit = w.get_attribute("limit")
        return limit is None or limit >= est_duration
    return fnc


class JobCategoryDispatcher(AbstractDispatcher):
    """Dispatcher that tries to improve user experience by placing long jobs in a separate queue.

    The estimation whether a job will be short or long is based on jobs that were already evaluated
    (both regular and ref.). The SA strategy is responsible for filling data for the estimator.
    """

    def __init__(self):
        # the dispatching algorithm only reads the index, SA strategy is responsible for filling the data
        self.duration_index = JobDurationIndex()

    def init(self, ts, workers):
        pass

    def dispatch(self, job, workers):
        # we need to estimate the duration of the job first (! no peeking to job.duration !)
        estimate = self.duration_index.estimate_duration(job.exercise_id, job.runtime_id)
        if estimate is None:
            estimate = job.limits / 2.0

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

    def add_ref_job(self, job):
        """External interface for SA strategy (which can add jobs to index to modify dispatcher behavior)."""
        self.duration_index.add(job)


class OracleJobCategoryDispatcher(AbstractDispatcher):
    """Same as JobCategoryDispatcher but with oracle that precisely forsees the job duration.

    This dispatcher can be used to determine the performance of theoretical ultimate model that would
    predict job durations precisely.
    """

    def __init__(self):
        # the dispatching algorithm only reads the index, SA strategy is responsible for filling the data
        self.duration_index = JobDurationIndex()

    def init(self, ts, workers):
        pass

    def dispatch(self, job, workers):
        # the dispatcher is cheating here, the duration would not be available until the job is completed !!!
        estimate = job.duration

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

    def add_ref_job(self, job):
        """External interface for SA strategy (which can add jobs to index to modify dispatcher behavior)."""
        self.duration_index.add(job)
