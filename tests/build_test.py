import nltk
from collections import Counter
import string
import pickle
import numpy as np
import bisect
import os

STOPWORDS = set(nltk.corpus.stopwords.words('english'))


def get_vector(paragraph):
    tokens = [token for token in nltk.word_tokenize(paragraph.lower()) if not token in STOPWORDS]
    tokens = [token for token in tokens if not token in string.punctuation]
    counted = Counter(tokens)
    return counted

def vectorize_abstract(words, vocabulary):
    vector = np.zeros((len(vocabulary), 1))
    for word in words.keys():
        i = bisect.bisect_left(vocabulary, word)
        if i != len(vocabulary) and vocabulary[i] == word:
            vector[i] = words[word]
    return vector

def read(f_name):
    vals = []
    f = open(f_name, 'r')
    for line in f:
        vals.append(line.replace('\n', ''))
    return vals

def vectorize_title_and_authors(words, vocabulary):
    vector = np.zeros((len(vocabulary), 1))
    for word in words:
        i = bisect.bisect_left(vocabulary, word)
        if i != len(vocabulary) and vocabulary[i] == word:
            vector[i] = 1
    return vector

for f_name in os.listdir('test_preprints'):
    os.remove('test_preprints/' + f_name)

abstract_vocabulary = []
f = open('../database/vocabulary/temp/abstract_vocabulary', 'rb')
for line in f:
    abstract_vocabulary.append(line.decode()[:-1])
f.close()

title_vocabulary = []
f = open('../database/vocabulary/temp/title_vocabulary', 'rb')
for line in f:
    title_vocabulary.append(line.decode()[:-1])
f.close()

authors_vocabulary = []
f = open('../database/vocabulary/temp/authors_vocabulary', 'rb')
for line in f:
    authors_vocabulary.append(line.decode()[:-1])
f.close()

biorxiv_pmidss = read('biorxiv_pmids.txt')
preprint_abstracts = read('preprint_abstract.txt')
preprint_authorss = read('preprint_authors.txt')
preprint_doiss = read('preprint_dois.txt')
preprint_titles = read('preprint_title.txt')
test_pmidss = read('test_pmids.txt')

for i in range(len(biorxiv_pmidss)):
    print(i)
    preprint_abstract = vectorize_abstract(get_vector(preprint_abstracts[i]), abstract_vocabulary)
    preprint_title = vectorize_title_and_authors(preprint_titles[i].split(' '), title_vocabulary)
    preprint_authors = vectorize_title_and_authors(preprint_authorss[i].split(','), authors_vocabulary)

    abstract_norm = np.linalg.norm(preprint_abstract)
    title_sum = np.sum(preprint_title)
    authors_sum = np.sum(preprint_authors)

    if biorxiv_pmidss[i] == '':
        biorxiv_pmidss[i] = '-1'

    if test_pmidss[i] == '':
        test_pmidss[i] = '-1'

    f = open('test_preprints/' + preprint_doiss[i].replace('/', '_') + ',' + biorxiv_pmidss[i] + ',' + test_pmidss[i], 'wb')
    pickle.dump([np.array(preprint_abstract), abstract_norm, np.array(preprint_title), title_sum, np.array(preprint_authors), authors_sum], f)
    f.close()