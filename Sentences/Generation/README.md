# Generation

This directory houses all of the scripts associated with generating the sentences to supply as
our training data. These scripts don't necessarily need to be run many times, but will be in cases
where components of the project are being re-built. The general pipeline is fairly straightforward.

We use a database of trending YouTube videos to get a list of videos to download subtitles from.
The tool 'youtube-dl' downloads the english subtitles (note: only those written by a human), which
we then parse into sentences.

### Subdirectories

* **youtube-subtitles**: Ingored by git. Stores all of the subtitles once they have been
	downloaded.

### Files

* [gen_consts.py](gen_consts.py): Contains various constants (mostly filepaths) used by these
	scripts so that they can be modified from one central source.
* [get_random_sentences_script.py](get_random_sentences_script.py): Provides a random subset of the
	sentences from 'Sentences/sentences.txt'
* [videolist.py](videolist.py): Provides 'videolist.video_ids()', which returns a list of all of
	the video IDs.
* [get_subtitles_script.py](get_subtitles_script.py): This script fetches the manually-written
	subtitles from youtube for each video. Note: To work properly, it may need to be reset (as it
	edits its source). It can be exited at any time (I find spamming ctrl+C to be sometimes
	necessary), and it will ensure that it updates the starting index so the next time it's run, it
	will pick up where it left off.
* [make_sentences.py](make_sentences.py): Parses the subtitles collected in 'youtube-subtitles' to
	generate a list of sentences, which is output to 'Sentences/sentences.txt'.
* [videoids.json](videoids.json): Because it's a small file and requires USvideos.csv to generate,
	this file is kept here. It's simply the list of YouTube video IDs

##### Not present

* **USvideos.csv**: A dataset of trending YouTube videos in the United States. One of the files
	present in the 'youtube-new' dataset, which can be found [here](https://www.kaggle.com/datasnaek/youtube-new).
	* Note: The file is also included in [Sentences/Sources](../Sources) as `USvideos.zip`.