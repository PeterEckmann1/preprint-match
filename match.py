import math
import nltk
import string
import sys
import requests
import re
import time
from collections import Counter
import os
import pickle
import scipy.sparse
import numpy as np
import bisect
import warnings

warnings.filterwarnings('ignore')

STOPWORDS = set(nltk.corpus.stopwords.words('english'))

MAIN_DELIM = '{MainDelim}'
SUB_DELIM = '{SubDelim}'
SUB_SUB_DELIM = '{SubSubDelim}'


def combine(first, second, third):
    return (first) + (math.tanh(3 * second) - math.exp(-55 * second ** 2)) + (math.tanh(3 * third) + math.exp(-500 * (third - 1) ** 2))

def author_similarity(paper):
    return max([len(set(paper['authors']).intersection(preprint['authors'])) / len(set(paper['authors']).union(preprint['authors'])), len(set(paper['authors']).intersection(preprint['authors_reversed'])) / len(set(paper['authors']).union(preprint['authors_reversed']))])

def title_similarity(paper):
    return len(set(preprint['title']).intersection(paper['title'])) / len(set(preprint['title']).union(paper['title']))

def abstract_similarity(paper):
    product = sum([preprint['abstract_vector'][word] * paper['abstract_vector'][word] for word in preprint['abstract_vector'].keys() if word in paper['abstract_vector'].keys()])
    magnitude = preprint['abstract_magnitude'] * paper['abstract_magnitude']
    if magnitude == 0:
        return 0
    else:
        return product / magnitude


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
    if abstract == '':
        print('BioRxiv abstract empty?')

    pubmed = get('https://connect.biorxiv.org/bx_pub_doi_get.php?doi=' + doi)

    cont = False
    if 'pub_doi' in pubmed:
        pubmed = pubmed.split('"pub_doi":"')[1]
        pubmed = pubmed.split('"')[0]
        pubmed = pubmed.replace('\\', '')
        json = get('https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?ids=' + pubmed + '&versions=no&format=json')
        for line in json.split('\n'):
            if '"pmid"' in line:
                pubmed = line.split('"')[-2]
                cont = True

    else:
        cont = True
        pubmed = None

    if not cont:
        print('Published, but could not find PMID from DOI')
        exit(0)

    if 'Abstract' in abstract[0:10]:
        abstract = abstract[10:]
    preprint['pubmed_pmid'] = pubmed
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

doi = sys.argv[1]
version = sys.argv[2]
if '--before' in sys.argv or '-b' in sys.argv:
    before = True
else:
    before = False

print('Fetching preprint from BioRxiv')
preprint = get_preprint(doi, version)

f = open('svm_model', 'rb')
model = pickle.load(f)
f.close()

max_val = -3
max_pmid = ''

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

print('Begin searching')
t = time.time()
for i in range(0, int(len(os.listdir('database/matrices'))) * 100, 100):
    try:
        abstract_matrix = scipy.sparse.load_npz('database/matrices/abstract' + str(i) + '.npz')
        title_matrix = scipy.sparse.load_npz('database/matrices/title' + str(i) + '.npz')
        authors_matrix = scipy.sparse.load_npz('database/matrices/authors' + str(i) + '.npz')
    except FileNotFoundError:
        continue

    print(i)

    abstract_vector = np.load('database/matrices/abstract' + str(i) + '_vector.npz')['arr_0']
    title_vector = np.load('database/matrices/title' + str(i) + '_vector.npz')['arr_0']
    authors_vector = np.load('database/matrices/authors' + str(i) + '_vector.npz')['arr_0']

    abstract_sim = np.squeeze(abstract_matrix.dot(preprint_abstract)) / (abstract_norm * abstract_vector)
    abstract_sim = np.nan_to_num(abstract_sim)

    dot = title_matrix.dot(preprint_title)
    title_sim = np.squeeze(np.array(dot / (title_sum + title_vector - dot)))
    title_sim = np.nan_to_num(title_sim)

    dot = authors_matrix.dot(preprint_authors)
    authors_sim = np.squeeze(np.array(dot / (authors_sum + authors_vector - dot)))
    authors_sim = np.nan_to_num(authors_sim)

    predictions = model.predict(np.array([abstract_sim, authors_sim, title_sim]).T)
    for paper_num, prediction in enumerate(predictions):
        if prediction:
            print('match')
            val = combine(abstract_sim[paper_num], authors_sim[paper_num], title_sim[paper_num])
            if val > max_val:
                max_val = val
                pmids = np.load('database/matrices/' + str(i) + '_pmids.npz')['arr_0']
                max_pmid = pmids[paper_num]

print(time.time() - t)
if max_pmid == '':
    print('unpublished')
    
print('final', preprint['doi'], preprint['pubmed_pmid'], max_pmid, max_val)

#preprint doi, preprint title, preprint abstract, preprint authors, announced pmid, announced title, announced abstract, announced authors, matched pmid, matched title, matched abstract, matched authors
#csv = [preprint['doi'], ' '.join(preprint['title']), preprint['abstract'], ','.join(preprint['authors']), announced['pmid'], ' '.join(announced['title']), announced['abstract'], ','.join(announced['authors']), max_paper['pmid'], ' '.join(max_paper['title']), max_paper['abstract'], ','.join(max_paper['authors'])]
#csv = ['"' + string.replace('"', "'") + '"' for string in csv]
#csv = ','.join(csv)
#csv = csv.replace('\n', '')
#print('csv', end=' ')
#for char in csv:
#    try:
#        print(char, end='')
#    except UnicodeEncodeError:
#        pass