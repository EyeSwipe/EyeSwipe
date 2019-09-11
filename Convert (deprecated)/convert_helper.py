# This holds a large number of specific functions used in 'convert_script.py'.

import os
import sys
import json

import cv2
import dlib

# import `consts.py` from the parent directory
from os.path import abspath, join, dirname
sys.path.append(abspath(join(dirname(abspath(__file__)), '..')))
import consts

# indexes in dlib's 68-point landmark shape predictor
# taken from:
# https://www.pyimagesearch.com/2017/04/03/facial-landmarks-dlib-opencv-python/,
# https://www.pyimagesearch.com/wp-content/uploads/2017/04/facial_landmarks_68markup.jpg
l_eye_l_edge = 36
l_eye_r_edge = 39
r_eye_l_edge = 42
r_eye_r_edge = 45

# pre-load the face-detection from dlib so they we have them while we do cropping
detector = dlib.cnn_face_detection_model_v1(consts.face_detector_path)
predictor = dlib.shape_predictor(consts.facial_landmark_detector_path)

previous_write = ""
def write_flush(s):
	global previous_write

	sys.stdout.write(s)
	sys.stdout.flush()
	previous_write = s

def query_yes_no(init_msg, retry_msg, delayed_interrupt=None):
	if delayed_interrupt is not None:
		delayed_interrupt.disable()
	write_flush(init_msg)

	while True:
		response = sys.stdin.readline().strip()
		
		if response == 'y' or response == 'n':	
			if delayed_interrupt is not None:
				delayed_interrupt.enable()
			return response

		write_flush(retry_msg)


def get_namespace(delayed_interrupt):
	previous_line = previous_write

	namespace = {}
	if os.path.exists(consts.namespace_path):
		with open(consts.namespace_path, 'r') as f:
			namespace = json.load(f)
	else:
		response = query_yes_no('\rNo namespace file found. Continue? (y/n): ',
								"Please enter 'y' or 'n'. Continue? (y/n): ",
								delayed_interrupt)
		if response == 'n':
			print("Found no file at: '{}'".format(consts.namespace_path))
			return None

		write_flush(previous_line)
	
	return namespace

def update_namespace(new_namespace):
	with open(consts.namespace_path, 'w+') as f:
		json.dump(new_namespace, f)

# This function is separated so that it can be changed later
def parse_import_filename(filename):
	id_and_ext = filename.split('.')
	# returns id, ext
	return id_and_ext[0], id_and_ext[1]

# renames the file with the given name, and returns the new name
#
# This function assumes that our working directory is the top-level directory of the project
def rename_with_namespace(delayed_interrupt, filename):
	sentence_id, ext = parse_import_filename(filename)

	namespace = get_namespace(delayed_interrupt)
	if namespace is None:
		return None

	n = namespace[sentence_id] if sentence_id in namespace else 0
	namespace[sentence_id] = n + 1

	new_filename = "{}-{}.{}".format(sentence_id, n, ext)
	new_filepath = os.path.join(consts.import_dir, new_filename)
	old_filepath = os.path.join(consts.import_dir, filename)
	os.rename(old_filepath, new_filepath)

	# We wait until the end to update `namespace` because we don't want to write to the file with
	# our changes to `namespace` until we know that we need to (i.e. until we've renamed the file)
	#
	# In reality, we wait on every part of this to finish, because of how it's called in
	# `convert_script.py`, but -- in case that doesn't work (or the process is killed) -- it's good
	# to be safe about it.
	# The specific concern here is that `os.rename` fails
	update_namespace(namespace)

	return new_filename

# moves the given directory entry (e.g. file, subdirectory) in `init_dir` with the given `filename`
# into `targ_dir` 
def move(filename, init_dir, targ_dir):
	os.rename(os.path.join(init_dir, filename), os.path.join(targ_dir, filename))

# makes a subdirectory with `subdir_name` within `containing_dir` and outputs a sequence of images to 
def convert_to_imgs(filename, subdir_name, containing_dir):
	filepath = os.path.join(containing_dir, filename)
	
	subdir_path = os.path.join(containing_dir, subdir_name)
	os.makedirs(subdir_path)

	file_names = os.path.join(subdir_path, consts.img_file_format)

	os.system("ffmpeg -loglevel panic -i {} -r {} {}".format(filepath, consts.fps, file_names))

def crop_image(i, img_path, face_box):
	# unfortunately, it appears we can't simply use the same image both times; we have to
	# independently load it twice. In its C++ documentation, dlib lists `cv_image()` as a method
	# for generating a dlib image from an opencv image, but that feature does not seem to be
	# available for Python.

	shape = predictor(dlib.load_rgb_image(img_path), face_box)

	img = cv2.imread(img_path)

	output_dim_ratio = float(consts.output_height) / float(consts.output_width)

	def crop_helper(write_file, l_edge_index, r_edge_index):
		# get the bounds of the cropped region on the x-axis
		x1 = shape.part(l_edge_index).x
		x2 = shape.part(r_edge_index).x

		# from our given x-axis bounds, determine our y coordinates. We'll center the cropped
		# region at the average of the corners of the eye (given by the shape indexes)
		y_center = (shape.part(l_edge_index).y + shape.part(r_edge_index).y) / 2
		height = output_dim_ratio * (x2 - x1)
		y1 = int(y_center - height/2)
		y2 = int(y_center + height/2)

		# get the new, cropped image and scale it
		new_img = img[y1:y2, x1:x2]
		
		scale_factor = float(consts.output_height) / float(int(height))
		new_width = (x2 - x1) * scale_factor
		new_height = (y2 - y1) * scale_factor
		
		new_img = cv2.resize(new_img, (int(new_width), int(new_height)))

		# save the image
		cv2.imwrite(write_file, new_img)

	crop_helper(consts.left_eye_format.format(i), l_eye_l_edge, l_eye_r_edge)
	crop_helper(consts.right_eye_format.format(i), r_eye_l_edge, r_eye_r_edge)

