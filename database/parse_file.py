import gzip
import sys
import os
import math
from collections import Counter
import string
import nltk
import pickle


STOPWORDS = set(nltk.corpus.stopwords.words('english'))

MAIN_DELIM = '{MainDelim}'
SUB_DELIM = '{SubDelim}'
SUB_SUB_DELIM = '{SubSubDelim}'


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


filename = sys.argv[1]
f = gzip.open(filename)

papers = []
delete = False
to_delete = []

for line in f:
    line = line.decode('utf-8')
    line = line.replace(MAIN_DELIM, '')
    line = line.replace(SUB_DELIM, '')
    line = line.replace(SUB_SUB_DELIM, '')
    if '<PubmedArticle>' in line:
        papers.append({'title': '', 'abstract': '', 'pmid': '', 'year': '', 'month': '', 'day': '', 'authors': []})

    if '<ArticleTitle>' in line:
        title = line.split('<ArticleTitle>')[1]
        title = title.split('</ArticleTitle>')[0]
        papers[-1]['title'] = title
        papers[-1]['title_full'] = title

    if 'AbstractText' in line:
        line = line.replace('<i>', '')
        line = line.replace('</i>', '')
        line = line.replace('<sub>', '')
        line = line.replace('</sub>', '')
        line = line.replace('<sup>', '')
        line = line.replace('</sup>', '')
        line = line.replace('<b>', '')
        line = line.replace('</b>', '')
        line = line.replace('<u>', '')
        line = line.replace('</u>', '') 
        abstract = line.split('>')[1]
        abstract = abstract.split('</AbstractText')[0]
        papers[-1]['abstract'] += abstract + ' '

    if '<LastName>' in line:
        name = line.split('<LastName>')[1]
        name = name.split('</LastName>')[0]
        papers[-1]['authors'].append(name)

    if '<PMID Version="1">' in line:
        pmid = line.split('>')[1]
        pmid = pmid.split('<')[0]
        if delete:
            to_delete.append([pmid])
        else:
            papers[-1]['pmid'] = pmid

    if '<Year>' in line:
        year = line.split('>')[1]
        year = year.split('<')[0]
        papers[-1]['year'] = year

    if '<Month>' in line:
        month = line.split('>')[1]
        month = month.split('<')[0]
        papers[-1]['month'] = month

    if '<Day>' in line:
        day = line.split('>')[1]
        day = day.split('<')[0]
        papers[-1]['day'] = day

    if '<DeleteCitation>' in line:
        delete = True


f.close()
#ADD TO_DELETE FUNCTIONALITY
final_papers = []
for paper in papers:
    paper['title'] = tokenize_title(paper['title'])
    paper['abstract_vector'] = get_vector(paper['abstract'])
    paper['abstract_magnitude'] = get_magnitude(paper['abstract_vector'])
    final_papers.append(paper)

f = open('pubmed3/' + filename + '.db', 'wb')
pickle.dump(final_papers, f)
f.close()

os.remove(filename)