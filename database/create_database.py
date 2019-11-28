import numpy as np
import scipy.sparse
import os
import pickle
import time
import bisect

vocabulary = []
data = []
row = []
col = []
paper_count = 0
file_num = 0

try:
    os.system('del matrices\\*.npz')
    os.system('del matrices\\*.p')
except:
    os.system('rm matrices/*.npz')
    os.system('rm matrices/*.p')

for f_num, f in enumerate(os.listdir('pubmed3')):
    print(f_num, '/', len(os.listdir('pubmed3')))
    f = open('pubmed3/' + f, 'rb')
    papers = pickle.load(f)
    f.close()

    for n, paper in enumerate(papers):
        for word in paper['abstract_vector'].keys():
            i = bisect.bisect_left(vocabulary, word)

            if i == len(vocabulary) or vocabulary[i] != word:
                vocabulary.insert(i, word)

            data.append(paper['abstract_vector'][word])
            row.append(paper_count)
            col.append(i)
        paper_count += 1

    if (f_num % 10 == 0 and f_num != 0) or f_num == len(os.listdir('pubmed3')) - 1:
        print('Saving')
        matrix = scipy.sparse.csr_matrix((data, (row, col)), shape=(paper_count, len(vocabulary)))
        scipy.sparse.save_npz('matrices/matrix' + str(file_num), matrix)

        vocab_f = open('matrices/vocab' + str(file_num) + '.p', 'wb')
        pickle.dump(vocabulary, vocab_f)
        vocab_f.close()

        file_num += 1
        vocabulary = []
        data = []
        row = []
        col = []
        paper_count = 0