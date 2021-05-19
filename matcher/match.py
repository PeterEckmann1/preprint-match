import numpy as np
from numba import jit, prange, set_num_threads, config
from math import sqrt
from tqdm import tqdm
import pickle


class Classifier:
    def __init__(self, base_classifier, max_abstract_for_title_cutoff, title_cutoff, max_title_for_abstract_cutoff, abstract_cutoff):
        self.base_classifier = base_classifier
        self.max_abstract_for_title_cutoff = max_abstract_for_title_cutoff
        self.title_cutoff = title_cutoff
        self.max_title_for_abstract_cutoff = max_title_for_abstract_cutoff
        self.abstract_cutoff = abstract_cutoff

    def predict(self, abstract_similarity, title_similarity):
        if abstract_similarity > self.abstract_cutoff:
            return True
        if title_similarity > self.title_cutoff:
            return True
        if abstract_similarity < self.abstract_cutoff and title_similarity < self.max_title_for_abstract_cutoff:
            return False
        if title_similarity < self.title_cutoff and abstract_similarity < self.max_abstract_for_title_cutoff:
            return False
        return self.base_classifier.predict([(abstract_similarity, title_similarity)])[0]


class Matcher:
    def __init__(self, folder):
        self.folder = folder
        self.abstract_ids, self.abstract_row_count = self._load(folder, 'abstract')
        self.title_ids, self.title_row_count = self._load(folder, 'title')
        self.classifier = pickle.load(open(f'{folder}/classifier.pickle', 'rb'))

    def _load(self, folder, field):
        row_count = np.memmap(f'{folder}/{field}_matrix.dat', mode='r', dtype=np.float32).size // 300
        ids = np.memmap(f'{folder}/{field}_ids.dat', dtype=np.int32)
        return ids, row_count

    def _refresh_memmaps(self, is_abstract):
        if is_abstract:
            return np.memmap(f'{self.folder}/abstract_matrix.dat', mode='r', dtype=np.float32, shape=(self.abstract_row_count, 300))
        else:
            return np.memmap(f'{self.folder}/title_matrix.dat', mode='r', dtype=np.float32, shape=(self.title_row_count, 300))

    @staticmethod
    @jit(nopython=True, parallel=True)
    def _match(a, b, matches, offset):
        a_norms = np.zeros((a.shape[0],))
        for i in prange(a.shape[0]):
            square_sum = 0
            for j in range(300):
                square_sum += a[i][j] ** 2
            a_norms[i] = sqrt(square_sum)
        b_norms = np.zeros((b.shape[0],))
        for i in prange(b.shape[0]):
            square_sum = 0
            for j in range(300):
                square_sum += b[i][j] ** 2
            b_norms[i] = sqrt(square_sum)
        for i in prange(a.shape[0]):
            for j in range(b.shape[0]):
                dot = 0
                for k in range(300):
                    dot += a[i][k] * b[j][k]
                similarity = dot / (a_norms[i] * b_norms[j])
                for k in range(matches.shape[1]):
                    if similarity > matches[j][k][0] and (k + 1 == matches.shape[1] or similarity < matches[j][k + 1][0]): #todo problem is same id is showing up for all parts of array
                        for m in range(k):
                            matches[j][m] = matches[j][m + 1]
                        matches[j][k][0] = similarity
                        matches[j][k][1] = i + offset
                        break
        return matches

    def _match_field(self, a_vector_count, b_vectors, step, k, is_abstract):
        matches = np.zeros((b_vectors.shape[0], k, 2)) #todo should technically be two different dtypes, try to do title vectors with abstract model
        for i in tqdm(range(0, a_vector_count, step), desc=f"matching {'abstract' if is_abstract else 'title   '}   "):
            a_vectors = self._refresh_memmaps(is_abstract)
            matches = self._match(a_vectors[i: i + step], b_vectors, matches, i)
        return matches

    def _abstract_first_n(self, text, n):
        return ' '.join([word[:5] for word in text.split() if ('(' not in word and word.lower() not in {'a', 'an', 'the', 'background:', 'introduction:'})][:n])

    def _title_colon(self, text):
        if len(text.split()) == 0 or ':' not in text.split()[0]:
            return None
        return text.split()[0]

    def _get_author_similarity(self, paper_authors, preprint_authors, in_main_loop):
        if not in_main_loop:
            if len(paper_authors) < 2:
                return 1
            for term in ['group', 'consortium', 'investigators', 'team']:
                if term in [author.lower() for author in preprint_authors] and len(set(paper_authors).intersection(preprint_authors)) / len(set(paper_authors).union(preprint_authors)) > 0.1:
                    return 1
        try:
            first_authors_match = paper_authors[0] == preprint_authors[0]
        except:
            first_authors_match = False
        try:
            return len(set(paper_authors).intersection(preprint_authors)) / len(set(paper_authors).union(preprint_authors)) + (1 if first_authors_match and in_main_loop else 0)
        except ZeroDivisionError:
            print('zero division')
            return 0

    def match(self, dois, authors, abstracts, titles, abstract_vectors, title_vectors, cur, step, k, threads=config.NUMBA_NUM_THREADS, abstract_matches=None, title_matches=None):    #todo output dois instead of i
        #authors is a dict of dois to sets of author last names
        set_num_threads(threads)
        matches = []
        if abstract_matches is None:
            abstract_matches = self._match_field(self.abstract_row_count, abstract_vectors, step, k, True)
            abstract_matches[:,:,1] = self.abstract_ids[abstract_matches[:,:,1].astype(np.int32)]
            title_matches = self._match_field(self.title_row_count, title_vectors, step, k, False)
            title_matches[:,:,1] = self.title_ids[title_matches[:,:,1].astype(np.int32)]

        for i in tqdm(range(abstract_matches.shape[0]), desc='determining matches '):
            all_ids = list(set(abstract_matches[i,:,1]).union(title_matches[i,:,1]))
            best_guess = (i, None, None, None)
            abstract, title = abstracts[dois[i]], titles[dois[i]]
            preprint_first_n = self._abstract_first_n(abstract, 7)
            preprint_title_colon = self._title_colon(title)
            for id in all_ids:
                abstract_index = list(np.where(abstract_matches[i,:,1] == id)[0])
                title_index = list(np.where(title_matches[i,:,1] == id)[0])
                abstract_similarity = 0
                title_similarity = 0
                if abstract_index:
                    abstract_similarity = abstract_matches[i][abstract_index][0][0]
                if title_index:
                    title_similarity = title_matches[i][title_index][0][0]
                if self.classifier.predict(abstract_similarity, title_similarity):
                    if not best_guess[1] or (best_guess[1] and best_guess[3] < title_similarity):
                        best_guess = (i, int(id), abstract_similarity, title_similarity)
                elif not best_guess[1]:
                    cur.execute("select substring(name from '\w+$') from authors where paper = %s", (int(id),))
                    paper_authors = [row[0] for row in cur]
                    author_similarity = self._get_author_similarity(paper_authors, authors[dois[i]], True)
                    cur.execute("select substring(name from '^\w+') from authors where paper = %s", (int(id),))
                    paper_author_first_names = [row[0] for row in cur]
                    if self._get_author_similarity(paper_author_first_names, authors[dois[i]], True) > author_similarity:
                        author_similarity = self._get_author_similarity(paper_author_first_names, authors[dois[i]], True)
                    cur.execute("select abstract, title from papers where id = %s", (int(id),))
                    abstract, title = cur.fetchone()
                    paper_first_n = self._abstract_first_n(abstract, 7)
                    paper_title_colon = self._title_colon(title)
                    if preprint_first_n.lower() == paper_first_n.lower() or (preprint_title_colon and paper_title_colon and preprint_title_colon == paper_title_colon):
                        best_guess = (i, int(id), abstract_similarity, title_similarity)
                        continue
                    if self.classifier.predict(abstract_similarity + author_similarity * 0.01, title_similarity + author_similarity * 0.03):
                        best_guess = (i, int(id), abstract_similarity, title_similarity)
            if best_guess[1] and not (best_guess[2] > 0.999 or best_guess[3] > 0.999):
                cur.execute("select substring(name from '\w+$') from authors where paper = %s", (best_guess[1],))
                paper_authors = [row[0] for row in cur]
                author_similarity = self._get_author_similarity(paper_authors, authors[dois[i]], False)
                cur.execute("select substring(name from '^\w+') from authors where paper = %s", (best_guess[1],))
                paper_author_first_names = [row[0] for row in cur]
                if self._get_author_similarity(paper_author_first_names, authors[dois[i]], False) > author_similarity:
                    author_similarity = self._get_author_similarity(paper_author_first_names, authors[dois[i]], False)
                    paper_authors = paper_author_first_names
                if author_similarity < 0.33:
                    best_guess = (i, None, None, None)
                elif len(paper_authors) > 1 and  authors[dois[i]][0] not in paper_authors[:5] and authors[dois[i]][1] not in paper_authors[:5]:
                    best_guess = (i, None, None, None)
            if not best_guess[1] and len(authors[dois[i]]) > 3:
                author_string = ''.join(authors[dois[i]])
                cur.execute('select paper from author_strings where author_string = %s', (author_string,))
                rows = cur.fetchall()
                if len(rows) == 1:
                    best_guess = (i, rows[0][0], 0, 0)
                elif len(authors[dois[i]]) > 10:
                    cur.execute('select paper from author_strings where left(author_string, 10) = left(%s, 10)', (author_string,))
                    for row in cur:
                        paper = row[0]
                        cur.execute("select substring(name from '\w+$') from authors where paper = %s", (paper,))
                        paper_authors = [row[0] for row in cur if row[0].lower() not in ['group', 'consortium', 'investigators', 'team']]
                        authors[dois[i]] = [author for author in authors[dois[i]] if author.lower() not in ['group', 'consortium', 'investigators', 'team']]
                        if paper_authors[:3] == authors[dois[i]][:3] and paper_authors[-3:] == authors[dois[i]][-3:]:
                            best_guess = (i, paper, 0, 0)
            matches.append(best_guess)
        return matches


if __name__ == '__main__':
    import pickle
    import psycopg2
    matcher = Matcher('../data')
    dois, authors, abstracts, titles, abstract_matches, title_matches, step, k = pickle.loads(open('../matcher/temp.pickle', 'rb').read())
    conn = psycopg2.connect(dbname='postgres', user='postgres', password='testpass', port=5434)
    cur = conn.cursor()
    for i, paper, abstract_similarity, title_similarity in matcher.match(dois, authors, abstracts, titles, None, None, cur, step, k, abstract_matches=abstract_matches, title_matches=title_matches):
        if paper:
            cur.execute('select doi from papers where id = %s', (paper,))
            paper = cur.fetchone()[0]
        print(dois[i], paper)