from __future__ import absolute_import, division, print_function

import os
import matplotlib.pyplot as plt

import tensorflow as tf
import tensorflow.contrib.eager as tfe


def parse_csv(line):
    example_defaults = [[0.], [0.], [0.], [0.], [0]]  # sets field types
    parsed_line = tf.decode_csv(line, example_defaults)
    # First 4 fields are features, combine into single tensor
    features = tf.reshape(parsed_line[:-1], shape=(4,))
    # Last field is the label
    label = tf.reshape(parsed_line[-1], shape=())
    return features, label


def loss(model, x, y):
    y_ = model(x)
    return tf.losses.sparse_softmax_cross_entropy(labels=y, logits=y_)


def grad(model, inputs, targets):
    with tf.GradientTape() as tape:
        loss_value = loss(model, inputs, targets)
    return tape.gradient(loss_value, model.variables)


tf.enable_eager_execution()

print("TensorFlow version: {}".format(tf.VERSION))

train_dataset_fp = "/Users/sanchosmit/PycharmProjects/tensorflowWatering/water_training.csv"

train_dataset = tf.data.TextLineDataset(train_dataset_fp)
# parse each row
train_dataset = train_dataset.map(parse_csv)
# randomize
train_dataset = train_dataset.shuffle(buffer_size=500)
train_dataset = train_dataset.batch(30)

# model
model = tf.keras.Sequential([
    tf.keras.layers.Dense(10, activation="relu", input_shape=(4,)),  # input shape required
    tf.keras.layers.Dense(10, activation="relu"),
    tf.keras.layers.Dense(2)
])

# optimizer
optimizer = tf.train.GradientDescentOptimizer(learning_rate=0.01)

# keep results for plotting
train_loss_results = []
train_accuracy_results = []

num_epochs = 501

# learning
for epoch in range(num_epochs):
    epoch_loss_avg = tfe.metrics.Mean()
    epoch_accuracy = tfe.metrics.Accuracy()

    # Training loop - using batches of 30
    for x, y in train_dataset:
        # Optimize the model
        grads = grad(model, x, y)
        optimizer.apply_gradients(zip(grads, model.variables),
                                  global_step=tf.train.get_or_create_global_step())

        # Track progress
        epoch_loss_avg(loss(model, x, y))  # add current batch loss
        # compare predicted label to actual label
        epoch_accuracy(tf.argmax(model(x), axis=1, output_type=tf.int32), y)

    # end epoch
    train_loss_results.append(epoch_loss_avg.result())
    train_accuracy_results.append(epoch_accuracy.result())

    if epoch % 50 == 0:
        print("Epoch {:03d}: Loss: {:.3f}, Accuracy: {:.3%}".format(epoch,
                                                                    epoch_loss_avg.result(),
                                                                    epoch_accuracy.result()))


# plots
fig, axes = plt.subplots(2, sharex=True, figsize=(12, 8))
fig.suptitle('Training Metrics')

axes[0].set_ylabel("Loss", fontsize=14)
axes[0].plot(train_loss_results)

axes[1].set_ylabel("Accuracy", fontsize=14)
axes[1].set_xlabel("Epoch", fontsize=14)
axes[1].plot(train_accuracy_results)

plt.show()


# test
test_fp = "/Users/sanchosmit/PycharmProjects/tensorflowWatering/water_training_test.csv"

test_dataset = tf.data.TextLineDataset(test_fp)
test_dataset = test_dataset.map(parse_csv)      # parse each row with the funcition created earlier
test_dataset = test_dataset.shuffle(1000)       # randomize
test_dataset = test_dataset.batch(30)           # use the same batch size as the training set

test_accuracy = tfe.metrics.Accuracy()

for (x, y) in test_dataset:
  prediction = tf.argmax(model(x), axis=1, output_type=tf.int32)
  test_accuracy(prediction, y)

print("Test set accuracy: {:.3%}".format(test_accuracy.result()))


# prediction
class_ids = ["Not water", "Water"]

predict_dataset = tf.convert_to_tensor([
    [2., 65.3, 23.7, 30.5],
    [3., 25.3, 22.4, 40.5],
    [1., 55.3, 20.7, 55.5],
    [5., 15.3, 21.7, 67.5],
    [4., 45.3, 22.3, 77.5]
])

predictions = model(predict_dataset)

for i, logits in enumerate(predictions):
    class_idx = tf.argmax(logits).numpy()
    name = class_ids[class_idx]
    print("Example {} prediction: {}".format(i, name))


# saving
checkpoint_directory = "/Users/sanchosmit/PycharmProjects/tensorflowWatering/checkpoint"
checkpoint_prefix = os.path.join(checkpoint_directory, "ckpt")

root = tfe.Checkpoint(optimizer=optimizer, model=model)
root.save(file_prefix=checkpoint_prefix)



