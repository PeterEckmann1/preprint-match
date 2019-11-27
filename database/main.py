import os
import subprocess
import psutil
import time


def get_downloaded():
    f = open('downloaded.txt', 'r')
    downloaded = f.read().split(',')
    f.close()
    return downloaded


def delete_database():
    try:
        os.system('del pubmed3\\*.db')
    except:
        os.system('rm pubmed3/*.db')
    f = open('downloaded.txt', 'w')
    f.write('')
    f.close()


def download(num):
    global ps
    if num > 972:
        header = 'ftp://ftp.ncbi.nlm.nih.gov/pubmed/updatefiles/pubmed19n'
    else:
        header = 'ftp://ftp.ncbi.nlm.nih.gov/pubmed/baseline/pubmed19n'

    print('Trying to download')
    try:
        subprocess.call(['curl', header + str(num).zfill(4) + '.xml.gz', '-o', 'temp_file' + str(num) + '.gz'])#, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        print('Download failed')
        print(e)
        return False
    print('Download success')
    print('Running parser')
    ps.append(subprocess.Popen(['python', 'parse_file.py', 'temp_file' + str(num) + '.gz']))
    while len(psutil.Process().children()) > 6:
        print('More than 6 processes running')
        time.sleep(0.1)
        [p.communicate() for p in ps]

    f = open('downloaded.txt', 'a')
    f.write(str(num) + ',')
    f.close()

    return True


try:
    os.system('del *.gz')
except:
    os.system('rm *.gz')

ps = []
#delete_database()
i = 1
while i < 2000:
    print(i)
    attempts = 0
    if not str(i) in get_downloaded():
        print('Starting new file')
        while attempts < 5:
            if download(i):
                break
            else:
                print('Trying again')
                attempts += 1

    i += 1