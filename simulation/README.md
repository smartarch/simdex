# ReCodEx Backend Simulator

This readme presents some internal details of the Simdex, a simulator of [ReCodEx](https://github.com/recodex) backend that replays its [compiled workload logs](https://github.com/smartarch/simdex/tree/main/data). For details on how to execute the `main.py` script, please refer to the [main project readme](https://github.com/smartarch/simdex#getting-started).


## Overview

The simulator algorithm is wrapped in the `Simulation` class in [`simulation.py`](https://github.com/smartarch/simdex/blob/main/simulation/simulation.py). It expects to be called (its public routine `run`) once for each job by the main loop and then with `job=None` at the end. The simulation class is also responsible for assembling the simulation components from the configuration Yaml file.

Each job is represented by an instance of the `Job` data class (reference solution jobs use the `RefJob` data class). All necessary helper tools for loading data and handling the jobs are in [`jobs.py`](https://github.com/smartarch/simdex/blob/main/simulation/jobs.py). Please note that the readers are built to read jobs one by one (the reader implements an iterator interface), so the whole dataset does not have to be present in memory. On the other hand, this requires that simulated datasets are sorted by the job spawning time.

### Workers and Queues

The backend workers are represented by worker queues in the simulator (i.e., when we are talking about workers or queues, it means the same). Each queue is a simple FIFO that processes the jobs in the exact order in which the jobs are put forth. Job, which is currently at the front of the queue, is being executed (virtually) by the worker. The execution `duration` is taken from the dataset logs. Once the job is finished (stays long enough in the queue), it is removed.

The most important method is
```python
def enqueue(self, job):
```
which places new job into the queue. Please note that the `job` object is altered immediately (its finish timestamp is computed based on the last job in the queue).

Each queue has attributes attached. They are identified by `name` (a string key) and their value may be anything that Python can handle. The attributes are accessed by simple getter and setter:
```python
def get_attribute(self, name):
def set_attribute(self, name, value):
```

Finally, the
```python
def jobs_count(self):
```
will return the number of jobs actually present in the queue (including the front job, which is currently "*running*").


### Implemented experiments

As an example, we provide two scenarios with 7 configurations (`.yaml` files) prepared to be launched.

The **simple** scenario is based on the assumption that the workers can be suspended when the system is underutilized to save power. It uses only the worker queue attributes (namely the `active` attribute) to control, which workers are running and which are suspended. At least one worker needs to be running at all times.

- [`simple-no-sa-1worker.yaml`](https://github.com/smartarch/simdex/blob/main/simulation/experiments/simple-no-sa-1worker.yaml) -- baseline with no self-adaptation (using single worker the whole time)
- [`simple-no-sa-4worker.yaml`](https://github.com/smartarch/simdex/blob/main/simulation/experiments/simple-no-sa-4worker.yaml) -- baseline with no self-adaptation (using 4 workers the whole time)
- [`simple-self-adaptive.yaml`](https://github.com/smartarch/simdex/blob/main/simulation/experiments/simple-self-adaptive.yaml) -- self-adaptive strategy that de/activates workers (1 to 4) based on the number of jobs in the queues. If there is at least one queue with more than 1 job and at least one worker is not running, it is activated. Otherwise, it there are at least two active empty queues, one of them is deactivated.

All configurations of this scenario are evaluated by `PowerMetricsCollector` and `JobDelayMetricsCollector` (see below).


The **user_experience** scenario demonstrates application of machine learning. It applies self-adaptive strategy to improve user experience regarding the latency of the jobs. The main assumption is that short jobs should be evaluated interactively whilst long-running jobs may be delayed since the user will not wait for them anyway.

The dispatcher tries to estimate the duration of each job and place them into appropriate queue. Three queues are dedicated for jobs that are assumed to take less than `30s`, the fourth queue is open for all jobs. If more than one queue is appropriate for a job, the shortest one (with the least jobs) is used.

The self-adaptive strategy does not alter the configuration of the queues, but only adjusts the model used for predicting job durations.

- [`user_experience-no-sa.yaml`](https://github.com/smartarch/simdex/blob/main/simulation/experiments/user_experience-no-sa.yaml) -- baseline without self-adaptive module; uses half of the job time limits as the duration estimate
- [`user_experience-oracle.yaml`](https://github.com/smartarch/simdex/blob/main/simulation/experiments/user_experience-oracle.yaml) -- special baseline that violates simulation causality (uses the actual duration as a prediction); this simulates the ultimate oracle that could precisely predict all the jobs accurately (i.e., the theoretical limit of this scenario)
- [`user_experience.yaml`](https://github.com/smartarch/simdex/blob/main/simulation/experiments/user_experience.yaml) -- self-adaptive approach that employs simple statistical model; computes an average of durations of past jobs (categorized by exercise ID and runtime ID)
- [`user_experience_nn.yaml`](https://github.com/smartarch/simdex/blob/main/simulation/experiments/user_experience_nn.yaml) -- self-adaptive approach that integrates [TensorFlow](https://www.tensorflow.org/) and implements the estimator using simple neural network (as a regression predictor)

All configurations of this scenario are evaluated by `JobDelayMetricsCollector` and `UserExperienceMetricsCollector` (see below).


### Predefined metrics

There are three predefined metric collectors

`PowerMetricsCollector` (default module) -- computes total time the queues were active (i.e., power consumption of the workers); it is printed out as relative value (1.0 = one worker queue was active on average)

`JobDelayMetricsCollector` (default module) -- computes average and maximal job delay

`UserExperienceMetricsCollector` (user_experience module) -- computes user experience by dividing jobs into three categories:
- *on time* -- minimal or no delay
- *delayed* -- noticeable, yet still acceptable delay
- *late* -- significant (potentially problematic) delay

The output is three numbers -- how many of the jobs felt into each category. The categories are based on duration estimates and multiplication constants (e.g., if job delay is less than `1.5x` its expected duration, it is considered on time). The expected durations are computed from reference solutions jobs (i.e., the `--refs` option must be used when executing the experiment with this metric). 


---


## Creating new experiments

A quick guide how to create your own experiments using the simulator. Every experiment has to have a configuration `.yaml` file, which holds the initial parameters for the queues and controls the component instantiation process. You may use one of the attached examples as a starting point and modify it.


### Yaml config file

The configuration file is a collection that holds the following root keys:
- `workers` -- either an integer (number of workers) or a list of collections, each collection is used as an initial set of attributes for one worker
- `dispatcher` -- component specification for the Dispatcher module
- `sa_strategy` -- component specification for the SA strategy module
- `period` -- an integer that indicates, how often is the `do_adapt` method of the SA strategy invoked (in seconds of the simulation time)
- `metrics` -- a list of components specifications of Metric modules (all listed modules are used for analysis and their results are printed at the end)

A component specification value is either a string (a full name of the component class), for instance `experiments.simple.dispatcher.SimpleDispatcher` refers to a class `SimpleDispatcher` in `dispatcher.py` file in the `experiments/simple` subdirectory, or a collection which holds:
- `class` - a full name of the component class as explained above
- `args` - arguments passed to the constructor of that class when it is being instantiated
The `args` can be stored either as a list (positional arguments) or collection (named arguments).

All arguments are treated as static constants; however, in some cases, we need to express the injection pattern as well. For this purpose, we define *injected arguments* as arguments that are replaced with explicit values before being passed to the constructor. The injected arguments are always strings prefixed with `@@`. At the moment, the simulator implements the following injections:
- `@@ref_jobs` - injects the list of loaded reference solution jobs (requires that `--refs` command line option is used; otherwise the simulation fails)


### Dispatcher and strategy classes

Both the dispatcher and self-adaptive strategy are classes that must implement interface prescribed in [`interfaces.py`](https://github.com/smartarch/simdex/blob/main/simulation/interfaces.py) --- `AbstractDispatcher` and `AbstractSelfAdaptingStrategy`.

Namely, the **dispatcher** class must implement 
```python
def dispatch(self, job, workers):
```
method which is responsible for job dispatching. It gets a list of all worker queues, selects the right one and places the job inside by calling `worker.enqueue(job)`.

Optionally, it may implement
```python
def init(self, ts, workers):
```
method that is called once when the dispatcher is being initialized. The `ts` holds timestamp when the simulation starts (in virtual time).

The **self-adapting strategy** must implement
```python
def do_adapt(self, ts, dispatcher, workers, job=None):
```
method, which is the generic interface for invoking MAPE-K loop (or similar concept). Whether actual `do_adapt` call performs only the monitoring step, or whether it performs the entire loop including the execution of modifications is completely up to the implemented SA component.

This method is invoked periodically by the simulator (period is given in the configuration) and right before dispatching the job. The periodic calls have `job=None`, otherwise `job` holds the job that is about to be dispatched. The `dispatcher` argument holds the actual dispatcher object, so that SA strategy may execute modifications via whatever interface the author of the experiment has defined between these two components.

Similarly to the dispatcher, SA strategy may implement
```python
def init(self, ts, dispatcher, workers):
```
method that is invoked once at the beginning.

Please note that both dispatcher and SA strategy should refrain from accessing `duration`, `correctness`, and `compilation_ok` properties of the `Job` data class before the job is actually processed (i.e., after it has its `finish_ts` time computed and current simulation time is greater than `finish_ts`).


### Defining new metrics

Metric collectors are components that implement an interface defined by `AbstractMetricsCollector`. They may implement two collecting routines.

```python
def snapshot(self, ts, workers):
```
The snapshots are taken periodically, right before the `do_adapt` method of SA strategy is invoked. This method may be used for periodic monitoring of the state of the worker queues (e.g., whether they are active or not).

```python
def job_finished(self, job):
```
This callback is invoked for every job right after it is finished and removed from the worker queue. The collector can use `spawn_ts`, `start_ts`, or even `finish_ts` to gather data regarding the delay of the job.

Finally, the metric component must provide a printing method that outputs the findings.
```python
def print(self, machine=False, verbose=False):
```
The two flags may affect the printing data. The `machine` flag indicates that the output will be collected and processed by a script (probably when a batch of simulations is being executed). The `verbose` flag indicates that the user desires a more detailed output. Both flags may be ignored if not relevant for a particular metric collector.
