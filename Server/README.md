# Server

This directory contains all of the files necessary to run a simple HTTP server to connect with our
data-collection app.

There are still significant portions of this server left to build. The entire pipeline envisioned
is as follows:
The app requests 1 (or more) sentences from the server to have the user swipe and uploads the video
to the server. This could go in many orders (such as bulk sentence request, then bulk upload VS.
one at a time), but these are the two core functionalities.

Other features that are nice to have are: individual user tracking, so we can put some individuals
in our holdout set; storing video/user metadata to allow that input to the model.

This portion of the project is written in Go, so files are stored in idiomatic Go fashion. The only
exception here is that `GOPATH` should be set to [this](.) directory (EyeSwipe/Server). That being
said, it should be noted that no part of the executable requires a specific path relative to the
rest of the project - 'sentences-link.txt' can be changed to allow the freedom to move the absolute
path to this directory.

### Files

* **bin/sentences-link.txt**: A symbolic link to EyeSwipe/Sentencecs/sentences.txt
* **bin/server-state.json**: A saved copy of the state of the server (not present here).


-----------------------------------

Update 2/23/21: Go Server refactored and completed. Several changes to server design and data pipeline
were made:

New data pipeline: The server has only two handler functions: getSentence and storeVideo. App users issue
a GET request to serverIP:8080/sentence/get and receive a random sentence from the sentence pool. Similarly, 
users issue a POST request containing metadata and a video file to serverIP:8080/data/upload to store video.
Upload requests are entirely decoupled from sentence-getting, and all necessary metadata including userID
and the sentence itself are contained in the metadata of each upload request.

These two methods capture the core functionality of the server while retaining a simple design. Previous design
assigned sentences to users based on an allocation system, while the new design simply chooses a random
sentence from the sentence pool and assigns it. In practice there is a very small chance that a user will
be assigned the same sentence twice, and even if this happens there is no real downside to it.

Data storage is as follows:

EyeSwipe/
	Server/
		src/
			...
		testing/
			...
		data/
			userID1/
				hash(sentence)/
					1.mov
					metadata-1.txt
					2.mov
					metadata-2.txt
			userID2/
				...

Within the data directory, files are stored first according to userID, to make grouping by user convenient.
After this, a video for a particular sentence is stored in its own directory, along with associated metadata.
For uniqueness the directory name is the hash of the sentence whose video is being stored. If a user has n 
videos on file for a sentence, the videos and their associated metadata files are numbered 1-n and stored in 
the same directory. UserID is chosen on the app end; one good userID system could be hash(firstName + lastName +
DOB).

Design update #1: Server is now stateless. After the new data pipeline was envisioned, it became clear that
server management of userIDs, etc was unnecessary. All necessary data for both directions of data flow are 
directly included in HTTP requests, so the server does not need to remember any information about users or
sentence allocation.

Design update #2: sentences.go renamed/refactored into io.go, and main method moved to run_server.go. With a stateless
design, the MainContext struct became unnecessary and was replaced by the sentenceManager struct, which maintains
a slice containing all sentences in the sentence pool, and methods initialize(), which loads sentences.txt into the
sentenceManager, and getSentence() which returns a random sentence from the pool. The rest of io.go contains methods
to create and manage the file system described above. 

Design update #3: math/rand replaced with crypto/rand. This is a minor point, but math/rand methods are deterministic
across different runs, so if the server is restarted more frequently than the sentences file is updated, there
will be a subset of sentences which are picked first repeatedly, leading to an uneven distribution of selected
sentences.

Design update #4: Added a basic testing suite. Running go test after starting the server will query the server for
a sentence and print it, and then send a POST request containing testing/test.mov and test metadata and test
for the presence of ../data/testID/hash(testSentence)/1.mov, ../data/testID/hash(testSentence)/metadata1.txt and
check their integrity.