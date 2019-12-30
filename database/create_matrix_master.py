import subprocess
import os
import time
import scipy.sparse
import numpy as np

os.system('del matrices\\*.npz')
os.system('rm matrices/*.npz')

running_procs = 0
prev_file_count = 0

starting = range(0, len(os.listdir('pubmed3')), 100)[:-1]
i = 0

while i < len(starting):
    if running_procs < 1: 
        subprocess.Popen(['python', 'create_matrix_slave.py', str(starting[i]), str(starting[i] + 100), '0'])
        subprocess.Popen(['python', 'create_matrix_slave.py', str(starting[i]), str(starting[i] + 100), '1'])
        subprocess.Popen(['python', 'create_matrix_slave.py', str(starting[i]), str(starting[i] + 100), '2'])
        running_procs += 3
        i += 1

    if len(os.listdir('matrices')) / 2 != prev_file_count:
        running_procs -= len(os.listdir('matrices')) / 2 - prev_file_count
        prev_file_count = len(os.listdir('matrices')) / 2

    time.sleep(1)

subprocess.Popen(['python', 'create_matrix_slave.py', str(len(os.listdir('pubmed3')) - len(os.listdir('pubmed3')) % 100), str(len(os.listdir('pubmed3'))), '0'])
subprocess.Popen(['python', 'create_matrix_slave.py', str(len(os.listdir('pubmed3')) - len(os.listdir('pubmed3')) % 100), str(len(os.listdir('pubmed3'))), '1'])
subprocess.Popen(['python', 'create_matrix_slave.py', str(len(os.listdir('pubmed3')) - len(os.listdir('pubmed3')) % 100), str(len(os.listdir('pubmed3'))), '2'])

while int(len(os.listdir('matrices')) / 6) * 100 < len(os.listdir('pubmed3')):
    time.sleep(1)

for f_name in os.listdir('matrices'):
    if 'pmids' in f_name:
        if 'abstract' in f_name:
            os.rename('matrices/' + f_name, 'matrices/' + f_name[8:])
        else:
            os.remove('matrices/' + f_name)
    elif not 'EMPTY' in f_name:
        matrix = scipy.sparse.load_npz('matrices/' + f_name)
        if 'abstract' in f_name:
            vector = np.squeeze(np.array(np.sqrt(matrix.power(2).sum(axis=1))))
        else:
            vector = matrix.sum(axis=1)
        np.savez('matrices/' + f_name.replace('.npz', '_vector'), vector)