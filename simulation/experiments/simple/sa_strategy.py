from interfaces import AbstractSelfAdaptingStrategy


class SimpleSelfAdaptingStrategy(AbstractSelfAdaptingStrategy):
    """Represents a simple SA controller for activation/deactivation of queues based on current workload.

    Activates suspended worker queues when the system gets staturated, deactivates queues that are idle.
    """

    def init(self, ts, dispatcher, workers):
        # At the beginning, make only the first worker active
        for worker in workers:
            worker.set_attribute("active", False)
        workers[0].set_attribute("active", True)

    def do_adapt(self, ts, dispatcher, workers, job=None):
        # analyse the state of the worker queues
        active = 0
        overloaded = 0
        empty = []  # active yet empty work queues
        inactive = []  # inactive work queues
        for worker in workers:
            if worker.get_attribute("active"):
                active += 1
                if worker.jobs_count() == 0:
                    empty.append(worker)
                elif worker.jobs_count() > 1:
                    overloaded += 1
            else:
                inactive.append(worker)

        # take an action if necessary
        if len(empty) > 1 and overloaded == 0 and empty:
            empty[0].set_attribute("active", False)  # put idle worker to sleep
        elif inactive and overloaded > 0:
            inactive[0].set_attribute("active", True)  # wake inactive worker
