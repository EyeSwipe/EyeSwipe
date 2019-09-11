# Data

**NOTE: DEPRECATED.** Below is the purpose it previously served.

This is the directory in which we store all of the input images to our model. Each directory is
given a name corresponding to the video file in 'SourceData' with the same name. All of the files
in this directory are left ignored by git, with the exception of this README -- backing up the
data itself to github is unecessary.

Each directory here is formatted by '$ID-$N', where $ID is the numerical ID corresponding to the
sentence it represents, and $N is a unique non-negative number used to prevent naming conflicts.
$N is simply the number of videos for the sentence given by $ID that are already present in the
dataset before this video has been added.

Within each directory, there are two sets of files: images cropped to the left eye are written as
'l_$F.jpg', where $F is the frame of the video, starting at 0. Likewise, the images corresponding
to the right eye are written as 'r_$F.jpg'. There is also a single file - 'total' - that indicates
the number of frames.

The format of every part of this directory will likely change in the future.