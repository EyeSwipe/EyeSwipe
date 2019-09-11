# Convert

**NOTE: DEPRECATED.** Below is the purpose it previously served.

This directory contains all of the relevant files used for creating training data from our source
video files.

The basic data conversion process is fairly simple. Once data has been loaded into ['/Import'](../Import)
(in the top-level directory), we rename the video and use ffmpeg to convert it into a series of
images. Dlib's face detection is used on the first frame to locate the general position of the face
in the video, and the facial landmark detector is used to crop each image. SIGINT is delayed
throughout the majority of this process in order to ensure that we won't ever need to revert
changes once we've made them (e.g. renaming, creating subdirectories, etc.), or clean up partway
through. The data that we're saving is the collection of cropped images.

After we have a subdirectory -- usually within '/Import' of cropped images, we transfer that set to
['/Data'](../Data), and move the original video file to ['/SourceData'](SourceData).

The other method for conversion instead rebuilds the contents of 'Data' from the files in
'SourceData'. This can be selected with an interactive menu at runtime.

### Files

* [delayedinterrupt.py](delayedinterrupt.py): This file establishes a simple class to be used to
	prevent SIGINT from halting key parts of the conversion process -- allowing it to be terminated
	safely at any time. More information can be found in the file.
* [convert_helper.py](convert_helper.py): Just a simple helper file for 'convert_script.py'. It
	takes care of most of the function, while the script itself displays the interaction.
* [convert_script.py](convert_script.py): This is the main script for the video conversion process.

##### Files not present

* **namespace.json**: This file serves to record how many videos for each unique sentence ID have
	already been added to the dataset. This file is not included, as it is only useful in
	combination with the dataset, which is not present in this repo.
* **mmod_human_face_detector.dat**: Will be removed soon. This is one of dlib's supplied face
	detectors. It does not come pre-installed with the rest of dlib, but can be downloaded
	[here](http://dlib.net/files/mmod_human_face_detector.dat.bz2)
* **shape_predictor_68_face_landmarks.dat**: This will also be removed soon. This is a facial
	landmarks detector supplied by dlib, and it can be downloaded
	[here](http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2).

### An additional note, post-deprecation:

Because `namespace.json` is not present, and these scripts may not be run again, here is the last
value of `namespace.json` with just a few videos all done by one person:
```json
{"14": 1, "1": 1, "2": 1, "4": 1, "6": 1, "7": 1, "12": 1, "3": 1, "8": 1, "13": 1, "11": 1, "9": 1, "10": 1, "5": 1, "15": 1}
```