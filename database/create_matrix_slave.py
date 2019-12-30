import os
import pickle
from scipy.sparse import csr_matrix, save_npz
import bisect
import sys
import numpy as np

vocabulary = []

for f_name in os.listdir('vocabulary/temp'):
    if 'abstract' in f_name and sys.argv[3] == '0':
        f = open('vocabulary/temp/' + f_name, 'rb')
        for line in f:
            vocabulary.append(line.decode()[:-1])
        f.close()

    if 'title' in f_name and sys.argv[3] == '1':
        f = open('vocabulary/temp/' + f_name, 'rb')
        for line in f:
            vocabulary.append(line.decode()[:-1])
        f.close()

    if 'authors' in f_name and sys.argv[3] == '2':
        f = open('vocabulary/temp/' + f_name, 'rb')
        for line in f:
            vocabulary.append(line.decode()[:-1])
        f.close()

paper_count = 0
data = []
row = []
col = []

pmids = []

print('Encoding')
for f_num, f in enumerate(os.listdir('pubmed3')):
    if f_num < int(sys.argv[1]) or f_num >= int(sys.argv[2]):
        continue
    print(f_num, '/', len(os.listdir('pubmed3')))
    f = open('pubmed3/' + f, 'rb')
    papers = pickle.load(f)
    f.close()

    for paper in papers:
        if int(paper['year']) < 2014:
            continue
        if sys.argv[3] == '0':
            for word in paper['abstract_vector'].keys():
                i = bisect.bisect_left(vocabulary, word)
                data.append(paper['abstract_vector'][word])
                row.append(paper_count)
                col.append(i)

        if sys.argv[3] == '1':
            for word in set(paper['title']):
                i = bisect.bisect_left(vocabulary, word)
                data.append(1)
                row.append(paper_count)
                col.append(i)

        if sys.argv[3] == '2':
            for word in set(paper['authors']):
                i = bisect.bisect_left(vocabulary, word)
                data.append(1)
                row.append(paper_count)
                col.append(i)

        paper_count += 1
        pmids.append(paper['pmid'])

print('Saving')
if len(data) == 0:
    if sys.argv[3] == '0':
        open('matrices/abstract' + sys.argv[1] + 'EMPTY.npz', 'w').close()
        open('matrices/abstract' + sys.argv[1] + 'EMPTY_pmids.npz', 'w').close()
    if sys.argv[3] == '1':
        open('matrices/title' + sys.argv[1] + 'EMPTY.npz', 'w').close()
        open('matrices/title' + sys.argv[1] + 'EMPTY_pmids.npz', 'w').close()
    if sys.argv[3] == '2':
        open('matrices/authors' + sys.argv[1] + 'EMPTY.npz', 'w').close()
        open('matrices/authors' + sys.argv[1] + 'EMPTY_pmids.npz', 'w').close()
else:
    if sys.argv[3] == '0':
        save_npz('matrices/abstract' + sys.argv[1], csr_matrix((data, (row, col)), shape=(paper_count, len(vocabulary))))
        np.savez('matrices/abstract' + sys.argv[1] + '_pmids', np.array(pmids))
    if sys.argv[3] == '1':
        save_npz('matrices/title' + sys.argv[1], csr_matrix((data, (row, col)), shape=(paper_count, len(vocabulary))))
        np.savez('matrices/title' + sys.argv[1] + '_pmids', np.array(pmids))
    if sys.argv[3] == '2':
        save_npz('matrices/authors' + sys.argv[1], csr_matrix((data, (row, col)), shape=(paper_count, len(vocabulary))))
        np.savez('matrices/authors' + sys.argv[1] + '_pmids', np.array(pmids))
print('Done')