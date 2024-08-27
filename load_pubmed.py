from matcher.data_manager import Database, Vectors
from matcher.data_sources import PubMed
from matcher.match import Matcher
import numpy as np
import os
import json


if __name__ == '__main__':
    if os.path.exists('processed_files.json'):
        processed_files = set(json.loads(open('processed_files.json', 'r').read()))
    else:
        processed_files = []
    if not os.path.exists('data/pubmed'):
        os.mkdir('data/pubmed')
    all_files = ['data/pubmed/' + file for file in os.listdir('data/pubmed')]
    print([file for file in all_files if file not in processed_files])
    pubmed = PubMed([file for file in all_files if file not in processed_files])
    db = Database('postgres', 'testpass', port=5434)
    db.delete()
    for i, paper in enumerate(pubmed.stream_papers()):
        db.insert(paper['doi'], paper['title'], paper['abstract'], paper['authors'], paper['affiliations'], date=paper['date'], pmid=paper['pmid'])
        if i % 10001 == 0:
            processed_files = list(set(pubmed.processed_files).union(processed_files))
            open('processed_files.json', 'w').write(json.dumps(processed_files))
    db.commit()
    processed_files = list(set(pubmed.processed_files).union(processed_files))
    open('processed_files.json', 'w').write(json.dumps(processed_files))
    db.generate_word_vectors('data', 1, 1)
    db.apply_word_vectors('data')
    db.generate_matrices('data')
    matcher = Matcher('data', db)
    vectors = Vectors('data')
