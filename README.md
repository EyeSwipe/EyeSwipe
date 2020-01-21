# EyeSwipe

Making a proper README is a priority. The project roadmap is in [roadmap.md](roadmap.md).


## Sentences
This directory serves as a workspace for two main functions. The primary use is the generation of sentences from YouTube subtitles, to give as labels for our data-collectors. This process will likely change soon, as we are planning to make a dedicated iOS app for data collection. The associated resources for this can be found in Sentences/Generation.

The secondary use is the creation of a lexicon of ~14k words. The lexicon currently only serves to help in the generation of sentences, but it will eventually be used to inform our language model.

## Server


This directory contains all of the files necessary to run a simple HTTP server to connect with our data-collection app.

There are still significant portions of this server left to build. The entire pipeline envisioned is as follows: The app requests 1 (or more) sentences from the server to have the user swipe and uploads the video to the server. This could go in many orders (such as bulk sentence request, then bulk upload VS. one at a time), but these are the two core functionalities.

Other features that are nice to have are: individual user tracking, so we can put some individuals in our holdout set; storing video/user metadata to allow that input to the model.

This portion of the project is written in Go, so files are stored in idiomatic Go fashion. The only exception here is that GOPATH should be set to this directory (EyeSwipe/Server). That being said, it should be noted that no part of the executable requires a specific path relative to the rest of the project - 'sentences-link.txt' can be changed to allow the freedom to move the absolute path to this directory.

Files
bin/sentences-link.txt: A symbolic link to EyeSwipe/Sentencecs/sentences.txt
bin/server-state.json: A saved copy of the state of the server (not present here).
