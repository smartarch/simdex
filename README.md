# SIMDEX: ReCodEx Backend Simulator and Dataset

[![Build Status](https://github.com/smartarch/recodex-dataset/workflows/CI/badge.svg)](https://github.com/smartarch/recodex-dataset/actions)

This repository contains an artifact described in a paper called *Simdex: A Simulator of a Real Self-adaptive Job-dispatching System Backend*, which was submitted to SEAMS conference, and it comprises:
- A simulator of a job-processing backend of a real system enhanced with a self-adaptive interface which allows testing various strategies and scenarios.
- A dataset comprises a log of workloads metadata of real users collected from our instance of [ReCodEx](https://github.com/recodex) (a system for evaluation of coding assignments). The simulator can replay the logs, which provides rather unique evaluation based on real data.


## Getting started

The repository is ready to be used immediately as is (just clone it). You only need to have Python 3.7+ installed. If you are using Python virtual environment, do not forget to adjust paths to `python3` and `pip3` executables.

Install basic dependencies:
```
$> cd ./simulation
$> pip3 install -r ./requirements.txt
```

Quick check the scripts are running (on dataset sample):
```
$> python3 ./main.py --config ./experiments/simple-no-sa-1worker.yaml ../data/release01-2021-12-29/data-sample.csv

Total jobs: 1000, avg. delay: 0.14171400094032288, max. delay: 19.865999937057495
Simulation time: 1018260.0 s, relative workers uptime: 1.0
```


## Running prepared experiments

The simulator entry point is `main.py` script which is invoked as:
```
$> python3 ./main.py --config <path-to-config-file> [options] <path-to-data-file>
```
The config is in a `.yaml` file that is used to initialize the simulation. [Config files for our examples](https://github.com/smartarch/simdex/tree/main/simulation/experiments) are already in this repository and additional information can be found in the [quick guide](https://github.com/smartarch/simdex/tree/main/simulation).
The data file is `.csv` or `.csv.gz` file that must be in the same format as [our dataset](https://github.com/smartarch/simdex/tree/main/data).

Additional options recognized by the main script:
- `--refs` option holds one string value -- a path to reference solutions data file (`.csv` or `.csv.gz`), please note that ref. solutions must be loaded for some experiments
- `--limit` option holds one integer, which is a maximal number of rows loaded from the data file (allows to restrict the number of simulated jobs)
- `--progress` is a bool flag that enables progress printouts to std. output (particularly useful for ML experiments that take a long time to process)

The examples of experiments provided with the simulator can be invoked as follows. Most of the following experiments require less than 30s to process on common desktop computers and laptops.


### Simple scenario (optimizing power consumption)

The *simple* scenario demonstrates backend with up to 4 queues which can be activated/deactivated based on the system workload. At least one queue must be active at all times to ensure reasonable latency for idle system. Presented strategies are evaluated by two metrics:
- job delay (average and maximal time jobs had to wait in queues)
- relative uptime (consumed energy relativized to consumption of one worker)

Using 1 worker with no self-adapting strategy (first baseline):
```
$> python3 ./main.py --config ./experiments/simple-no-sa-1worker.yaml ../data/release01-2021-12-29/data.csv.gz

Total jobs: 398302, avg. delay: 311.65797756387946, max. delay: 36544.78699851036
Simulation time: 133815360.0 s, relative workers uptime: 1.0
```

Using 4 workers with no self-adapting strategy (second baseline):
```
$> python3 ./main.py --config ./experiments/simple-no-sa-4worker.yaml ../data/release01-2021-12-29/data.csv.gz

Total jobs: 398302, avg. delay: 9.12266597718005, max. delay: 11129.636000156403
Simulation time: 133815360.0 s, relative workers uptime: 4.0
```

Using self-adaptive strategy that changes the number of active queues based on current workload:
```
$> python3 ./main.py --config ./experiments/simple-self-adaptive.yaml ../data/release01-2021-12-29/data.csv.gz

Total jobs: 398302, avg. delay: 14.168042374734924, max. delay: 13284.132000207901
Simulation time: 133815360.0 s, relative workers uptime: 1.0498902368158634
```

The SA version demonstrates only slight increase in job delays, but the power consumption is only `5%` higher with respect to the minimal scenario with 1 worker.


### User-experience scenario (using machine-learning)

All the following experiments also require job logs of reference solutions (the `--refs` argument).

The first baseline does not use a self-adapting strategy, so job test limits (divided by 2) are used as the rough estimate.
```
$> python3 ./main.py --config ./experiments/user_experience-no-sa.yaml --refs ../data/release01-2021-12-29/ref-solutions.csv ../data/release01-2021-12-29/data.csv.gz

Total jobs: 398302, avg. delay: 89.47350952287265, max. delay: 34924.11799955368
Total jobs: 398302, on time: 382615, delayed: 2461, late: 13226
```

The second baseline uses oracle instead of machine-learning model. The oracle represents ultimate predictor since it breaches simulation causality and reads the job duration value before the job is actually processed. This experiment is not realistic, but it helps us find the best possible (theoretical) performance for this particular setup.
```
$> python3 ./main.py --config ./experiments/user_experience-oracle.yaml --refs ../data/release01-2021-12-29/ref-solutions.csv ../data/release01-2021-12-29/data.csv.gz

Total jobs: 398302, avg. delay: 52.17845850431202, max. delay: 34611.763999938965
Total jobs: 398302, on time: 388244, delayed: 1940, late: 8118
```

The first machine-learning model based on simple statistics of the history of jobs:
```
$> python3 ./main.py --config ./experiments/user_experience.yaml --refs ../data/release01-2021-12-29/ref-solutions.csv ../data/release01-2021-12-29/data.csv.gz

Total jobs: 398302, avg. delay: 62.089308951997175, max. delay: 34752.292999982834
Total jobs: 398302, on time: 387502, delayed: 1928, late: 8872
```

This model exhibits significant improvement over the non-SA baseline and we can also see it is not that far from the optimum established by the oracle baseline.

> The last experiment uses [TensorFlow](https://www.tensorflow.org/) framework for machine learning. We have placed this requirement separately, since TensorFlow is rather large and takes some time to install. However, it can be installed easily using pip as follows.

```
$> pip3 install numpy tensorflow
```

The experiment was tested with TensorFlow 2.7. You may verify your version as 
```
$> python3
>>> import tensorflow as tf
>>> print(tf.version.VERSION)
2.7.0
```

The experiment with neural network duration estimator takes significantly more time than the previous experiments (even with a GPU). It is recommended to use `--progress` switch that makes the script print out a dot `.` after every `1000` jobs. 
```
$> python3 ./main.py --config ./experiments/user_experience_nn.yaml --refs ../data/release01-2021-12-29/ref-solutions.csv --progress ../data/release01-2021-12-29/data.csv.gz
..............................................................................................................................................................................................................................................................................................................................................................................................................
Total jobs: 398302, avg. delay: 55.39687156005332, max. delay: 34723.453000068665
Total jobs: 398302, on time: 387216, delayed: 1928, late: 9158
```

The NN-model exhibits only slightly worse performance than the simple statistical model; however, the main objective was to demonstrate the applicability of machine-learning methods in our simulator. It might be possible to improve this model further. We would like to also mention that this model is not completely deterministic as the NN is trained by partially stochastic algorithms. I.e., subsequent runs may yield slightly different results.


## More reading

- [Simulator overview and quick guide to creating your own experiments](https://github.com/smartarch/simdex/tree/main/simulation)
- [Dataset details](https://github.com/smartarch/simdex/tree/main/data)
