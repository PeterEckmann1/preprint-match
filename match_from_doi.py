from matcher.match import Matcher
from matcher.data_manager import Vectors
from biorxiv import Preprint
import re
import psycopg2
import numpy as np
from tqdm import tqdm


matcher = Matcher('../data')
vectors = Vectors('../data')
conn = psycopg2.connect(dbname='postgres', user='postgres', password='testpass', port=5434)
cur = conn.cursor()


def match_from_doi(dois):
    abstracts = {}
    titles = {}
    authors = {}
    abstract_vectors = []
    title_vectors = []
    used_dois = []
    for i, doi in tqdm(enumerate(dois), total=len(dois)):
        metadata = Preprint(doi, None).get_metadata()
        if metadata['abstract'] == '':
            continue
        used_dois.append(doi)
        abstracts[doi] = metadata['abstract']
        titles[doi] = metadata['title']
        authors[doi] = [re.findall('\\w+$', author)[0] for author in metadata['authors'] if len(re.findall('\\w+$', author)) > 0]
        abstract_vectors.append(vectors.abstract_text_to_vector(metadata['abstract']))
        title_vectors.append(vectors.title_text_to_vector(metadata['title']))
    matches = {}
    for i, paper, abstract_similarity, title_similarity in matcher.match(used_dois, authors, abstracts, titles, np.array(abstract_vectors), np.array(title_vectors), cur, 1000000, 100):
        if paper:
            cur.execute('select doi from papers where id = %s', (paper,))
            matches[dois[i]] = cur.fetchone()[0]
        else:
            matches[dois[i]] = None
    return matches