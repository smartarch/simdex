import tensorflow as tf
import numpy as np
from interfaces import AbstractSelfAdaptingStrategy


def _get_category_encoding_layer(size):
    return lambda feature: tf.one_hot(feature, size + 1)  # +1 since classes are labeled from 1


def _prepare_inputs():
    all_inputs = tf.keras.Input(shape=(2,), dtype='int32')
    encoded_features = []
    domain_sizes = [1875, 20]
    for idx in range(0, 2):
        encoding_layer = _get_category_encoding_layer(domain_sizes[idx])
        encoded_col = encoding_layer(all_inputs[:, idx])
        encoded_features.append(encoded_col)

    return all_inputs, encoded_features


def _create_model(layers_widths):
    all_inputs, encoded_features = _prepare_inputs()

    last_layer = tf.keras.layers.Concatenate()(encoded_features)
    for width in layers_widths:
        last_layer = tf.keras.layers.Dense(int(width), activation=tf.keras.activations.relu)(last_layer)
    output = tf.keras.layers.Dense(1, tf.keras.activations.exponential)(last_layer)

    model = tf.keras.Model(inputs=all_inputs, outputs=output)
    learning_rate = tf.keras.experimental.CosineDecay(0.01, 10000000)
    model.compile(optimizer=tf.optimizers.Adam(learning_rate=learning_rate), loss=tf.losses.Poisson())
    # model.summary()
    return model


def _jobs_to_tensors(jobs):
    x = list(map(lambda job: [job.exercise_id, job.runtime_id], jobs))
    y = list(map(lambda job: [job.duration], jobs))
    return tf.convert_to_tensor(x, dtype=tf.int32), tf.convert_to_tensor(y, dtype=tf.float32)


class CategorySelfAdaptingStrategy(AbstractSelfAdaptingStrategy):
    """Uses machine-learning neural-network regression model to predict the job duration.

    The model is trained in SA and used by dispatcher (via estimation function interface).
    The model is implemented in TensorFlow.
    """

    def __init__(self, layers_widths=[64], batch_size=5000, batch_epochs=5, ref_jobs=None):
        tf.config.threading.set_inter_op_parallelism_threads(8)
        tf.config.threading.set_intra_op_parallelism_threads(8)
        # tf.config.set_visible_devices([], 'GPU')

        self.layers_widths = layers_widths
        self.batch_size = batch_size
        self.batch_epochs = batch_epochs
        self.ref_jobs = ref_jobs[:] if ref_jobs else None
        self.buffer = []
        self.model = None

    def _advance_ts(self, ts):
        while len(self.ref_jobs) > 0 and self.ref_jobs[-1].spawn_ts + self.ref_jobs[-1].duration <= ts:
            job = self.ref_jobs.pop()
            if job.compilation_ok:
                self.buffer.append(job)

    def _train_batch(self):
        """Take the job buffer and use it as batch for training."""
        if len(self.buffer) > self.batch_size:
            x, y = _jobs_to_tensors(self.buffer)
            self.model.fit(x, y, batch_size=len(self.buffer), epochs=self.batch_epochs, verbose=False)
            self.buffer = []  # reset the job buffer at the end

    def init(self, ts, dispatcher, workers):
        self.model = _create_model(self.layers_widths)
        self._advance_ts(ts)
        self._train_batch()

        @tf.function
        def predict_single(input):
            return self.model(input, training=False)[0]

        def predictor(job):
            x = np.array([[job.exercise_id, job.runtime_id]], dtype='int32')
            return predict_single(x).numpy()[0]

        dispatcher.set_predictor(predictor)

    def do_adapt(self, ts, dispatcher, workers, job=None):
        self._advance_ts(ts)
        if job and job.compilation_ok:
            self.buffer.append(job)
            self._train_batch()
