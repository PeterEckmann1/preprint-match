# preprint-match

Matches BioRxiv preprints with their corresponding PubMed paper.

<h2> Overview </h2>
Preprints from BioRxiv are matched with PubMed papers based on similarity between the abstract, title, and authors. This can be used to determine if a preprint ever led to a publication, and if so, what exactly that publication is. A list of BioRxiv DOIs are entered, and a list of PubMed PMIDs are returned for all preprints where a match has been found. This algorithm is correct for >99% of preprints.

<h2> Setup </h2>
<h3> Dependencies </h3>
Python 3.8 is required, as well as the latest versions of:

- [`scipy 1.3.3`](scipy 1.3.3)

- `numpy`

- `nltk`

- `psutil`

- `sklearn`

<h3> Installing the database </h3>
A copy of PubMed is required for the program to run. Follow the following steps to download and parse the database for usage.

1. Run `pubmed_master.py` in the `database` folder (i.e. `python pubmed_master.py`)

2. Run `create_matrix_master.py` in the `database` folder (i.e. `python create_matrix_master.py`)

<h2> Usage </h2>
Create a file of DOIs, each on a separate line. For example,

```
10.1101/003673
10.1101/2019.12.27.881656
10.1101/272831
```
Save the file in the the project folder (`preprint-match`), and call `find_papers.py` with a command line argument specifying the name of the DOI file. If we call the previous file `dois.txt`, we would call `python find_papers.py dois.txt`.

When finished, a file for each DOI will be found in the `results` folder of `preprint-match`. Each file contains the PMID of the matching paper (or `-1` if no match was found).

<h3> Testing </h3>
To test the algorithm, follow the following steps.

1. Run `build_test.py` in the `tests` folder (i.e. `python build_test.py`)

2. Run `find_papers.py` with the flag `-t` or `--test` (i.e. `python find_papers.py -t`)
