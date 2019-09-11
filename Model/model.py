# This file establishes the component models that create the equivalent of Google's LAS "Listener", but for
# streams of video inputs, using modifications to attention found in the paper:
#   "END-TO-END ATTENTION-BASED LARGE VOCABULARY SPEECH RECOGNITION" (2015)
#
# A couple notes:
# * Because we want to allow variable-length sequences while knowing the shape of the individual
#   images, we're using `item_shape` to indicate the shape of the items in any sequence, be it the
#   input sequence of video frames or the condensed sequence passed between DSBLSTM layers
#
# * On the general format of the total model: We have frame-by-frame input provided to the Watcher,
#   which is composed of two parts: the convolutions of individual frames and the subsequent layers
#   of stacked bidirectional RNNs (either LSTMs or GRUs). This is created by WatcherBuilder and
#   outputs the "hidden" layer, the shorter sequence that is passed to the decoder.
# * The decoder (analagous to LAS's AttendAndSpell) uses the attention proposed by the paper listed
#   above (ETEABLVSR) combined with an RNN decoder. Of note is that the attention mechanism is
#   tasked with finishing by itself (so it could theoretically run forever without other mechanisms
#   in place), so there are elements built in to prevent that from being an issue.

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

import numpy as np

__all__ = ['DeepStackedBiRNNBuilder', 'Speller']

