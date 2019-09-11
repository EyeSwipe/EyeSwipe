# Lexicon

This directory contains the relevant files for constructing the lexicon ('lexicon.txt'). The
lexicon was originally going to be used for the output layer for our model, but that is no longer
the case. It is currently being used to help with [parsing](../get_sentences_from_subtitles_script.py)
YouTube subtitles into sentences.

Eventually, the lexicon will be used to create our language model to aid with the output
probabilities.

### Creation

The lexicon is created as the product of two lists: the 5000 most frequently used English words,
and a set of lexemes (word families) for a large number of English words (\~14.8k). Word families
are essentially the conjugations of a word (e.g. 'run' -> 'runs', 'ran', and 'running'). Our
lexicon is then composed of each word in the 5k list, in addition to all other words in its lexeme.

Note:
	
* At the top of the list of lemmas are a few other words that were not originally present, mainly
	to include contractions. Other contractions were added in to the list manually. The
	[original list](../Generation/Sources/lemmas_original.txt) can be found in [Generation/Sources](../Generation/Sources).
* '5k.txt' contains some duplicates. Those are accounted for when we create the lexicon.

### Files

* [5k.txt](5k.txt): A list of the 5000 most frequently used English words.
* [lemmas.txt](lemmas.txt): A list of lexemes for the top \~15k headwords.
* [lexicon.txt](lexicon.txt): The lexicon.