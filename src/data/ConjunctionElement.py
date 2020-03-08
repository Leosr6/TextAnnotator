class ConjunctionElement:

    f_to = None
    f_from = None
    f_type = None

    def __init__(self, el_from, el_to, conj):
        self.f_from = el_from
        self.f_to = el_to
        self.f_type = conj
