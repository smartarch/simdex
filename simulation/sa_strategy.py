class SelfAdaptingStrategy:
    """Represents the algorithms used for self-adaptation of the system.

    The main part is hidden into mapek() method that represents one iteration of the MAPE-K loop.
    The mapek() does not to perform the entire loop, in some invocations it can perform only data
    gathering for instance.
    """

    def init(self, ts, workers):
        # At the beginning, make only the first worker active
        for worker in workers:
            worker.set_attribute("active", False)
        workers[0].set_attribute("active", True)

    def mapek(self, ts, workers):
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
        if active > 1 and overloaded == 0 and empty:
            empty[0].set_attribute("active", False)  # put idle worker to sleep
        elif inactive and overloaded > 0:
            inactive[0].set_attribute("active", True)  # wake inactive worker
