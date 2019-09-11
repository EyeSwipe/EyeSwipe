# provides a simple interface for getting the sentence associated with a given sentence id number
import os
import re
import json

from . import sentence_consts as consts

__all__ = ['from_id', 'as_labels', 'load_sentences', 'unload_sentences']

sentences = None
# preloads the sentences in memory so that we don't have to repeatedly read the file.
def load_sentences():
	global sentences
	if sentences is not None:
		return

	with open(consts.cleaned_sentences) as f:
		sentences = f.read().split('\n')

def unload_sentences():
	global sentences
	sentences = None

def from_id(id_num, remove_punctuation=True):
	load_sentences()
	s = sentences[id_num]
	unload_sentences()

	if remove_punctuation:
		s = re.sub('[^' + output_set_str + ']', '', s)

	return s

# '^' and '$' signify the start and end of the sequence, respectively
output_set_str = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz ^$'
output_set = list(output_set_str)
char_dict = {}
for i, c in enumerate(output_set):
	char_dict[c] = i

def as_labels(sentence):
	return [char_dict[c] for c in list('^' + sentence + '$')]