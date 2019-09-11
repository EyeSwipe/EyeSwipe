import os
containing_dir = os.path.dirname(os.path.abspath(__file__))

def wrap(path):
	return os.path.abspath(os.path.join(containing_dir, path))

videos_dataset = wrap('USvideos.csv')
video_id_list = wrap('videoids.json')
subtitles_dir = wrap('youtube-subtitles')
all_sentences = wrap('sentences_all.txt')
ext = 'en.vtt'

# the maximum amount of gap between subtitle blocks that for which we'll
# consider them as continuous, measured in seconds
#
# Note: This is used in two ways. (1) To determine overlapped regions,
# and (2) to indicate the start of a new sentence
subtitle_max_gap_time = 0.3

# the required portion of subitles that need to have overlap in order to
# consider it a part of the formatting for the video
subtitle_min_fraction = 0.5

# These two constants dictate the minimum and maximum lengths of
# sentences we'll allow with our cleaning script
lower_bound = 3
upper_bound = 15