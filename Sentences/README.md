# Sentences

This directory serves as a workspace for two main functions. The primary use is the generation of
sentences from YouTube subtitles, to give as labels for our data-collectors. This process will
likely change soon, as we are planning to make a dedicated iOS app for data collection. The
associated resources for this can be found in [Sentences/Generation](Sentences/Generation).

The secondary use is the creation of a lexicon of \~14k words. The lexicon currently only serves to
help in the generation of sentences, but it will eventually be used to inform our language model.

### Subdirectories

* [Generation](Generation): A set of scripts and datasets for generating sentences.
* [Lexicon](Lexicon): Scripts and datasets for generating a (\~14k word) lexicon.
* [Sources](Sources): All of the original source files for the datasets used in sentence/lexicon
	generation.

### Files

* [add_sentence_numbers_script.py](add_sentence_numbers_script.py): Will be deprecated soon.
	Creates 'sentences_annotated.txt', which gives the sentences found in 'sentences.txt' unique
	numerical IDs.
* [make_sentence_dict_script.py](make_sentence_dict_script.py): Constructs 'sentence_dict.json'
	from the list of sentences in order to provide a way to go from sentence ID back to the text of
	the sentence.
* [sets.py](sets.py): Various operations to do with these lists of sentences, mainly for use in
	top-level scripts.
* [sentences.txt](sentences.txt): A list of sentences. For the meantime, this is manually vetted
	from the larger list found in [Sentences/Generation](Sentences/Generation).
* [sentences_annotated.txt](sentences_annotated.txt): Will be deprecated soon. The list of
	sentences, where each one is prefixed by its ID number.
* [sentence_consts.py](sentence_consts.py): Stores various constants (primarily filepaths) used by
	scripts in this directory (and its subdirectories).

##### Not present

* **all_sentence_list.txt**: The output file for the list of sentences created by
	[Generation/make_sentences.py](Generation/make_sentences.py)
* **sentence_dict.json**: A dictionary that maps sentence id to sentence text, stored as JSON.