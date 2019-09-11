# This file serves as a place to put all of the various constants used by parts of this system.

import os
containing_dir = os.path.dirname(os.path.abspath(__file__))

def wrap(path):
	return os.path.join(containing_dir, path)

data_dir = wrap('Data')
import_dir = wrap('Import')
source_data_dir = wrap('SourceData')
checkpoint_dir = wrap('Checkpoints')
checkpoint_prefix = wrap('Checkpoints/ckpt')

num_total_file = 'total'
left_eye_format = "l_{}.jpg"
right_eye_format = "r_{}.jpg"

output_height = 20
output_width = 30
fps = 30
namespace_path = wrap('Convert/namespace.json')
face_detector_path = wrap('Convert/mmod_human_face_detector.dat')
facial_landmark_detector_path = wrap('Convert/shape_predictor_68_face_landmarks.dat')
img_file_format = "%d.jpg"

from Sentences import sets

# the final model output size
final_output_size = len(sets.output_set)
