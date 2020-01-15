import subprocess
import sys
import os
import time

def make_dir(name):
    try:
        os.mkdir(name)
    except:
        pass

make_dir('results')
make_dir('test_database')
make_dir('test_database/matrices')

for f_name in os.listdir('matching/preprints'):
    os.remove('matching/preprints/' + f_name)
for f_name in os.listdir('results'):
    os.remove('results/' + f_name)

if len(sys.argv) > 1:
    if sys.argv[1] == '-t' or sys.argv[1] == '--test':
        print('Testing mode')
        if os.listdir('tests/
    else:
        print('Fetching preprints')
        dois = []
        f = open(sys.argv[1], 'r')
        for line in f:
            dois.append(line[:-1])
        f.close()

        running_procs = 0
        prev = 0
        i = 0
        while i < len(dois):
            if running_procs < 8:
                subprocess.Popen(['python', 'matching/get_preprint.py', dois[i]])
                i += 1
                running_procs += 1
            if len(os.listdir('matching/preprints')) > prev:
                running_procs -= len(os.listdir('matching/preprints')) - prev
                prev = len(os.listdir('matching/preprints'))

        while len(os.listdir('matching/preprints')) < len(dois):
            time.sleep(1)
else:
    print('Invalid command line arguments')
    exit(0)

time.sleep(1)

if len(sys.argv) > 1 and (sys.argv[1] == '-t' or sys.argv[1] == '--test'):
    result_num = 0
    while len(os.listdir('tests/test_preprints')) > 0:
        print(len(os.listdir('tests/test_preprints')))
        subprocess.call(['python', 'matching/match.py', '-t'])
        os.rename('results/results', 'results/results' + str(result_num))
        result_num += 1
else:
    result_num = 0
    while len(os.listdir('matching/preprints')) > 0:
        subprocess.call(['python', 'matching/match.py'])
        os.rename('results/results', 'results/results' + str(result_num))
        result_num += 1

passed = True
if len(sys.argv) > 1 and (sys.argv[1] == '-t' or sys.argv[1] == '--test'):
    for f_name in os.listdir('results'):
        if 'results' in f_name:
            f = open('results/' + f_name, 'r')
            for line in f:
                line = line[:-1].split(' ')
                if line[2] == '31000691' or line[2] == '31772203' or line[2] == '31758551' or line[2] == '29806908' or line[2] == '29343502' or line[2] == '29263382' or line[2] == '29465398' or line[2] == '31760159' or line[2] == '31770461':
                    continue
                if line[2] != line[4]:
                    passed = False

    print('Tests passed:', passed)
else:
    for f_name in os.listdir('results'):
        f = open('results/' + f_name, 'r')
        for line in f:
            sub_f = open('results/' + line.split(' ')[0].replace('/', '_'), 'w')
            sub_f.write(line.split(' ')[2])
            sub_f.close()
        f.close()
        os.remove('results/' + f_name)
