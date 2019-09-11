# Assumes that all of the files in 'Import/' are video files that have already been renamed to a
# format that we want them to be: e.g. '7.MOV', '21.mp4'
#
# we'll run into issues if there are any files in 'Import/' that are not video files.
#
#
# USAGE:
# This script exists to process raw video files, typically from 'Import/', and convert them to the
# format that we want. In the process of converting new data, we update 'namespace.json' to avoid
# any naming conflicts.
#
# The training data can also be reconstructed from the source video files in 'SourceData/', which
# will not change 'namespace.json'
#
# Choosing between these options is done with an interactive interface, so it need not be specified
# beforehand.

import os
import sys
import json

import cv2
import dlib

from delayedinterrupt import DelayedInterrupt
import convert_helper as helper

# import `consts.py` from the parent directory
from os.path import abspath, join, dirname
sys.path.append(abspath(join(dirname(abspath(__file__)), '..')))

import consts

# Choose between rebuilding from source files or going without
# the 'yes' == ... converts 'yes'/'no' to True/False
from_source = 'y' == helper.query_yes_no('Rebuild from source data? (y/n): ',
										   "Please enter 'y' or 'n'. Rebuild? (y/n): ")

# This is the directory that we'll get all of our video files from.
data_dir = consts.source_data_dir if from_source else consts.import_dir

working_directory_save = os.getcwd()

# convert the videos to sets of frames
videos = os.listdir(data_dir)
for i, filename in enumerate(videos):
	with DelayedInterrupt() as delayed_interrupt:
		helper.write_flush("Working on video '{}' ({}/{})".format(filename, i+1, len(videos)))

		# use `namespace` to rename the image to a unique name
		if not from_source:
			filename = helper.rename_with_namespace(delayed_interrupt, filename)
			if filename is None:
				sys.exit()

			helper.write_flush("\rWorking on video '{}' ({}/{}, renamed)\n".format(filename, i+1, len(videos)))
		else:
			# we're done now
			helper.write_flush('\n')

		# Convert all of the images to files
		subdir_name = filename.split('.')[0]
		helper.write_flush('\tConverting to image sequence...')
		helper.convert_to_imgs(filename, subdir_name, data_dir)
		helper.write_flush(' Done\n')

		# NOTE: We change our working directory here so that all of the operations are on relative
		# filepaths.
		os.chdir(os.path.join(data_dir, subdir_name))

		# do our image processing

		helper.write_flush("\tFinding faces...")
		faces = helper.detector(dlib.load_rgb_image("1.jpg"), 0)
		helper.write_flush(" Done! Found {}.\n".format(len(faces)))

		if len(faces) != 1:
			print("Cannot use video '{}', did not contain exactly one face.".format(filename))
			 
			# save the original video
			os.chdir(working_directory_save)
			helper.move(filename, consts.data_dir, consts.source_data_dir)

			continue

		face_box = faces[0].rect

		files = os.listdir('.')
		for i, img_path in enumerate(files):
			percent = 100 * i // len(files)
			helper.write_flush("\r\tProcessing images... {}%".format(percent))

			helper.crop_image(i, img_path, face_box)

		helper.write_flush("\r\tProcessing images... Done!\n")

		# make a note of how many frames there were
		with open(consts.num_total_file, 'w+') as f:
			json.dump(len(files), f)

		# instead of collecting the image files into videos, we'll leave them as is
		# we will, however, remove the other video files, though. We'll leave a simple text file to
		# tell us how many frames there are in the video
		#
		# because we're using 'files', we only get the original images, not the new ones
		helper.write_flush("\tFinishing up... ")
		for img_path in files:
			os.remove(img_path)

		os.chdir(working_directory_save)

		# move the directory to data
		helper.move(subdir_name, data_dir, consts.data_dir)
		# save the original video to source data
		helper.move(filename, data_dir, consts.source_data_dir)
		helper.write_flush(" Done!\n")
