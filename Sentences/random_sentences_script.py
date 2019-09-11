import os
import random
import sys
import random

import sentence_consts as consts

to_file = None

if len(sys.argv) != 2:
	print("Expected argument for number of sentences to get")
	sys.exit()
	
sys.stdout.write("Would you like to output to a file? (y/n): ")
sys.stdout.flush()
while True:
	response = sys.stdin.readline().strip()

	if response == 'y':
		to_file = True
		break
	elif response == 'n':
		to_file = False
		break

	sys.stdout.write("Please enter 'y' or 'n'. To file? (y/n): ")

with open(consts.cleaned_sentences) as f:
	sentences = f.read().split('\n')

num_get = int(sys.argv[1])
random_set = random.sample(sentences, num_get)
as_string = '\n'.join(random_set)

if to_file:
	with open(consts.random_sentence_list, 'w') as f:
		f.write(as_string + '\n')
else:
	print(as_string)
