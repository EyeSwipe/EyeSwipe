# an assorted collection of things that are referenced by 'main.py', but do not need to be defined
# there.
import random
import json
import os
from os import path
import timeit

import tensorflow as tf
import cv2

import consts
from Sentences import sets

# the set of videos we'll pull from
set_of_videos = []
with open(consts.namespace_path) as f:
    namespace = json.load(f)
    for video_id, n in namespace.items():
        for i in range(0, n):
            set_of_videos.append((int(video_id), i))

def get_images(video, n):
    subdir = path.join(consts.data_dir, "{}-{}".format(video, n))

    total = path.join(subdir, consts.num_total_file)
    if not path.exists(total):
        raise Exception("No total file found ('{}' does not exist)".format(total))
    with open(total) as f:
        size = int(f.read().strip())

    left_imgs = []
    right_imgs = []

    for i in range(0, size):
        left_path = path.join(subdir, consts.left_eye_format.format(i))
        right_path = path.join(subdir, consts.right_eye_format.format(i))

        l_img = cv2.imread(left_path)
        r_img = cv2.imread(right_path)

        if l_img is None:
            raise Exception("File '{}' not found.".format(left_path))
        if r_img is None:
            raise Exception("File '{}' not found.".format(right_path))
        
        left_imgs.append(tf.convert_to_tensor(l_img, dtype=tf.float32))
        right_imgs.append(tf.convert_to_tensor(r_img, dtype=tf.float32))

        # left_imgs.append(tf.convert_to_tensor(cv2.imread(left_path), dtype=tf.float32))
        # right_imgs.append(tf.convert_to_tensor(cv2.imread(right_path), dtype=tf.float32))

    return (tf.convert_to_tensor(left_imgs), tf.convert_to_tensor(right_imgs))

def loss_function(real, pred):
    mask = tf.math.logical_not(tf.math.equal(real, 0))
    loss_ = loss_object(real, pred)

    mask = tf.cast(mask, dtype=loss_.dtype)
    loss_ *= mask

    return tf.reduce_mean(loss_)

def index_list():
    l = set_of_videos.copy()
    random.shuffle(l)
    return l

def trial_with_random(img_process, dsbrnn, speller):
    # this is just an arbitrarily chosen number
    seq_len = 32
    input_shape = [consts.output_height, consts.output_width, 3]
    random_left = tf.random.uniform([seq_len] + input_shape)
    random_right = tf.random.uniform([seq_len] + input_shape)

    _, _ = speller(dsbrnn([img_process(random_left), img_process(random_right)]), None)

# The following section is taken directly form the tensorflow 2.0 tutorial:
# https://www.tensorflow.org/beta/tutorials/text/nmt_with_attention#define_the_optimizer_and_the_loss_function
optimizer = tf.keras.optimizers.Adam()
loss_object = tf.keras.losses.SparseCategoricalCrossentropy(
        from_logits=True, reduction='none')

def loss_function(real, pred):
    mask = tf.math.logical_not(tf.math.equal(real, 0))
    loss_ = loss_object(real, pred)

    mask = tf.cast(mask, dtype=loss_.dtype)
    loss_ *= mask

    return tf.reduce_mean(loss_)

# inputs is a tuple of two tensors, left eye and right eye
def train_step(img_process, dsbrnn, speller, inputs, targets):
    loss = 0

    with tf.GradientTape() as tape:
        values = dsbrnn([img_process(inputs[0]), img_process(inputs[1])])

        # teacher forcing, so we'll disregard the previous
        speller_input = tf.expand_dims(tf.one_hot(targets[0], len(sets.output_set), dtype=tf.float32), axis=0)
        for t in targets[1:]:
            # returns output, rnn_state
            predictions, _ = speller(values, speller_input)

            loss += loss_function(tf.expand_dims(t, axis=0), predictions)

            # teacher forcing
            speller_input = tf.expand_dims(tf.one_hot(t, len(sets.output_set), dtype=tf.float32), axis=0)

    batch_loss = loss / (len(targets) - 1)
    
    variables = img_process.trainable_variables + dsbrnn.trainable_variables + speller.trainable_variables

    gradients = tape.gradient(loss, variables)

    optimizer.apply_gradients(zip(gradients, variables))

    speller.reset()

    return batch_loss