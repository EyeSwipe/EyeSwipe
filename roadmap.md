# TODO: Make a proper, separate README

This isn't it - we need one for newcomers to the project.

# Project Roadmap

This files serves to document everything that has already been done in the project, along with
everything that still needs to be done.

The project can be broken down into a few key systems: [Data Collection](#data-collection),
[Model Building](#model-building), and [Final Usage](#final-usage).

### Data Collection (Python, Go, Swift)

The end goal of our data collection is to provide a set of videos to use as training and test and
test data in constructing our model. This process can be further divided into sub-processes:
Sentence Generation, Dispatch, Recording, and Receiving. The specific data we'd like are videos of
individuals swiping certain sentences, as they would if they were actually using the system.

Sentence Generation is done in [Sentences/Generation](Sentences/Generation), giving the results to
Sentences/sentences.txt. Dispatching the sentences to the [data collection app](kaolin-eyeswipe-recorder)
for recording is done through the server, written in Go ([link](Server)). After the sentence has
been swiped, the app uploads the video file to the server, along with all of the associated
metadata in a separate file.

##### Sentence Generation (Done; Python)

The sentence-generation portion of the project is likely in its final state. It uses a set of of
hand-written YouTube subtitles downloaded with the tool [`youtube-dl`](https://ytdl-org.github.io/youtube-dl/index.html).
The subtitles are parsed and sentences extracted from them using the lexicon created and stored in [`lexicon.txt`](Sentences/Lexicon/lexicon.txt).
This final result is used by the server.

##### App (Swift)

Some work has been done on the app. A friend of the project, Kaolin Fire ([1](https://github.com/kaolin),
[2](http://erif.org/)), has kindly written a large chunk of the data-collection app. All of the
associated files have been placed into [kaolin-eyeswipe-recorder](kaolin-eyeswipe-recorder). The
amount of work left to do is unknown, but the primary things will be:
* Ensuring start/stop of video recording is aligned with sentences
  * Note: There are many options for ensuring this -- long blink to start/stop is one that comes
    to mind, but there are sure to be others. There are performance implications for running
    facial landmark detectors while recording video but it *might* be fine.
  * IF we are already using facial landmarks, we can also store that data and send the
    frame-by-frame locations as metadata along with it to train the model. There are a couple
    libraries that work for this, the most notable being ML Kit, by Google. It works on iOS and
    they provide a facial landmark detector built in.
* Fetching sentences from the server
* Uploading video files and associated metadata (device name/type (screen size), orientation
  (camera on left vs. right), facial landmarks - if tracking that)

##### Server (Go)

About half of the functionality of the server has been completed. Dispatching sentences to users
that request them has been implemented (there's no documentation/specification, though), while
receiving and processing (formatting) incoming videos has not yet been done. Notes on those are
listed:
* Receiving videos
* Processing / Formatting videos
  * Some work on this has been done in a different context, before we decided to make a
    data-collection app. That work can be found in [Convert](Convert (deprecated)) - it is
    mostly to do with standardizing videos and breaking them apart into discrete frames.

The primary goal of the server is to gather the data necessary for the final model building.

### Model Building (Python - TF 2.0)

Some work has been done on this already - including a handful of research. In addition to
everything that's been written in the files in the [Model](Model) subdirectory, there are a few
thoughts outlined below. For reference, the generic idea outlined there consists of three layers:
a convolutional portion that operates on individual images; deep-stacked bidirectional LSTMs
(yeilding a variable-size hidden layer); and a final attention-based decoder.

The primary file for actually training a model is `main_script.py`, which uses `helper.py` and
`consts.py` extensively.

###### Thoughts
* Beam Search is a critical component that should be added (the implementation may prove difficult
  though)
* With beam search, it may not be necessary to use bidirectional LSTMs. There are nice performance
  benefits to simplifying, and it may allow on-the-fly interpretation in a similar fashion to how
  Google's Google Assistant revises its interpretation as it goes - it also sometimes backtracks
  when new information comes in
* Another idea: It may be possible to replace the DSBRNN layer with something akin to google's
  WaveNet - incorporating several previous frames in increasingly large time horizons.
* Currently, the initial convolutional layers operate on a single frame at a time, but it may be
  advantageous to convolve on multiple frames at a time - either overlapping regions or collapsing.
* The encoder/decoder architecture may also not be the best - transformers have been all the rage
  lately, so they may work better.
  * It's also entirely possible to take some other ideas from it - like multi-head attention
    instead of just single-head.
* **Note**: While possible to avoid this, it's very probable that the best solution will involve
  some form of temporal pooling and attention over a hidden layer. No designs have been iterated
  though, so everything mentioned here is purely theoretical.

### Final Usage (Swift, Python?)

The final usage of the EyeSwipe will be as an iPad app, using an embedded model that may or may not
do some additional training with the user. The model could also be converted to an ML Core model
(which seems possible) in order to get the advantage of running Apple's software on their hardware.
We have not done speed comparisons for TensorFlow Lite and ML Core. TensorFlow Mobile is also
possible, but Google recommends TensorFlow Lite as it is what they are focusing on moving forward.