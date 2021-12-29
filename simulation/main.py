#!/usr/bin/env python3

import argparse
import ruamel.yaml as yaml
from jobs import JobReader, RefJobReader
from simulation import Simulation


def get_configuration(config_file):
    with open(config_file, "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as e:
            print("Simulation config file {} is not in YAML format.".format(config_file))
            print(e)
            exit()


def load_reference_jobs(path):
    reader = RefJobReader()
    reader.open(path)
    jobs = [job for job in reader]
    reader.close()
    return jobs


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", type=str, help="Path to the input .csv or .csv.gz file with jobs log.")
    parser.add_argument("--limit", type=int, default=1000000000,
                        help="Maximal number of jobs to be read from the input file.")
    parser.add_argument("--config", type=str, required=True, help="Path to yaml file with simulation configuration.")
    parser.add_argument("--refs", type=str, required=False,
                        help="Path to .csv or .csv.gz file with log with jobs of reference solutions.")
    args = parser.parse_args()

    # initialize the system
    configuration = get_configuration(args.config)
    ref_jobs = load_reference_jobs(args.refs) if (args.refs) else None
    simulation = Simulation(configuration, ref_jobs)

    reader = JobReader()
    reader.open(args.input_file)

    # read data and run the simulation
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
