import os
import time
from heapq import merge
import subprocess

def remove_duplicates(words):
    new_words = [words[0]]
    for i in range(1, len(words)):
        if words[i] != words[i - 1]:
            new_words.append(words[i])
    return new_words

#for f_name in os.listdir('temp'):
#    os.remove('temp/' + f_name)

running_procs = 0
prev_file_count = 0

starting = range(0, len(os.listdir('../pubmed3')), 10)[:-1]
i = 0

while i < len(starting):
    if running_procs < 5:
        subprocess.Popen(['python', 'vocabulary_slave.py', str(starting[i]), str(starting[i] + 10), '0'], stdout=subprocess.DEVNULL)
        subprocess.Popen(['python', 'vocabulary_slave.py', str(starting[i]), str(starting[i] + 10), '1'], stdout=subprocess.DEVNULL)
        subprocess.Popen(['python', 'vocabulary_slave.py', str(starting[i]), str(starting[i] + 10), '2'], stdout=subprocess.DEVNULL)
        running_procs += 3
        i += 1
    if len(os.listdir('temp')) != prev_file_count:
        running_procs -= len(os.listdir('temp')) - prev_file_count
        prev_file_count = len(os.listdir('temp'))
    time.sleep(1)

subprocess.Popen(['python', 'vocabulary_slave.py', str(len(os.listdir('../pubmed3')) - len(os.listdir('../pubmed3')) % 10), str(len(os.listdir('../pubmed3'))), '0'], stdout=subprocess.DEVNULL)
subprocess.Popen(['python', 'vocabulary_slave.py', str(len(os.listdir('../pubmed3')) - len(os.listdir('../pubmed3')) % 10), str(len(os.listdir('../pubmed3'))), '1'], stdout=subprocess.DEVNULL)
subprocess.Popen(['python', 'vocabulary_slave.py', str(len(os.listdir('../pubmed3')) - len(os.listdir('../pubmed3')) % 10), str(len(os.listdir('../pubmed3'))), '2'], stdout=subprocess.DEVNULL)

while (int(len(os.listdir('../pubmed3')) / 10) + 1) * 3 < len(os.listdir('temp')):
    time.sleep(1)

while len(os.listdir('temp')) > 3:
    groups = [[], [], []]
    for f_name in os.listdir('temp'):
        if 'abstract' in f_name:
            groups[0].append(f_name)
        if 'title' in f_name:
            groups[1].append(f_name)
        if 'authors' in f_name:
            groups[2].append(f_name)

    for group in groups:
        while len(group) > 1:
            first_vocab = []
            f = open('temp/' + group[0], 'rb')
            for line in f:
                first_vocab.append(line.decode()[:-1])
            f.close()

            second_vocab = []
            f = open('temp/' + group[1], 'rb')
            for line in f:
                second_vocab.append(line.decode()[:-1])
            f.close()

            final = list(merge(first_vocab, second_vocab))
            first_vocab = []
            second_vocab = []

            vocab_f = open('temp/' + group[0] + '@', 'ab')
            for word in final:
                word = (word + '\n').encode()
                vocab_f.write(word)
            vocab_f.close()

            os.remove('temp/' + group[0])
            os.remove('temp/' + group[1])
            group.remove(group[0])
            group.remove(group[0])


for f_name in os.listdir('temp'):
    words = []
    f = open('temp/' + f_name, 'rb')
    for line in f:
        words.append(line.decode()[:-1])
    f.close()
    words = remove_duplicates(words)
    if 'abstract' in f_name:
        vocab_f = open('temp/abstract_vocabulary', 'ab')
    elif 'title' in f_name:
        vocab_f = open('temp/title_vocabulary', 'ab')
    else:
        vocab_f = open('temp/authors_vocabulary', 'ab')

    for word in words:
        word = (word + '\n').encode()
        vocab_f.write(word)
    vocab_f.close()

    os.remove('temp/' + f_name)