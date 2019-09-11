# This script is only run once, to generate 'lexicon.txt', a vocabulary of ~11000 words. For
# information on the usage of the lexicon, see this directory's README.

word_dict = {}
word_list = []
words = []

# get a list of words, but with duplicates removed (as 5k.txt has a few duplicates)
with open("5k.txt") as f:
	for line in f:
		word = line.rstrip("\n")

		if word not in word_dict:
			word_dict[word] = None
			word_list.append(word)

lemmas = {}
with open("lemmas.txt") as f:
	for line in f:
		halves = line.rstrip("\n").split(" -> ")

		lemmas[halves[0]] = halves[1].split(",")

all_word_dict = {}
all_word_list = []

for word in word_list:
	if word not in all_word_dict:
		all_word_dict[word] = None
		all_word_list.append(word)

	if word in lemmas:
		for w in lemmas[word]:
			if w not in all_word_dict:
				all_word_dict[w] = None
				all_word_list.append(w)

with open("lexicon.txt", "w") as f:
	for word in all_word_list:
		f.write(word + "\n")