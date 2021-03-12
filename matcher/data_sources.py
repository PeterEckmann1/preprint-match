import lxml.etree as ET
import datetime
from multiprocessing import Pool
import psycopg2
from secrets import token_urlsafe


MONTHS = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']


#todo don't remove reviews and stuff because they sometimes show up
class PubMed:
    def __init__(self, files):
        self.files = files
        self.processed_files = []

    def _disambiguate_date(self, text):
        try:
            if len(text.split()) < 2:
                if text.strip().isdigit():
                    return int(text), 1, 1
                else:
                    return None, None, None
            year, month = int(text.split()[0]), text.split()[1].lower()
            if len(text.split()) > 2 and text.split()[-1].isdigit():
                day = int(text.split()[-1])
            else:
                day = 1
            if month.isdigit():
                month = int(month)
            else:
                months = MONTHS
                new_months = []
                for i, char in enumerate(month):
                    for j, month in enumerate(months):
                        if month[i] == char:
                            new_months.append(month)
                    months = new_months
                    new_months = []
                    if len(months) == 1:
                        month = MONTHS.index(months[0]) + 1
                        break
                if not str(month).isdigit():
                    month = 1
            return year, month, day
        except:
            return None, None, None

    def _parse(self, file):
        root = ET.parse(file).getroot()
        papers = []
        for article in root.iter('PubmedArticle'):
            paper = {'pmid': 0, 'doi': '', 'abstract': '', 'authors': [], 'date': None, 'title': '', 'types': [], 'affiliations': []}
            skip = False
            for type in article.iter('PublicationType'):
                paper['types'].append(type.text)
            if 'Comment' in paper['types'] or 'Published Erratum' in paper['types'] or 'Review' in paper['types'] or 'Preprint' in paper['types']:
                continue
            for affiliation in article.iter('Affiliation'):
                paper['affiliations'].append(affiliation.text)
            for data_field in article:
                if data_field.tag == 'MedlineCitation':
                    for field in data_field:
                        if field.tag == 'PMID':
                            paper['pmid'] = int(field.text)
                        if field.tag == 'Article':
                            for subfield in field:
                                for date in subfield.iter('PubDate'):
                                    year, month, day = self._disambiguate_date(' '.join([val.text for val in date]))
                                    try:
                                        paper['date'] = datetime.date(year, month, day)
                                    except:
                                        pass
                                if subfield.tag == 'Abstract':
                                    for abstract_text in subfield.iter('AbstractText'):
                                        paper['abstract'] += ET.tostring(abstract_text, encoding='utf-8',
                                                                         method='text').decode('utf-8').strip().replace('\n', ' ') + ' '
                                    paper['abstract'] = paper['abstract'].strip()
                                if subfield.tag == 'AuthorList':
                                    for last_name in subfield.iter('LastName'):
                                        paper['authors'].append(last_name.text)
                                    for i, fore_name in enumerate(subfield.iter('ForeName')):
                                        try:
                                            paper['authors'][i] = fore_name.text + ' ' + paper['authors'][i]
                                        except TypeError:
                                            pass
                                if subfield.tag == 'ArticleTitle':
                                    paper['title'] = ET.tostring(subfield, encoding='utf-8', method='text').decode('utf-8').strip().replace('\n', ' ')
                                if subfield.tag == 'Language':
                                    if subfield.text != 'eng':
                                        skip = True
                                        break
                                if skip:
                                    break
                    if skip:
                        break       
                if data_field.tag == 'PubmedData':
                    for id in data_field.iter('ArticleId'):
                        if id.attrib['IdType'] == 'doi':
                            paper['doi'] = id.text
            if skip or paper['doi'] == '':
                continue
            papers.append(paper)
        return papers

    def stream_papers(self):
        with Pool(1) as pool:
            for i, paper_set in enumerate(pool.imap(self._parse, self.files)):
                for paper in paper_set:
                    yield paper
                self.processed_files.append(self.files[i])


class bioRxiv:
    def __init__(self, db):
        self.cur = db.conn.cursor(token_urlsafe(20))
        self.cur.execute('select doi, title, abstract from prod.articles')

    def stream_papers(self):
        for row in self.cur:
            if row[2]:
                yield {'doi': row[0], 'title': row[1], 'abstract': row[2].split('### Competing Interest Statement')[0].replace('\n', ' ').replace('  ', ' '), 'authors': []}