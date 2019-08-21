import sqlite3
import os
import subprocess
import time


def get_downloaded():
    f = open('downloaded.txt', 'r')
    downloaded = f.read().split(',')
    f.close()
    return downloaded


def delete_database():
    try:
        os.remove('pubmed.txt')
    except FileNotFoundError:
        pass
    f = open('downloaded.txt', 'w')
    f.write('')
    f.close()


def download(num):
    global processes
    if num > 972:
        header = 'ftp://ftp.ncbi.nlm.nih.gov/pubmed/updatefiles/pubmed19n'
    else:
        header = 'ftp://ftp.ncbi.nlm.nih.gov/pubmed/baseline/pubmed19n'

    try:
        subprocess.check_call(['curl', header + str(num).zfill(4) + '.xml.gz', '-o', 'temp_file' + str(num) + '.gz'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return False

    while True:
        processes = [proc for proc in processes if proc.poll() is None]
        if len(processes) < 5:
            break
        time.sleep(5)

    processes.append(subprocess.Popen(['python3', 'parse_file.py', 'temp_file' + str(num) + '.gz']))

    f = open('downloaded.txt', 'a')
    f.write(str(num) + ',')
    f.close()

    return True


delete_database()

os.system('rm *.gz')
processes = []

i = 1
while True:
    print(i)
    attempts = 0
    if not str(i) in get_downloaded():
        while attempts < 5:
            if download(i):
                break
            else:
                attempts += 1
        if attempts == 5:
            break

    i += 1
