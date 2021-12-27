#
# Base classes for important components and helper functions for dynamic loading and instantiation of their implementations.
#

class AbstractMetricsCollector:
    """Base class for all metrics collectors.

    The snapshot() is inoked before every MAPE-K loop invocation to capture workers state periodically.
    The job_finished() is invoked for every job after it is removed from the queue.
    """

    def snapshot(self, ts, workers):
        pass  # an empty placeholder that just declares the interface

    def job_finished(self, job):
        pass  # an empty placeholder that just declares the interface

    def print(self, machine=False, verbose=False):
        """Print the metrics to std. output.

        machine - if true, the output should be printed without any human-readable comments
        verbose - if true, more verbose output is given (if available)
        """
        raise NotImplementedError


class AbstractDispatcher:
    """Base class (interface declaration) for all dispatchers.

    Dispatcher is responsible for assigning jobs into worker queues.
    Dispatcher itslef runs a fixed algorithm, but its behavior may be altered in MAPE-K loop.
    """

    def init(self, ts, workers):
        """Initialize the dispathcher before the first job."""
        pass

    def dispatch(self, job, workers):
        """Assign given job to one of the workers."""
        raise NotImplementedError


class SelfAdaptingStrategy:
    """Represents the controller used for self-adaptation of the system.

    The main part is hidden into mapek() method that represents one iteration of the MAPE-K loop.
    The mapek() does not to perform the entire loop, in some invocations it can perform only data
    gathering for instance.
    """

    def init(self, ts, workers):
        pass

    def mapek(self, ts, workers, job=None):
        """The main interface method called from the simulation.

        The method is called periodically (with job == None) and when new job is spawned
        (right before the job is dispatched).
        The ts holds simulation time and workers is the list of all worker queues.
        """
        pass


def create_component(class_name, constructor_args={}):
    """Create an instance of a component of given name.

    This is used in dynamic loading and component composition based on configuration file.
    class_name - fully qualified name of the class (module.submodule.classname)
    constructor_args - optional dict or list with args passed to constructor
    """
    components = class_name.split('.')
    module = __import__('.'.join(components[:-1]))
    for component in components[1:]:
        module = getattr(module, component)
    class_ = module
    if class_ is None:
        raise RuntimeError("Class {} not found.".format(class_name))

    # create instance
    if constructor_args and isinstance(constructor_args, dict):
        obj = class_(**constructor_args)
    elif constructor_args and isinstance(constructor_args, list):
        obj = class_(*constructor_args)
    else:
        obj = class_()

    return obj
