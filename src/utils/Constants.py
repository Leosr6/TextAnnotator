"""
    All the explanation of the labels are established as per the
    Stanford Dependencies documentation on:
    https://nlp.stanford.edu/software/dependencies_manual.pdf
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
AGENT = "agent"
# A relative clause modifier of an NP is a relative clause modifying the NP
RCMOD = "rcmod"
# A copula is the relation between the complement of a copular verb and the copular verb.
COP = "cop"
# A conjunct is the relation between two elements connected by a coordinating conjunction, such as "and", "or", etc.
CONJ = "conj"
# A prepositional modifier of a verb, adjective, or noun is any prepositional phrase that serves to modify the meaning of the verb, adjective, noun, or even another prepositon.
PREP = "prep"
# An open clausal complement (xcomp) of a verb or an adjective is a predicative or clausal complement without its own subject.
XCOMP = "xcomp"
# A dependency is labeled as dep when the system is unable to determine a more precise dependency relation between two words.
DEP = "dep"
# A noun compound modifier of an NP is any noun that serves to modify the head noun.
NN = "nn"
AUX = "aux"
AUXPASS = "auxpass"
ADVMOD = "advmod"
ACOMP = "acomp"
NEG = "neg"
PRT = "prt"
PREPC = "prepc"
ADJP = "adjp"
POSS = "poss"
DET = "det"
INFMOD = "infmod"
PARTMOD = "partmod"
NUM = "num"
AMOD = "amod"
NNAFTER = "nnafter"
CCOMP = "ccomp"
COMPLM = "complm"
PUNCT = "punct"
MARK = "mark"
DIRECT = "direct"


"""
    Penn Treebank II Tags
    Extracted from:
    https://web.archive.org/web/20130517134339/http://bulba.sdsu.edu/jeanette/thesis/PennTags.html
"""

ROOT = "ROOT"
NP = "NP"
VP = "VP"
S = "S"
SBAR = "SBAR"
SINV = "SINV"
PRN = "PRN"
PP = "PP"
ADVP = "ADVP"
CD = "CD"
IOBJ = "IOBJ"
VBN = "VBN"
VB = "VB"
WHNP = "WHNP"

"""
    TODO: write description
    Recurrent words
"""

IN = "in"
IT = "it"
IF = "if"
OF = "of"
DO = "do"
BE = "be"
INTO = "into"
UNDER = "under"
ABOUT = "about"
TERMINATE = "terminate"
THAT = "that"
OR = "or"
AND = "and"
ANDOR = "and/or"
XOR = "xor"
BUT = "but"
TO = "to"
NO = "no"
FOR = "for"
MIXED = "mixed"
WHILE = "while"
WHEREAS = "whereas"
OTHERWISE = "otherwise"
EXCEPT = "except"
IFCOMPLM = "if-complm"
THEN = "then"
ALSO = "also"
SOON = "soon"

"""
    TODO: write description
"""

ANIMATE = "ANIMATE"
INANIMATE = "INANIMATE"
BOTH = "BOTH"

"""
    Flow type
    TODO: write description
"""

JUMP = "JUMP"
MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
CHOICE = "CHOICE"
CONCURRENCY = "CONCURRENCY"
EXCEPTION = "EXCEPTION"
SEQUENCE = "SEQUENCE"

"""
    Conjunction status
    TODO: write description
"""

NOT_CONTAINED = "NOT_CONTAINED"
ACTION = "ACTION"
ACTOR_SUBJECT = "ACTOR_SUBJECT"
ACTOR_OBJECT = "ACTOR_OBJECT"
RESOURCE = "RESOURCE"

"""
    Link types
    TODO: write description
"""

FORWARD = "FORWARD"
JUMP = "JUMP"
LOOP = "LOOP"
NONE = "NONE"

"""
    Phrase types
    TODO: write description
"""

CORE = "CORE"
PERIPHERAL = "PERIPHERAL"
EXTRA_THEMATIC = "EXTRA_THEMATIC"
GENITIVE = "GENITIVE"
UNKNOWN = "UNKNOWN"

"""
    Flow direction
    TODO: write description
"""

SPLIT = "SPLIT"
JOIN = "JOIN"

"""
    TODO: write description
"""

SUBJECT_ROLE_SCORE = 10
OBJECT_ROLE_SCORE = 10
ROLE_MATCH_SCORE = 20
SENTENCE_DISTANCE_PENALTY = 15

"""
    TODO: write description
