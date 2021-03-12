from matcher.data_manager import Database
import requests
import string


db = Database('postgres', 'testpass', port=5433)

db.cur.execute(open('queries/true_positives.sql', 'r').read().format(open('queries/get_data.sql', 'r').read()))
print('true positives:', db.cur.fetchone()[0])

db.cur.execute(open('queries/false_positives.sql', 'r').read().format(open('queries/get_data.sql', 'r').read()))
print('false positives:', db.cur.fetchone()[0])

false_negatives = 0
db.cur.execute(open('queries/false_negatives.sql', 'r').read().format(open('queries/get_data.sql', 'r').read()))
for paper_doi, title in db.cur:
    real_title = requests.get(f'https://api.crossref.org/works/{paper_doi}').json()['message']['title'][0]
    norm = lambda text : ''.join([char for char in text.lower() if char in string.ascii_lowercase])
    if norm(title) == norm(real_title):
        false_negatives += 1
print('false negatives:', false_negatives)

db.cur.execute(open('queries/true_negatives.sql', 'r').read().format(open('queries/get_data.sql', 'r').read()))
print('true negatives:', db.cur.fetchone()[0])