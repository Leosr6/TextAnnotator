class Action:

    f_baseForm = None

    f_actorFrom = None
    f_object = None

    f_xcomp = None


    f_prt = None
    f_cop = None
    f_copIndex = None
    f_aux = None

    f_mod = None
    f_modPos = -1

    f_marker = None
    f_markerFromPP = False
    f_preAdvMod = None
    f_preAdvModPos = -1
    f_prepc = None
    f_negated = False

    f_link = None
    f_linkType = None
    f_transient = False

class Actor:

    f_unreal = False
    f_metaActor = False
    f_passive = False
    f_name = ""

class Resource:

    f_wordIndex = -1
    f_name = ""
    f_origin = None  # Stanford Sentence
