from flask import Flask, render_template, redirect, request, flash
import psycopg2
import re


app = Flask(__name__)
app.secret_key = '0NOXd777Cpk9bxw56f3ZoqCvwMA'
conn = psycopg2.connect(dbname='postgres', user='postgres', password='testpass', port=5434)
cur = conn.cursor()


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def get_match():
    doi = re.findall('10\.\d{4,9}/[-._;()/:A-Z0-9]+', request.form['doi'])
    if len(doi) == 0:
        return render_template('index.html', message='No valid DOI or link was given.')
    else:
        doi = doi[0]
        if doi.startswith('10.1101/'):
            cur.execute('select papers.doi from matches inner join prod.articles on articles.id = matches.article left join papers on papers.id = matches.paper where articles.doi = %s', (doi,))
            paper_doi = cur.fetchone()
            if paper_doi:
                if paper_doi[0]:
                    return redirect(f'https://www.doi.org/{paper_doi[0]}')
                else:
                    return render_template('index.html', message=f'No matches were found for {doi}.')
        else:
            cur.execute('select articles.url from matches inner join prod.articles on articles.id = matches.article left join papers on papers.id = matches.paper where papers.doi = %s', (doi,))
            link = cur.fetchone()
            if link:
                return redirect(link[0])
    return render_template('index.html', message='A DOI was found, but it did not match any papers in PubMed or any bioRxiv preprints.')


if __name__ == '__main__':
    app.run(debug=True)