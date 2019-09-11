# Filters the sentences in 'sentences_all.txt' to only include those that match certain criteria.
# Those are listed below. The resulting list of sentences is then written to
# 'Sentences/sentences.txt', the final list.

import re
import sys

import gen_consts as gconsts

# import 'sentence_consts' from the parent directory
from os.path import abspath, join, dirname
sys.path.append(abspath(join(dirname(abspath(__file__)), '..')))
import sentence_consts as sconsts

# returns whether the sentence should be kept
def filter_sentence(s):
	num_words = len(s.split(' '))
	if num_words < gconsts.lower_bound or num_words > gconsts.upper_bound:
		return False

	return True

with open(gconsts.all_sentences) as f:
	sentences = f.read().split('\n')

as_string = '\n'.join(filter(filter_sentence, sentences))
with open(sconsts.cleaned_sentences, 'w') as f:
	f.write(as_string + '\n')
