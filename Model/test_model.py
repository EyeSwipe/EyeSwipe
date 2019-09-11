import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

from model import *

print('Testing a sample model')

# define the necessary input
sample_input = tf.random.uniform([60, 100, 100, 3])
input_shape = sample_input.shape[1:]
seq_len = sample_input.shape[0]

# base convolutional operations
video_stream = keras.Input(shape=input_shape)
l = layers.AveragePooling2D(pool_size=(2,2))(video_stream)
l = layers.Conv2D(10, (5, 5), activation='relu')(l)
l = layers.MaxPooling2D((2, 2))(l)
l = layers.Conv2D(20, (3, 3), activation='relu')(l)
l = layers.MaxPooling2D((2, 2))(l)
l = layers.Conv2D(20, (3, 3))(l)
img_converter = keras.Model(inputs=video_stream, outputs=l)

print('image converter summary:')
img_converter.summary()

dsbrnn_input_shape = l.shape[1:]
dsbrnn = DeepStackedBiRNNBuilder(dsbrnn_input_shape)
dsbrnn.add(40, output_pooling=2).repeat(2)
dsbrnn.add(20)
dsbrnn = dsbrnn.build()

print('dsbrnn summary')
dsbrnn.summary()

attn_units = 10
attn_conv_features = 4
attn_window = (0, 4)
rnn_units = 20
output_size = 30
speller = Speller(attn_units, attn_conv_features, attn_window, rnn_units, output_size)

output, _ = speller(dsbrnn(img_converter(sample_input)), None)
print('sample output:', output)
print('done testing!')
