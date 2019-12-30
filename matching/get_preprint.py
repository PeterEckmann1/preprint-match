import nltk
import string
import sys
import requests
import re
import time
from collections import Counter
import bisect
import math
import numpy as np
import pickle

STOPWORDS = set(nltk.corpus.stopwords.words('english'))

def get_vector(paragraph):
    tokens = [token for token in nltk.word_tokenize(paragraph.lower()) if not token in STOPWORDS]
    tokens = [token for token in tokens if not token in string.punctuation]
    counted = Counter(tokens)
    return counted

def get_magnitude(vector):
    return math.sqrt(sum([vector[word] ** 2 for word in vector.keys()]))

def tokenize_title(title):
    title = nltk.word_tokenize(title.lower())
    title = [word for word in title if not word in STOPWORDS and not word in string.punctuation]
    return title

def get(url):
    result = None
    worked = False
    while not worked:
        worked = True
        try:
            result = requests.get(url)
        except:
            print('Waiting 10 seconds...')
            time.sleep(10)
            worked = False
    return result.text

def get_preprint(doi, version):
    preprint = {'authors': [], 'authors_reversed': []}
    title = ''

    day = 0
    month = 0
    year = 0
    html = get('https://www.biorxiv.org/content/' + doi + 'v' + version)

    for line in html.split('\n'):
        if '<span class="nlm-given-names">' in line:
            names = line.split('<span class="nlm-given-names">')
            for name in names[1:]:
                name = name.split('<')[0]
                preprint['authors_reversed'].append(name.split(' ')[0])
            break

    for line in html.split('\n'):
        if '<span class="nlm-surname">' in line:
            names = line.split('<span class="nlm-surname">')
            for name in names[1:]:
                name = name.split('<')[0]
                preprint['authors'].append(name)
            break

    for line in html.split('\n'):
        if '<meta name="DC.Title" content="' in line:
            title = line.split('<meta name="DC.Title" content="')[1]
            title = title.split('"')[0]

        if '<meta name="DC.Date" content=' in line:
            date = line.split('content="')[1]
            date = date.split('"')[0]
            year, month, day = date.split('-')

    reading_abstract = False
    abstract = ''
    for line in html.split('\n'):
        if '<meta name="citation_journal_title" content=' in line and reading_abstract:
            reading_abstract = False

        if '<meta name="citation_abstract" lang=' in line and not reading_abstract:
            reading_abstract = True
            line = line.replace('<meta name="citation_abstract" lang="en" content="', '')

        if reading_abstract:
            abstract += re.sub(r'&lt;.+?&gt;', ' ', line)

    abstract = abstract[:-5][1:].replace('\n', '')

    if 'Abstract' in abstract[0:10]:
        abstract = abstract[10:]
    preprint['title'] = tokenize_title(title)
    preprint['abstract_vector'] = get_vector(abstract)
    preprint['abstract_magnitude'] = get_magnitude(preprint['abstract_vector'])
    preprint['abstract'] = abstract
    preprint['doi'] = doi
    preprint['year'] = int(year)
    preprint['month'] = int(month)
    preprint['day'] = int(day)
    return preprint

def vectorize_abstract(preprint, vocabulary):
    vector = np.zeros((len(vocabulary), 1))
    for word in preprint['abstract_vector'].keys():
        i = bisect.bisect_left(vocabulary, word)
        if i != len(vocabulary) and vocabulary[i] == word:
            vector[i] = preprint['abstract_vector'][word]
    return vector

def vectorize_title_and_authors(words, vocabulary):
    vector = np.zeros((len(vocabulary), 1))
    for word in words:
        i = bisect.bisect_left(vocabulary, word)
        if i != len(vocabulary) and vocabulary[i] == word:
            vector[i] = 1
    return vector

def get_latest_version(doi):
    i = 1
    while not 'html not-front not-logged-in page-error page-error-not-found context-error hw-default-jcode-biorxiv' in get('https://www.biorxiv.org/content/' + doi + 'v' + str(i)):
        i += 1
    return i - 1


doi = sys.argv[1]
try:
    version = sys.argv[2]
except IndexError:
    version = get_latest_version(doi)

preprint = get_preprint(doi, str(version))

vocabulary = []
f = open('database/vocabulary/temp/abstract_vocabulary', 'rb')
for line in f:
    vocabulary.append(line.decode()[:-1])
f.close()
preprint_abstract = vectorize_abstract(preprint, vocabulary)

vocabulary = []
f = open('database/vocabulary/temp/title_vocabulary', 'rb')
for line in f:
    vocabulary.append(line.decode()[:-1])
f.close()
preprint_title = vectorize_title_and_authors(preprint['title'], vocabulary)

vocabulary = []
f = open('database/vocabulary/temp/authors_vocabulary', 'rb')
for line in f:
    vocabulary.append(line.decode()[:-1])
f.close()
preprint_authors = vectorize_title_and_authors(preprint['authors'], vocabulary)
vocabulary = []

abstract_norm = np.linalg.norm(preprint_abstract)
title_sum = np.sum(preprint_title)
authors_sum = np.sum(preprint_authors)

f = open('matching/preprints/' + str(preprint['doi']).replace('/', '_'), 'wb')
pickle.dump([np.array(preprint_abstract), abstract_norm, np.array(preprint_title), title_sum, np.array(preprint_authors), authors_sum], f)
f.close()