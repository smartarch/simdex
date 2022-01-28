# Dataset

The dataset comprises job logs from the ReCodEx system that can be loaded and replayed by our simulator.


## Student solutions (main dataset)

The main dataset comprises solutions submitted by students.
The gzip-compressed CSV file `data.csv.gz` and small sample file `data-sample.csv` have both the following columns:

- `submission_id` - globally unique identifier (not relevant for the simulation)
- `solution_id` - identifier of the solution (i.e., source code yielded by user); one solution may have multiple submissions if it is re-evaluated by a teacher or an administrator 
- `group_id` - group in which the student submits the solution (roughly equivalent of a real group of students attending one labs)
- `tlgroup_id` - top-level group that aggregates all groups of one (or few closely related) course(s)
- `exercise_id` - to which exercise the solution is addressed (solutions of one exercise are often similar in the duration)
- `runtime_id` - programming language (and its runtime environment configuration) of the solution (one exercise may be solved in different languages/runtimes)
- `worker_group_id` - defines a set of workers which could evaluate the solution (`default` = common workers without special features, `long` = common workers but the evaluation will probably take long, `specialX` where X is a number = set of workers with special features)
- `user_id` - author of the submission
- `spawn_ts` - unix timestamp when the job was created and enqueued (rounded to seconds)
- `end_ts` - unix timestamp when the backend submitted results of evaluation (not relevant for the simulations, may be used for rough comparisons)
- `limits` - sum of time limits (as float in seconds) imposed by the configuration of the corresponding exercise (and corresponding runtime); time limits are imposed only on tests, not on compilation or judging phase, but they may act as an approximate upper limit for the duration of evaluation
- `cpu_time` - bool flag (0/1), `true` means the exercise was configured with CPU limits (i.e., designed for more precise measurement, ignoring I/O operations); `false` corresponds to wall-time limits (less precise, but more realistic)
- `correctness` - a float indicating the computed correctness of the solution base on which tests have passed (1 = 100% correct)
- `compilation_ok` - bool flag (0/1), `true` means the compilation phase was successful, thus tests were executed, `false` means the solution failed quickly (no test were executed)
- `duration` - how long the evaluation actually took (as float in seconds); this is not an exact value as internal overhead as well as some data-moving operations are not included (only compilation, execution, and judging times collected from sandbox measurements)

All ID values (except for `worker_group_id`) were anonymized using SHA1 hashing function (along with secret suffix). This anonymization should prevent re-association of provided identifiers with actual identifiers from the live database.

The `correctness`, `compilation_ok`, and `duration` values are gathered **after** the job was evaluated. In other words, they should not be used before that happens in the simulation (e.g., when the job is being dispatched into a worker queue).


## Reference solutions

Reference solutions are submitted by teachers to verify that newly created exercises are working and to gather initial performance measurements based on which time and memory limits for each exercise can be set. Furthermore, teachers may use these solutions for experimenting (e.g., re-testing modified solutions of students or exploring alternative approaches to solving the exercise).

The `ref-solutions.csv` has the following columns:

- `submission_id` - globally unique identifier (not relevant for the simulation)
- `solution_id` - identifier of the reference solution (i.e., source code submitted by teacher); one solution may have multiple submissions if it is re-evaluated by a teacher or an administrator 
- `exercise_id` - to which exercise the solution is addressed (solutions of one exercise are often similar in the duration)
- `runtime_id` - programming language (and its runtime environment configuration) of the solution (one exercise may be solved in different languages/runtimes)
- `worker_group_id` - defines a set of workers which could evaluate the solution (`default` = common workers without special features, `long` = common workers but the evaluation will probably take long, `specialX` where X is a number = set of workers with special features)
- `spawn_ts` - unix timestamp when the job was created and enqueued (rounded to seconds)
- `correctness` - a float indicating the computed correctness of the solution base on which tests have passed (1 = 100% correct)
- `compilation_ok` - bool flag (0/1), `true` means the compilation phase was successful, thus tests were executed, `false` means the solution failed quickly (no tests were executed)
- `duration` - how long the evaluation actually took (as float in seconds); this is not an exact value as internal overhead as well as some data-moving operations are not included (only compilation, execution, and judging times collected from sandbox measurements)

Note that this is a subset of the columns from the main dataset and the columns follow the same rules for encoding, anonymization, etc.
