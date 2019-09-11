# Adds index numbers to every sentence found in `new_sentences.txt` and saves the file as
# `sentences_annotated.txt`
#
# Note: If there is a larger stream of incoming sentences, we can change this to keep track of the
# current number so that we start this with that and append to that file.

import os

sentences = []

with open("sentences.txt") as f:
	for line in f:
		sentences.append(line.strip())

with open("sentences_annotated.txt", "a+") as f:
	for i, s in enumerate(sentences):
		f.write("{:<3}: {}\n".format(i+1, s))