# for use in DeepStackedBiRNNBuilder
class ConcatPool(layers.Layer):
    def __init__(self, factor):
        super(ConcatPool, self).__init__()

        self.factor = factor

    def build(self, input_shape):
        return

    def call(self, inputs):
        # this is a special case that's only called during setup
        if inputs.shape[0] is None:
            return tf.concat([inputs, inputs], axis=2)

        num_items = inputs.shape[0] // self.factor * self.factor

        # new_shape = list(inputs.shape)
        # new_shape[0] //= self.factor
        # new_shape[-1] = -1

        t = tf.reshape(inputs[:num_items], [inputs.shape[0] // self.factor, 1, -1])
        return t

class DeepStackedBiRNNBuilder:
    def __init__(self, input_shape):
        self.inputs = [keras.Input(shape=input_shape), keras.Input(shape=input_shape)]

        # combine the two inputs
        flattened_left = layers.Flatten()(self.inputs[0])
        flattened_right = layers.Flatten()(self.inputs[1])
        combined = tf.concat([flattened_left, flattened_right], axis=1)
        # add a dimension to make it compatible
        ins = tf.expand_dims(combined, axis=1)

        self.fw = ins
        self.bw = tf.reverse(ins, [0])

        # last_birnn is (rnn_type, units, output_pooling, kwargs)
        self.last_birnn = None

        self.built = False


    def check_build_status(self):
        if self.built:
            raise Exception('Model has already been built')

    def add(self, units, rnn_type=layers.LSTM, output_pooling=1, **kwargs):
        self.check_build_status()

        kwargs["return_sequences"] = True

        self.fw = rnn_type(units, **kwargs)(self.fw)
        self.bw = rnn_type(units, **kwargs)(self.bw)

        if output_pooling != 1:
            self.fw = ConcatPool(output_pooling)(self.fw)
            self.bw = ConcatPool(output_pooling)(self.bw)

        self.last_birnn = (rnn_type, units, output_pooling, kwargs)

        return self

    def repeat(self, n):
        self.check_build_status()

        if self.last_birnn is None:
            raise Exception('Nothing to repeat')

        (rnn_type, units, output_pooling, kwargs) = self.last_birnn

        for i in range(n):
            self.fw = rnn_type(units, **kwargs)(self.fw)
            self.bw = rnn_type(units, **kwargs)(self.bw)

            if output_pooling != 1:
                self.fw = ConcatPool(output_pooling)(self.fw)
                self.bw = ConcatPool(output_pooling)(self.bw)

        return self

    def build(self):
        self.check_build_status()

        # concatenate outputs to be given for each temporal slice so that we get both passes
        # (forward and backward) in the right order, then construct the model.

        self.bw = tf.reverse(self.bw, [0])

        outputs = tf.squeeze(tf.concat([self.fw, self.bw], axis=2), axis=1)

        return keras.Model(inputs=self.inputs, outputs=outputs)


# This is our attention model, which is based on the attention model from:
# "End-to-End Attention-Based Large Vocabulary Speech Recognition", 2016
# link: https://arxiv.org/abs/1508.04395
#
# This type of attention could be referred to as: "Windowed attention with convolutions", but that
# becomes far too lengthy for a class name.
#
# a note for names: in comments, 'hidden_size' refers to the size of the output of the encoder at
# each time-step.
class Attention(tf.keras.Model):
    # w_l and w_r give the number of units to the left and right (respectively) of the previous
    # median to look
    def __init__(self, units, num_features, w_l, w_r, kernel_size=None, preference_left_pad=True):
        super(Attention, self).__init__()

        self.w_l = w_l
        self.w_r = w_r

        if kernel_size is None:
            kernel_size = self.window_size()

        self.kernel_size = kernel_size

        # add necessary padding in order to output convolutional features centered at each
        # attention weight
        l_pad = kernel_size // 2
        r_pad = kernel_size // 2

        if self.kernel_size % 2 == 0:
            # we need to take a unit out on one of the sides of the filter
            if preference_left_pad:
                r_pad -= 1
            else:
                l_pad -= 1

        self.padding_shape = tf.constant([[0, 0], [l_pad, r_pad], [0, 0]])

        # these are as they are described in the aforementioned paper. Instead of directly
        # representing them as a parameter matrix, we're describing them as single-layer
        # perceptrons, because they are functionally the same.
        self.U = layers.Dense(units)
        self.V = layers.Dense(units)
        self.W = layers.Dense(units)
        self.Q = layers.Conv1D(num_features, self.kernel_size, strides=1)

        # In the paper, this is simply a weight vector, but this difference should not matter.
        # The bias vector mentioned in the paper is not present here because the dense layers have
        # their own biases.
        self.w = layers.Dense(1)

        # if not None, then it has the shape of a 1D array
        self.previous_attention = None
        self.previous_window_bounds = None

        self.bounds_restriction = None

    # This should be called at the end of every sequence prediction, once all characters have been
    # generated.
    def reset(self):
        self.previous_attention = None
        self.previous_window_bounds = None

    # sets a restriction on where we can center the attention.
    def set_bounds_restriction(self, bounds_restriction):
        self.bounds_restriction = bounds_restriction

    def remove_bounds_restriction():
        self.bounds_restriction = None

    def window_size(self):
        return self.w_l + 1 + self.w_r

    # only for internal use.
    # takes window bounds (which may walk off the end of 'values') and returns a nicely padded
    # window.
    #
    # returns window with shape (1, window_size, hidden_size)
    def window_helper(values, bounds):
        # lb for lower bound, ub for upper bound
        (lb, ub) = bounds

        seq_len = values.shape[0]

        window = values[max(lb, 0):min(ub, seq_len), ...]
        if lb < 0:
            window = tf.pad(window, [[-1 * lb, 0], [0, 0]], "CONSTANT")
        if ub > seq_len-1:
            diff = ub - seq_len #-1
            window = tf.pad(window, [[0, diff], [0, 0]], "CONSTANT")

        return tf.expand_dims(window, 0)

    # returns window, with shape = (1, window_size, hidden_size)
    #
    # does not allow a window to be centered outside 'values'
    def get_window(self, values):
        # if this is the first round, just center the attention as close to the start as we can.
        if self.previous_attention is None:
            m = 0 if self.bounds_restriction is None else self.bounds_restriction(None)[0]

            # we include the +1 because we want to go 'w_r' units out from the center. This is just
            # like a normal range: [lower, upper)
            self.previous_window_bounds = (m - self.w_l, m + self.w_r +1)
            return Attention.window_helper(values, self.previous_window_bounds)


        # we'll use available_range to define the range that we're allowed to choose our median
        # within
        available_range = (self.bounds_restriction(self.previous_window_bounds)
                           if self.bounds_restriction is not None
                           else (0, self.window_size()))

        # take only the overlap of the two ranges. Even without bound restrictions, this is
        # necessary because the previous window may have gone outside the edge of 'values'
        #
        # lower >= 0, upper <= len(previous_attention)
        lower = max(available_range[0], self.previous_window_bounds[0]) - self.previous_window_bounds[0]
        upper = min(available_range[1], self.previous_window_bounds[1]) - self.previous_window_bounds[0]

        # we're squeezing here because the previous_attention has shape (1, window_size)
        a = tf.squeeze(self.previous_attention)[lower:upper].numpy()
        
        # get index of median. This seems to be the fastest supported way to do this, per this
        # post:
        # https://stackoverflow.com/questions/32923605/is-there-a-way-to-get-the-index-of-the-median-in-python-in-one-command
        m = np.argsort(a)[len(a) // 2]
        
        # now that we have our median in terms of its position in the previous window, we get its
        # absolute position in 'values'
        m += self.previous_window_bounds[0]

        # set new bounds. See comment above near the top of this function about the +1
        self.previous_window_bounds = (m - self.w_l, m + self.w_r +1)
        return Attention.window_helper(values, self.previous_window_bounds)

    # values has shape (hidden_sequence_length, hidden_size)
    # previous_rnn_state has shape (rnn_state_size)
    # returns the context vector and the bounds of the window
    #
    # Will return 'None' if the window is outside of the bounds of the hidden layer
    def call(self, values, previous_rnn_state):
        # window has shape (1, window_size, hidden_size)
        window = self.get_window(values)
        if window is None:
            return None

        # we need the shape to be (1, window_size, 1)
        if self.previous_attention is None:
            self.previous_attention = tf.zeros([1, self.window_size(), 1])

        # in the paper, this is notated as 'F'
        # shape = (1, window_size, kernel_size)
        features = self.Q(tf.pad(self.previous_attention, self.padding_shape))
        # shape = (1, window_size, units)
        _V = self.V(window)
        _U = self.U(features)

        # at first, _W has shape (1, units), so we repeat it to be (1, window_size, units)
        _W = self.W(previous_rnn_state)
        _W = tf.reshape(tf.tile(_W, [1, self.window_size()]), _V.shape)

        # notated as 'e_t'
        # shape = (1, window_size, 1)
        scores = self.w(tf.nn.tanh(_V + _W + _U))

        # notated as '\alpha_t' and 'c_t', respectively
        # shape = (1, window_size, 1)
        attention_weights = tf.nn.softmax(scores)
        self.previous_attention = attention_weights

        # shape = (1, window_size, hidden_size)
        context = attention_weights * window

        # sum the various parts to produce a single, weighted vector -- this is an extension of
        # Bahdanau attention.
        # shape = (1, hidden_size) after reduction
        context_vector = tf.reduce_sum(context, axis=1)

        return context_vector


# speller takes as input the hidden layer produced by Watcher and provides output probabilities of
# each character
class Speller(tf.keras.Model):
    # bits of this are taken from the TensorFlow tutorial:
    # https://www.tensorflow.org/beta/tutorials/text/nmt_with_attention#write_the_encoder_and_decoder_model
    def __init__(self, attn_units, attn_conv_features, attn_window, rnn_units, output_size):
        super(Speller, self).__init__()

        self.attention = Attention(attn_units, attn_conv_features, attn_window[0], attn_window[1])
        self.rnn = layers.GRU(rnn_units, return_sequences=True, return_state=True)
        self.fc = layers.Dense(output_size)

        self.previous_rnn_state = None

    # values is the output from the Encoder
    # previous_output is a one-hot vector corresponding to the chosen output at the last time-step
    #
    # values shape = (1, hidden_sequence_length, hidden_size)
    # previous_output shape = (1, output_size)
    #
    # returns output: shape = (1, output_size); rnn_state: shape = (1, state_size)
    def call(self, values, previous_output):
        # This shouldn't typically be true, becase we'll feed it the start character
        if previous_output is None:
            previous_output = tf.zeros([1, self.fc.units])

        # we need to supply a state to the attention, because it doesn't have its own handling for
        # the 0th state.
        if self.previous_rnn_state is None:
            self.previous_rnn_state = tf.zeros([1, self.rnn.units])

        # shape = (1, hidden_size)
        context_vector = self.attention(values, self.previous_rnn_state)

        # rnn expects shape with ndims=3, so we need to add another dimension here
        # input shape = (1, 1, hidden_size + output_size)
        # rnn_output shape = (1, 1, rnn_output_size)
        # state shape = (1, state_size)
        rnn_output, state = self.rnn(tf.expand_dims(tf.concat([context_vector, previous_output], 1), axis=1))
        self.previous_rnn_state = state

        # shape = (1, rnn_output_size)
        rnn_output = tf.squeeze(rnn_output, axis=1)

        # shape = (1, output_size)
        output = self.fc(rnn_output)

        return output, state

    def reset(self):
        self.attention.reset()
        self.previous_rnn_state = None

    def set_bounds_restriction(self, bounds_restriction):
        self.attention.set_bounds_restriction(bounds_restriction)

    def remove_bounds_restriction(self):
        self.attention.remove_bounds_restriction()