import sys
import pickle
import bisect
import os

vocabulary = []

for f_num, f in enumerate(os.listdir('../pubmed3')[int(sys.argv[1]): int(sys.argv[2])]):
    print(f_num, '/', len(os.listdir('../pubmed3')), sys.argv[3])
    f = open('../pubmed3/' + f, 'rb')
    papers = pickle.load(f)
    f.close()

    for paper in papers:
        if int(paper['year']) < 2014:
            continue

        if sys.argv[3] == '0':
            for word in paper['abstract_vector'].keys():
                i = bisect.bisect_left(vocabulary, word)

                if i == len(vocabulary) or vocabulary[i] != word:
                    vocabulary.insert(i, word)

        elif sys.argv[3] == '1':
            for word in paper['title']:
                i = bisect.bisect_left(vocabulary, word)

                if i == len(vocabulary) or vocabulary[i] != word:
                    vocabulary.insert(i, word)

        elif sys.argv[3] == '2':
            for word in paper['authors']:
                i = bisect.bisect_left(vocabulary, word)

                if i == len(vocabulary) or vocabulary[i] != word:
                    vocabulary.insert(i, word)

        else:
            print('incorrect mode')
            exit(0)

if sys.argv[3] == '0':
    vocab_f = open('temp/abstract_vocabulary' + sys.argv[1], 'ab')
elif sys.argv[3] == '1':
    vocab_f = open('temp/title_vocabulary' + sys.argv[1], 'ab')
else:
    vocab_f = open('temp/authors_vocabulary' + sys.argv[1], 'ab')

for word in vocabulary:
    word = (word + '\n').encode()
    vocab_f.write(word)
vocab_f.close()