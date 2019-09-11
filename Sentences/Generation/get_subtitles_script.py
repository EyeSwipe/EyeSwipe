import csv
import os
import inspect
import time
import signal

import videolist as vlist
import gen_consts as consts

video_ids = vlist.video_ids()

# The following line will change every time the script is interrupted to reflect where we need to
# pick up on.
startAt = 6350
line_of_start = inspect.stack()[0].lineno - 1

index = startAt

if not os.path.exists(consts.subtitles_dir):
	os.makedirs(consts.subtitles_dir)

# when formatted, produces something like:
# "youtube-dl --write-sub --sub-lang en --skip-download -o youtube-subtitles/kfPNxNIDHrA https://www.youtube.com/watch?v=kfPNxNIDHrA"
cmdBase = "youtube-dl --write-sub --sub-lang en --skip-download -o {}{}{} https://www.youtube.com/watch?v={}"
try:
	for video in video_ids[startAt:]:
		# sleep so that we can allow ^C
		time.sleep(0.3)

		print("Video: {}".format(index))
		cmd = cmdBase.format(consts.subtitles_dir, os.path.sep, video, video)
		os.system(cmd)

		index += 1

	# because of the 'finally' block, this indicates that we're FULLY done
	index += 1
finally:
	# modify this file's source so that we can change `startAt` to reflect the new place we've gotten to.

	# disable keyboard interrupt temporarily
	old_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)

	with open(__file__) as f:
		source_lines = f.readlines()
	# line numbers start at 1, not zero
	source_lines[line_of_start -1] = 'startAt = {}\n'.format(index - 1)
	with open(__file__, 'w') as f:
		for l in source_lines:
			f.write(l)

	signal.signal(signal.SIGINT, old_handler)
