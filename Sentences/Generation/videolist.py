# This file provides a list of all of the videoids that are in the trending videos dataset. If the
# file has not already been created, this script will create 'videoids.json', which stores the list
# as a json array for easy access.

import csv
import os
import json

import gen_consts as consts

# If the file hasn't been made yet, write everything to the file so that we don't have to load the
# csv every single time.
if not os.path.exists(consts.video_id_list):
	# We make a set to ensure that we don't count the duplicates (there are many in the dataset)
	video_ids = []
	video_set = set()

	with open(consts.videos_dataset) as f:
		csv_reader = csv.reader(f, delimiter=',')

		first_line = True
		for row in csv_reader:
			if first_line:
				first_line = False
			else:
				video = row[0]
				if video not in video_set:
					video_ids.append(video)
					video_set.add(video)


	# store all of the videos
	with open(consts.video_id_list, 'w+') as f:
		json.dump(video_ids, f, indent=4)

def video_ids():
	with open(consts.video_id_list) as f:
		return json.load(f)