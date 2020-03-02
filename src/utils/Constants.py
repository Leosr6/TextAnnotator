"""
    All the explanation of the labels are established as per the
    Stanford Dependencies documentation on:
    https://nlp.stanford.edu/software/dependencies_manual.pdf

    The labels were all mapped to the Universal Dependencies format
    as per table 2 of the documentation on:
    https://nlp.stanford.edu/pubs/USD_LREC14_paper_camera_ready.pdf
"""

# A nominal subject is a noun phrase which is the syntactic subject of a clause
NSUBJ = "nsubj"
# A clausal subject is a clausal syntactic subject of a clause, i.e., the subject is itself a clause
CSUBJ = "csubj"
# The direct object of a VP is the noun phrase which is the (accusative) object of the verb
DOBJ = "dobj"
# A passive nominal subject is a noun phrase which is the syntactic subject of a passive clause
NSUBJPASS = "nsubjpass"
# A clausal passive subject is a clausal syntactic subject of a passive clause
CSUBJPASS = "csubjpass"
# An agent is the complement of a passive verb which is introduced by the preposition "by"
AGENT = "nmod:agent"
# A relative clause modifier of an NP is a relative clause modifying the NP
RELCL = "relcl"
# A copula is the relation between the complement of a copular verb and the copular verb.
COP = "cop"
# A conjunct is the relation between two elements connected by a coordinating conjunction, such as "and", "or", etc.
CONJ = "conj"


"""
    TO-DO: write description
"""

ROOT = "ROOT"
VP = "VP"
S = "S"
SBAR = "SBAR"
PRN = "PRN"
