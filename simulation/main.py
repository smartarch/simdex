#!/usr/bin/env python3

import argparse

from jobs import Reader
from simulation import Simulation
from metrics import JobDelayMetricsCollector, PowerMetricsCollector

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", type=str, help="Path to the input .csv or .csv.gz file with jobs log.")
    parser.add_argument("--limit", type=int, default=1000000000,
                        help="Maximal number of jobs to be read from the input file.")
    # parser.add_argument("--config", type=str, help="Path to yaml file with simulation configuration.")
    args = parser.parse_args()

    reader = Reader()
    reader.open(args.input_file)

    simulation = Simulation({})
    job_delay = JobDelayMetricsCollector()
    power = PowerMetricsCollector()
    simulation.register_metrics(job_delay, power)

    limit = args.limit
    for job in reader:
        if limit <= 0:
            break
        simulation.run(job)
        limit -= 1

    simulation.run(None)  # end the simulation
    reader.close()

    # print out measured statistics
    for metric in simulation.metrics:
        metric.print()
