import psycopg2
import psycopg2.extras
import os
from secrets import token_urlsafe
import fasttext
import numpy as np
import string
from tqdm import tqdm

#todo add tqdm for applying word vectors and others
class Database:
    def __init__(self, dbname, password, user='postgres', port=5432):
        self.conn = psycopg2.connect(dbname=dbname, user=user, password=password, port=port)
        self.cur = self.conn.cursor()
        self._create_tables()
        self.paper_queue = []
        self.author_queue = []
        self.doi_hashmap = {}
        self.vectors = None

    def _create_tables(self):
        self.cur.execute('create table if not exists papers (id integer primary key generated always as identity, doi text, source text, title text, abstract text, published date, title_vector real[], abstract_vector real[]); create index if not exists doi_index on papers(doi)')
        self.cur.execute('create table if not exists authors (paper integer, author text); create index if not exists paper_index on authors(paper)')
        self.conn.commit()

    def insert(self, doi, title, abstract, authors, date=None, source=None):
        if doi in self.doi_hashmap:
            self.paper_queue[self.doi_hashmap[doi]] = None
        self.doi_hashmap[doi] = len(self.paper_queue)
        self.paper_queue.append((doi, source, title, abstract, date))
        self.author_queue.append(authors)
        if len(self.paper_queue) > 9999:
            self.commit()

    def commit(self):
        if len(self.paper_queue) == 0:
            return
        self.paper_queue = [row for row in self.paper_queue if row]
        self.cur.execute('delete from papers where doi in %s returning id', (tuple(row[0] for row in self.paper_queue),))
        delete_ids = self.cur.fetchall()
        if len(delete_ids) != 0:
            self.cur.execute('delete from authors where paper in %s', (tuple(row[0] for row in delete_ids),))
        self.cur.execute('insert into papers (doi, source, title, abstract, published) values ' + ', '.join(self.cur.mogrify('(%s, %s, %s, %s, %s)', row).decode('utf-8') for row in self.paper_queue) + 'returning id')
        author_rows = []
        for i, id in enumerate([row[0] for row in self.cur.fetchall()]):
            for author in self.author_queue[i]:
                author_rows.append((id, author))
        psycopg2.extras.execute_values(self.cur, 'insert into authors values %s', author_rows, page_size=1000)
        del author_rows
        self.paper_queue = []
        self.author_queue = []
        self.doi_hashmap = {}
        self.conn.commit()

    def delete(self):
        self.cur.execute('drop table papers; drop table authors')
        self.conn.commit()
        self._create_tables()
        self.paper_queue = []
        self.author_queue = []

    def _generate_word_vectors(self, folder, percent, field):
        with self.conn.cursor(token_urlsafe(20)) as cur:
            cur.execute(f"select {field} from papers tablesample system ({percent}) where {field} != ''")
            f_name = token_urlsafe(20) + '.txt'
            with open(f_name, 'w', encoding='utf-8') as f:
                for row in cur:
                    f.write(row[0].lower() + '\n')
            model = fasttext.train_unsupervised(f_name, dim=300)
            os.remove(f_name)
            model.save_model(f'{folder}/{field}_vectors.bin')

    def generate_word_vectors(self, folder, abstract_percent, title_percent):
        self._generate_word_vectors(folder, abstract_percent, 'abstract')
        self._generate_word_vectors(folder, title_percent, 'title')

    def _apply_word_vectors(self, field, step):
        rows = []
        while len(rows) == 0 or len(rows) == step:
            rows = []
            with self.conn.cursor(token_urlsafe(20)) as cur:
                cur.execute(f"select id, {field} from papers where {field} != '' and {field}_vector is null limit {step}")
                for row in cur:
                    rows.append(row)
            if len(rows) == 0:
                break
            self.cur.execute(f"update papers set {field}_vector = c.{field}_vector from (values {', '.join([self.cur.mogrify('(%s::integer, %s)', (row[0], self.vectors.text_to_vector(field, row[1]).tolist())).decode('utf-8') for row in rows])}) as c(id, {field}_vector) where c.id = papers.id")
            self.conn.commit()

    def apply_word_vectors(self, folder, step=10000):
        self.vectors = Vectors(folder)
        self._apply_word_vectors('abstract', step)
        self._apply_word_vectors('title', step)

    def _generate_matrices(self, folder, field):
        self.cur.execute(f'select count(*) from papers where {field}_vector is not null')
        size = self.cur.fetchone()[0]
        np.memmap(f'{folder}/{field}_matrix.dat', mode='w+', dtype=np.float32, shape=(size, 300))
        np.memmap(f'{folder}/{field}_ids.dat', mode='w+', dtype=np.int32, shape=(size,))
        with self.conn.cursor(token_urlsafe(20)) as cur:
            cur.execute(f'select id, {field}_vector from papers where {field}_vector is not null')
            for i, row in enumerate(cur):
                if i % 100000 == 0:
                    matrix = np.memmap(f'{folder}/{field}_matrix.dat', dtype=np.float32, shape=(size, 300))
                    ids = np.memmap(f'{folder}/{field}_ids.dat', dtype=np.int32, shape=(size,))
                    print(i)
                matrix[i] = np.array(row[1], dtype=np.float32)
                ids[i] = row[0]

    def generate_matrices(self, folder):
        self._generate_matrices(folder, 'abstract')
        exit()
        self._generate_matrices(folder, 'title')

    def get_metadata_from_id(self, id):
        self.cur.execute('select * from papers where id = %s', (id,))
        row = self.cur.fetchone()
        return {'doi': row[1], 'source': row[2], 'title': row[3], 'abstract': row[4], 'date': row[5]}


class Vectors:
    def __init__(self, folder):
        self.abstract_model = fasttext.load_model(f'{folder}/abstract_vectors.bin')
        self.title_model = fasttext.load_model(f'{folder}/title_vectors.bin')

    def abstract_text_to_vector(self, text):
        return self.abstract_model.get_sentence_vector(text.lower().replace('\n', ' ').replace('  ', ' '))

    def title_text_to_vector(self, text): #todo this is hacky, should rerun everything with periods removed
        if not (text.endswith('?') or text.endswith('.')):
            text = text.strip() + '.'
        return self.title_model.get_sentence_vector(text.lower())

    def text_to_vector(self, field, text):
        if field == 'abstract':
            return self.abstract_text_to_vector(text)
        elif field == 'title':
            return self.title_text_to_vector(text)