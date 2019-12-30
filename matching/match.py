import math
import os
import pickle
import scipy.sparse
import numpy as np
import warnings
import time
import sys

warnings.filterwarnings('ignore')

if len(sys.argv) > 1 and sys.argv[1] == '-t':
    MATRICES_DIR = 'tests/test_database/matrices'
    PREPRINT_DIR = 'tests/test_preprints'
else:
    MATRICES_DIR = 'database/matrices'
    PREPRINT_DIR = 'matching/preprints'

def combine(first, second, third):
    return (first) + (math.tanh(3 * second) - math.exp(-55 * second ** 2)) + (math.tanh(3 * third) + math.exp(-500 * (third - 1) ** 2))


preprints = []
preprint_dois = []
preprint_pmids = []
test_pmids = []
print('Reading preprints')
for f_name in os.listdir(PREPRINT_DIR)[:50]:
    if len(f_name.split(',')) > 1:
        preprint_pmids.append(f_name.split(',')[1])
        test_pmids.append(f_name.split(',')[2])
    preprint_dois.append(f_name.split(',')[0].replace('_', '/'))
    f = open(PREPRINT_DIR + '/' + f_name, 'rb')
    preprints.append(pickle.load(f))
    f.close()
    os.remove(PREPRINT_DIR + '/' + f_name)
print(len(preprint_dois), 'preprints read')

f = open('matching/svm_model', 'rb')
model = pickle.load(f)
f.close()

max_vals = np.full((len(preprints)), -3.)
max_pmids = np.full((len(preprints)), -1)

print('Begin searching')
t = time.time()
for i in range(0, int(len(os.listdir(MATRICES_DIR))) * 100, 100):
    try:
        abstract_matrix = scipy.sparse.load_npz(MATRICES_DIR + '/abstract' + str(i) + '.npz')
        title_matrix = scipy.sparse.load_npz(MATRICES_DIR + '/title' + str(i) + '.npz')
        authors_matrix = scipy.sparse.load_npz(MATRICES_DIR + '/authors' + str(i) + '.npz')
    except FileNotFoundError:
        continue

    abstract_vector = np.load(MATRICES_DIR + '/abstract' + str(i) + '_vector.npz')['arr_0']
    title_vector = np.load(MATRICES_DIR + '/title' + str(i) + '_vector.npz')['arr_0']
    authors_vector = np.load(MATRICES_DIR + '/authors' + str(i) + '_vector.npz')['arr_0']

    pmids = np.load(MATRICES_DIR + '/' + str(i) + '_pmids.npz')['arr_0']

    print(i)

    preprint_num = 0
    for preprint_abstract, abstract_norm, preprint_title, title_sum, preprint_authors, authors_sum in preprints:
        abstract_sim = np.squeeze(abstract_matrix.dot(preprint_abstract)) / (abstract_norm * abstract_vector)
        abstract_sim = np.nan_to_num(abstract_sim)

        dot = title_matrix.dot(preprint_title)
        title_sim = np.squeeze(np.array(dot / (title_sum + title_vector - dot)))
        title_sim = np.nan_to_num(title_sim)

        dot = authors_matrix.dot(preprint_authors)
        authors_sim = np.squeeze(np.array(dot / (authors_sum + authors_vector - dot)))
        authors_sim = np.nan_to_num(authors_sim)

        predictions = model.predict(np.array([abstract_sim, authors_sim, title_sim]).T)
        for paper_num in np.array(np.nonzero(predictions))[0]:
            val = combine(abstract_sim[paper_num], authors_sim[paper_num], title_sim[paper_num])
            if val > max_vals[preprint_num]:
                max_vals[preprint_num] = val
                max_pmids[preprint_num] = pmids[paper_num]
        preprint_num += 1
print(time.time() - t)

open('results/results', 'w').close()
f = open('results/results', 'a')
for i in range(len(max_vals)):
    if len(sys.argv) > 1 and sys.argv[1] == '-t':
        f.write(str(preprint_dois[i]) + ' ' + str(preprint_pmids[i]) + ' ' + str(max_pmids[i]) + ' ' + str(max_vals[i]) + ' ' + test_pmids[i] + '\n')
    else:
        f.write(str(preprint_dois[i]) + ' ' + '_' + ' ' + str(max_pmids[i]) + ' ' + str(max_vals[i]) + ' ' + '_' + '\n')
f.close()