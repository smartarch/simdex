- `submission_id` - globally unique identifier (not relevant for the simulation)
- `solution_id` - identifier of the solution (i.e., source code yielded by user); one solution may have multiple submissions if it is re-evaluated by teacher or administrator 
- `group_id` - group in which the student submits the solution (roughly equivalent of real group of students attending one labs)
- `tlgroup_id` - top-level group that aggregates all groups of one (or few closely related) course(s)
- `exercise_id` - to which exercise the solution is addressed (soulutions of one exercise are often similar in the duration)
- `runtime_id` - programming language of the solution (one exercise may be solved in different languages)
- `worker_group_id` - defines a set of workers which could evaluate the solution (`default` = common workers without special features, `long` = common workers but the evaluation will probably take long, `specialX` where X is a number = set of workers with special features)
- `user_id` - author of the submission
- `spawn_ts` - unix timestamp when the job was created and enqueued
- `end_ts` - unix timestamp when the backend submitted results of evaluation (note relevant for the simulations)
- `limits` - sum of time limits (in seconds) imposed by the configuration of the corresponding exercise (and corresponding runtime); time limits are imposed only on tests, not on compilation or judging phase, but they may act as approimate upper limit for the duration
- `cpu_time` - bool flag (0/1), `true` means the exercise was configured with cpu limits (i.e., designed for more precise measurement, ignoring I/O operations); `false` corresponds to wall-time limits (less precise, but more realistic)
- `duration` - how long the evaluation actually took (in seconds); this is not an exact value as internal overhead as well as some data-moving operations are not included (only compilation, execution and judging times collected from sandbox measurements)

All ID values were anonymized using SHA1 hashing function (along with secret suffix). This anonymization should prevent re-association of provided identifiers with actual identifiers from the live database.
