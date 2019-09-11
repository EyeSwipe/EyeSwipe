import time

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

from Model.model import *
import helper
import consts
import Data
from Sentences import sets

print('Creating model...')

# Currently [20, 30, 3]
input_shape = [consts.output_height, consts.output_width, 3]

# Note: We are intentionally not using pooling here -- see the results of this paper:
# https://arxiv.org/pdf/1412.6806.pdf
#
# A lot of this is just guess-work. This is one of the more tweak-able parts of the model.
# init = keras.initializers.he_normal
img_process = keras.Sequential([
    layers.Conv2D(15, (7, 7), activation='relu', input_shape=input_shape),
    # shape = (14, 24, 30)
    layers.Conv2D(15, (3, 3), activation='relu'),
    # shape = (12, 22, 15)
    # pool
    layers.Conv2D(15, (3, 3), strides=(2, 2), activation='relu'),
    # shape = (5, 10, 15)
    layers.Conv2D(30, (3, 3), activation='relu'),
    # shape = (3, 8, 30)
])

# print('Image processor done. Summary:')
# img_process.summary()

# create our stacked birnn layers
# in this case, the input shape is (3, 8, 30)
dsbrnn_input_shape = img_process.layers[-1].output_shape[1:]
dsbrnn = DeepStackedBiRNNBuilder(dsbrnn_input_shape)
dsbrnn.add(40, output_pooling=2).repeat(2)
dsbrnn.add(20)
dsbrnn = dsbrnn.build()

# print('DSBRNN done. Summary:')
# dsbrnn.summary()

attn_units = 10
attn_conv_features = 4
attn_window = (0, 4)
rnn_units = 20
output_size = consts.final_output_size
speller = Speller(attn_units, attn_conv_features, attn_window, rnn_units, output_size)

# test a sample input to get speller summary
helper.trial_with_random(img_process, dsbrnn, speller)

print('Parameter counts:')
print("\timg_process: {}".format(img_process.count_params()))
print("\tdsbrnn: {}".format(dsbrnn.count_params()))
print("\tspeller: {}".format(speller.count_params()))

# establish checkpoint
checkpoint = tf.train.Checkpoint(optimizer=helper.optimizer,
                                 img_process=img_process,
                                 dsbrnn=dsbrnn,
                                 speller=speller)

# train
dset = helper.index_list()

EPOCHS = 10
for epoch in range(EPOCHS):
    start = time.time()

    total_loss = 0
    for batch, (video_id, n) in enumerate(dset):
        img_seq = helper.get_images(video_id, n)
        targets = sets.as_labels(sets.from_id(video_id))

        batch_loss = helper.train_step(img_process, dsbrnn, speller, img_seq, targets)
        total_loss += batch_loss

        if batch % 10 == 0:
            print('Epoch {} Batch {} Loss {:.4f}'.format(epoch + 1, batch, batch_loss.numpy()))

    # save a checkpoint every other epoch
    if (epoch + 1) % 2 == 0:
        checkpoint.save(file_prefix = consts.checkpoint_prefix)

    print('Epoch {} Loss {:.4f}'.format(epoch + 1, total_loss / len(dset)))
    print('Time taken for 1 epoch {} sec\n'.format(time.time() - start))
