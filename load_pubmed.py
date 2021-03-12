from matcher.data_manager import Database, Vectors
from matcher.data_sources import PubMed
from matcher.match import Matcher
import numpy as np
import os
import json

#todo can become bloated after hundreds of files, need restart, HAVE TO REDO VECTORS
if __name__ == '__main__':
    #processed_files = set(json.loads(open('processed_files.json', 'r').read()))
    #all_files = ['data/pubmed/' + file for file in os.listdir('data/pubmed')]
    #print([file for file in all_files if file not in processed_files])
    #pubmed = PubMed([file for file in all_files if file not in processed_files])
    db = Database('postgres', 'testpass', port=5434)
    #db.delete()
    #for i, paper in enumerate(pubmed.stream_papers()):
    #    db.insert(paper['doi'], paper['title'], paper['abstract'], paper['authors'], paper['date'])
    #    if i % 10001 == 0:
    #        processed_files = list(set(pubmed.processed_files).union(processed_files))
    #        open('processed_files.json', 'w').write(json.dumps(processed_files))
    #db.commit()
    #processed_files = list(set(pubmed.processed_files).union(processed_files))
    #open('processed_files.json', 'w').write(json.dumps(processed_files))
    #db.generate_word_vectors('data', 1)
    #db.apply_word_vectors('data')
    db.generate_matrices('data')
    exit()
    matcher = Matcher('data', db)
    vectors = Vectors('data')

    abstract_vector = vectors.abstract_text_to_vector('In this study of the binding properties of inositol hexaphosphate and 2,3-bisphosphoglycerate to chicken and human deoxyhemoglobin and carboxyhemoglobin were compared. It appeared that in all cases the binding to chicken hemoglobin is much stronger than to human hemoglobin. This is very probably due to the fact that 4 out of the 12 residues, responsible for the binding of phosphates in chicken hemoglobin, are arginines. These are absent in human hemoglobin, where the binding site is made up to only 8 residues. For chicken hemoglobin one strong binding site could be observed in both unliganded and liganded hemoglobin. From these observations we conclude that the same binding site is involved in both the oxy- and deoxy structure showing different affinity to phosphates in the two conformational states. For human hemoglobin we reached the same conclusion.')

    matcher.match(np.array([abstract_vector]), 1000000)