# preprint-match

Matches bioRxiv preprints with their corresponding PubMed paper. 

## Installation

First, install [docker](https://docs.docker.com/get-docker/) for hosting the PostgreSQL database. Then, the following python libraries must be installed via pip:
```
numpy
numba
tqdm
lxml
psycopg2-binary
fasttext
requests
```

preprint-match was tested with python 3.7, but it may work with other python3 versions.


## Usage

First, run `docker compose up -d` in the home directory of this repository to start a postgres instance in docker. Then, a local copy of PubMed must be created. Call the script `python load_pubmed.py` to download PubMed files one-by-one through the FTP service, and then preprocess the results and save them in the database. These steps must only be performed once.

To match a preprint and paper, use the API provided in `match_from_doi.py`. It contains a function, `match_from_doi`, that takes a list of preprint DOIs and returns a list of matching paper DOIs. Example usage:
```
from match_from_doi import match_from_doi

print(match_from_doi(['preprintdoi1', 'preprintdoi2']))
```


## Contact

Contact petereckmann(at)gmail(dot)com for help using the tool or for access to the data.

