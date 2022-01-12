# SIMDEX: ReCodEx Backend Simulator and Dataset

[![Build Status](https://github.com/smartarch/recodex-dataset/workflows/CI/badge.svg)](https://github.com/smartarch/recodex-dataset/actions)

This repository contains:
- A simulator of a job-processing backend of a real system enhanced with self-adaptive interface which allows testing various strategies and scenarios.
- A dataset comprise a log of workloads metadata of real users collected from our instance of [ReCodEx](https://github.com/recodex) (a system for evaluation of coding assignments). The simulator can replay the logs which provides rather unique evaluation based on real data.


## Getting started

The repository is ready to be used immediately as is (just clone it). You only need to have Python 3.7+ installed. If you are using Python virtual environment, do not forget to adjust paths to `python` and `pip` executables.

Install basic dependencies:
```
$> cd ./simulation
$> pip install -r ./requirements.txt
```

Kick the tires (check the scripts are running):
```
$> python ./main.py --config ./experiments/simple-no-sa-1worker.yaml ../data/release01-2021-12-29/data-sample.csv

Total jobs: 1000, avg. delay: 0.14171400094032288, max. delay: 19.865999937057495
Simulation time: 1018260.0 s, relative workers uptime: 1.0
```


## Running prepared experiments

Most of the following experiments require less than 30s to process on common desktop computers and laptops.


### Simple scenario (optimizing power consumption)

The *simple* scenario demonstrates backend with up to 4 queues which can be activated/deactivated based on the system workload. At least one queue must be active at all times to ensure reasonable latency for idle system. Presented strategies are evaluated by two metrics:
- job delay (average and maximal time jobs had to wait in queues)
- relative uptime (consumed energy relativized to consumption of one worker)

Using 1 worker with no self-adapting strategy (first baseline):
```
$> python ./main.py --config ./experiments/simple-no-sa-1worker.yaml ../data/release01-2021-12-29/data.csv.gz

Total jobs: 398302, avg. delay: 311.65797756387946, max. delay: 36544.78699851036
Simulation time: 133815360.0 s, relative workers uptime: 1.0
```

Using 4 workers with no self-adapting strategy (second baseline):
```
$> python ./main.py --config ./experiments/simple-no-sa-4worker.yaml ../data/release01-2021-12-29/data.csv.gz

Total jobs: 398302, avg. delay: 9.12266597718005, max. delay: 11129.636000156403
Simulation time: 133815360.0 s, relative workers uptime: 4.0
```

Using self-adaptive strategy that changes the number of active queues based on current workload:
```
$> python ./main.py --config ./experiments/simple-self-adaptive.yaml ../data/release01-2021-12-29/data.csv.gz

Total jobs: 398302, avg. delay: 14.168042374734924, max. delay: 13284.132000207901
Simulation time: 133815360.0 s, relative workers uptime: 1.0498902368158634
```

The SA version demonstrates only slight increase in job delays, but the power consumption is only `5%` higher with respect to the minimal scenario with 1 worker.


### User-experience scenario (using machine-learning)

TODO


## More reading

- [Simulator overview and quick guide to creating your own experiments](/smartarch/simdex/tree/main/simulation)
- [Dataset details](/smartarch/simdex/tree/main/data)