"""

f_realActorPPIndicators = ["in", "of"]
f_sequenceIndicators = ["then", "after", "afterward", "afterwards", "subsequently", "based on this", "thus"]
f_relativeResolutionTags = ["DT", "PRP", "WP"]
f_relativeResolutionWords = ["someone"]
f_conditionIndicators = ["if", "whether", "in case of", "in the case of", "in case", "for the case", "whereas", "otherwise", "optionally"]
f_exampleIndicators = ["for instance", "for example", "e.g.", "i.e."]
f_parallelIndicators = ["while", "meanwhile", "in parallel", "concurrently", "meantime", "in the meantime"]
f_frequencyWords = ["usually", "normally", "often", "frequently", "sometimes", "occasionally", "rarely", "seldom"]
f_wantedDeterminers = ["a", "an", "no", "the"]
finishedIndicators = ["when", "whenever", "once", "as soon as", "after"]
falseTimePeriod = ["second"]

"""
    TODO: write description
    Processing
"""

f_beForms = ["be", "am", "are", "is", "was", "were", "been"]
f_personPronouns = ["I", "you", "he", "she", "we", "you", "they", "me", "him", "her", "us", "them"]
f_thirdPersonPronouns = ["he", "she", "it", "they", "him", "her", "them"]
f_inanimatePronouns = ["it", "they", "them", "which"]
f_determiner = ["the", "this", "that", "these", "those"]
f_actionResolutionDeterminer = ["this", "that"]
f_relativeClausePronouns = ["who", "whose", "which", "that"]
f_weakVerbToThirdPerson = {"be": "is", "have": "has", "do": "does"}

"""
    TODO: write description
    WordNet Wrapper
"""

f_acceptedForForwardLink = ["finally", "in any case"]
f_personCorrectorList = ["resource provisioning", "customer service", "support", "support office", "support officer", "client service back office",
                         "master", "masters", "assembler ag", "acme ag", "acme financial accounting", "secretarial office", "office", "registry",
                         "head", "storehouse", "atm", "crs", "company", "garage", "kitchen", "department", "ec", "sp", "mpo", "mpoo", "mpon", "msp"
                         "mspo", "mspn", "go", "pu", "ip", "inq", "sp\\/pu\\/go", "fault detector"]
f_realActorDeterminers = ["person", "social group", "software system"]
f_metaActorsDeterminers = ["step", "process", "case", "state"]
f_weakVerbs = ["be", "have", "do", "achieve", "start", "exist", "base"]
f_acceptedAMODforLoops = ["next", "back", "again"]

"""
    TODO: write description
    Event types
"""

START_EVENT = "StartEvent"
INTERMEDIATE_EVENT = "IntermediateEvent"
END_EVENT = "EndEvent"
COMPENSATION_EVENT = "Compensation"
CONDITIONAL_EVENT = "Conditional"
ERROR_EVENT = "Error"
ESCALATION_EVENT = "Escalation"
MESSAGE_EVENT = "Message"
MULTIPLE_EVENT = "Multiple"
PARALLEL_MULTIPLE_EVENT = "ParallelMultiple"
SIGNAL_EVENT = "Signal"
TIMER_EVENT = "Timer"
CANCEL_EVENT = "Cancel"
TERMINATE_EVENT = "Terminate"
LINK_EVENT = "Link"
THROWING_EVENT = "Throw"
CATCHING_EVENT = "Catch"

"""
    TODO: write description
    Gateway types
"""

PARALLEL_GATEWAY = "ParallelGateway"
INCLUSIVE_GATEWAY = "InclusiveGateway"
EXCLUSIVE_GATEWAY = "ExclusiveGateway"
EVENT_BASED_GATEWAY = "EventBasedGateway"

"""
    TODO: write description
    Process Model Builder
"""

MAX_NAME_DEPTH = 3
ADD_UNKNOWN_PHRASETYPES = True

"""
    TODO: write description
"""

SPEC_SPLIT = ":"
DUMMY_NODE = "Dummy"

"""
    TODO: write description
    Verb Types
"""

END_VERB = "end"
START_VERB = "start"
SEND_VERB = "send"
RECEIVE_VERB = "receive"

"""
    TODO: write description
"""

TIME_PERIOD = "time period"
GROUP_ACTION = "group action"
POS_VERB = "v"
POS_NOUN = "n"
POS_ADJECTIVE = "a"
POS_ADVERB = "r"
