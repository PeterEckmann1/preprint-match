import requests
import subprocess
import os
from multiprocessing import Pool
from tqdm import tqdm


def download_worker(url):
    file = url.split('/')[-1]
    if file.replace('.gz', '') in os.listdir('pubmed') and file not in os.listdir('pubmed'):
        return
    data = requests.get(url).content
    open('pubmed/' + file, 'wb').write(data)
    subprocess.call(['7z', 'e', '-aoa', 'pubmed/' + file, '-opubmed/'], stdout=subprocess.DEVNULL)
    os.remove('pubmed/' + file)


def get_files(url):
    html = requests.get(url).text
    files = []
    for line in html.split('\n'):
        if '<a href="' in line:
            f_name = line.split('<a href="')[1].split('"')[0]
            if '.xml.gz' in f_name and not '.md5' in f_name:
                files.append(url + f_name)
    return files

#todo check why sometimes hangs on last file
if __name__ == '__main__':
    #download_worker('https://ftp.ncbi.nlm.nih.gov/pubmed/updatefiles/pubmed21n1162.xml')
    urls = get_files('https://ftp.ncbi.nlm.nih.gov/pubmed/baseline/') + get_files('https://ftp.ncbi.nlm.nih.gov/pubmed/updatefiles/')
    with Pool(2) as pool:
        list(tqdm(pool.imap(download_worker, urls), total=len(urls)))