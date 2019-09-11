# These are all of the local constants used for lexicon and sentence generation

import os
containing_dir = os.path.dirname(os.path.abspath(__file__))

def wrap(path):
	return os.path.join(containing_dir, path)

lexicon_dir = wrap('Lexicon')
gen_dir = wrap('Generation')

lexicon_file = os.path.join(lexicon_dir, 'lexicon.txt')

sentences_subset = wrap('sentences_subset.txt')
annotated_sentences_file = wrap('sentences_subset_annotated.txt')
sentence_dict_file = wrap('sentence_dict.json')
cleaned_sentences = wrap('sentences.txt')
random_sentence_list = wrap('random_sentences.txt')