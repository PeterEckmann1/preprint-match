import math
import nltk
import string
import sys
import requests
import re
import time
import sqlite3
from collections import Counter


STOPWORDS = set(nltk.corpus.stopwords.words('english'))


def combine(first, second, third):
    return (first) + (math.tanh(3 * second) - math.exp(-55 * second ** 2)) + (math.tanh(3 * third) + math.exp(-500 * (third - 1) ** 2))

def author_similarity(paper):
    return len(set(paper['authors']).intersection(preprint['authors'])) / len(set(paper['authors']).union(preprint['authors']))

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
    preprint = {'authors': []}
    title = ''

    day = 0
    month = 0
    year = 0
    html = get('https://www.biorxiv.org/content/' + doi + 'v' + version)

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

        if reading_abstract:
            abstract += re.sub(r'&lt;.+?&gt;', ' ', line)

        if '<meta name="citation_abstract" lang=' in line and not reading_abstract:
            reading_abstract = True

    abstract = abstract[:-5][1:].replace('\n', '')

    pubmed = get('https://connect.biorxiv.org/bx_pub_doi_get.php?doi=' + doi)

    if 'pub_doi' in pubmed:
        pubmed = pubmed.split('"pub_doi":"')[1]
        pubmed = pubmed.split('"')[0]
        pubmed = pubmed.replace('\\', '')
        json = get('https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?ids=' + pubmed + '&versions=no&format=json')
        for line in json.split('\n'):
            if '"pmid"' in line:
                pubmed = line.split('"')[-2]
                break

    else:
        pubmed = None

    preprint['pubmed_pmid'] = pubmed
    preprint['title'] = tokenize_title(title)
    preprint['abstract_vector'] = get_vector(abstract)
    preprint['abstract_magnitude'] = get_magnitude(preprint['abstract_vector'])
    preprint['doi'] = doi
    preprint['year'] = int(year)
    preprint['month'] = int(month)
    preprint['day'] = int(day)

    return preprint


version = '1'
try:
    version = sys.argv[2]
except:
    pass

preprint = get_preprint('10.1101/737734', version)#sys.argv[1], version)

max_val = -2
max_paper = {}

f = open('pubmed.txt', 'rb')

for row in f:
    row = row.decode('utf-8').split('?~V~Q')
    paper = {}
    paper['pmid'] = row[0]
    paper['title'] = row[1].split('▓')
    paper['abstract_vector'] = {}
    for word in row[2].split('▓'):
        if '░' in word:
            paper['abstract_vector'][word.split('░')[0]] = float(word.split('░')[1])
    paper['abstract_magnitude'] = float(row[3])
    paper['year'] = int(row[4])
    paper['month'] = int(row[5])
    paper['day'] = int(row[6])
    paper['authors'] = row[7].split('▓')
    print(paper)

    val = combine(abstract_similarity(paper), author_similarity(paper), title_similarity(paper))
    if val > max_val:
        max_val = val
        max_paper = paper
        print(paper)

print(preprint['doi'], max_paper['pmid'], max_val, preprint['pubmed_pmid'])
