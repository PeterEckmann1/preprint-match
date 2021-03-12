from matcher.data_manager import Database
import requests
from string import ascii_lowercase


def normalize(string):
    return ''.join([char for char in string.lower() if char in ascii_lowercase])


db = Database('postgres', 'testpass', port=5434)
db.cur.execute('select preprint_doi, biorxiv.doi, biorxiv.title, biorxiv.abstract from matches_final left join prod.articles on articles.doi = preprint_doi left join prod.article_publications on article_publications.article = articles.id left join papers as algorithm on algorithm.id = paper_id left join papers as biorxiv on biorxiv.doi = article_publications.doi where biorxiv.doi is not null and algorithm.doi is null')
for preprint_doi, paper_doi, apparent_title, abstract in db.cur.fetchall():
    if abstract == '':
        db.cur.execute('update matches_final set is_valid = false where preprint_doi = %s', (preprint_doi,))
        continue
    real_title = requests.get(f'https://api.crossref.org/works/{paper_doi}', params={'mailto': 'petereckmann@gmail.com'}).json()['message']['title'][0]
    if normalize(apparent_title) != normalize(real_title):
        db.cur.execute('update matches_final set is_valid = false where preprint_doi = %s', (preprint_doi,))
db.conn.commit()