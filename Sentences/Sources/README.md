# Sources

This directory contains the original version of various files or sets of data currently in use. One
such .zip file cannot be uploaded to github, as it is above the 100MB size limit at time of
writing. It is still mentioned, however.

##### Links

Here are the original links to download the files, in order:

* https://www.wordfrequency.info/free.asp
* https://lexically.net/downloads/BNC_wordlists/e_lemma.txt
* https://www.kaggle.com/datasnaek/youtube-new

### Files

* [5k_original.txt](5k_original.txt): This original list contains "n't" as a word. Because that's
	not compatible with our procedure for generating the lexicon, that line is removed in the copy
	that we use.
* [lemmas_original.txt](lemmas_original.txt): A few different changes were made to the set of
	lemmas (notably: removing the header and adding contractions as full words), so the original is
	still present here for comparison.
* [USvideos.zip](USvideos.zip): This is a zipped CSV of the set of trending YouTube videos over a
	certain time period. We took this from the "youtube-new" dataset linked above. My intuition was
	that popular videos were more likely to have hand-written subtitles and better conversation as
	opposed to random YouTube videos.