from matcher.match import Matcher
from matcher.data_manager import Database
from secrets import token_urlsafe
import numpy as np
import psycopg2.extras

#todo lowercase only preprocessing DONT FORGET TO ADD, literally just check if first letters of abstract match using postgres, use bigger vector length

db = Database('postgres', 'testpass', port=5434)
conn1 = psycopg2.connect(dbname='postgres', user='postgres', password='testpass', port=5434)
cur1 = conn1.cursor()
#vectors = Vectors('data')

#biorxiv = bioRxiv(db)
#psycopg2.extras.execute_values(cur1, 'insert into preprint_vectors values %s', [(paper['doi'], vectors.title_text_to_vector(paper['title']).tolist(), vectors.abstract_text_to_vector(paper['abstract']).tolist()) for paper in biorxiv.stream_papers()], page_size=1000)
#conn1.commit()

matcher = Matcher('data', db)

cur = db.conn.cursor(token_urlsafe(20))
cur.execute("select articles.id, preprint_vectors.doi, preprint_vectors.title_vector, preprint_vectors.abstract_vector from preprint_vectors inner join prod.articles on articles.doi = preprint_vectors.doi order by random()")

step = 1000
dois = []
abstracts = np.zeros((step, 300), dtype=np.float32)
titles = np.zeros((step, 300), dtype=np.float32)
i = 0
total = 0
for row in cur:
    dois.append(row[1])
    titles[i] = np.array(row[2])
    abstracts[i] = np.array(row[3])
    i += 1
    if i == step:
        for doi_index, paper_id, abstract_similarity, title_similarity in matcher.match(dois, abstracts, titles, cur1, 1000000, 100, threads=6):
            cur1.execute('insert into matches_final values (%s, %s, %s, %s)', (dois[doi_index], paper_id, abstract_similarity, title_similarity))
        conn1.commit()
        dois = []
        i = 0
        total += 1
        if total == 5:
            break


"""
select 
	preprint_doi,
	articles.title,
	biorxiv.title,
	articles.abstract,
	biorxiv.abstract,
	is_valid
from matches_final
left join prod.articles
	on articles.doi = preprint_doi
left join prod.article_publications
	on article_publications.article = articles.id
left join papers as algorithm
	on algorithm.id = paper_id
left join papers as biorxiv
	on biorxiv.doi = article_publications.doi
where 
	article_publications.doi is not null 
	and algorithm.doi is null
	and biorxiv.title is not null
	and (is_valid or is_valid is null)
"""