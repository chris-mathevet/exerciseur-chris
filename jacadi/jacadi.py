def solution(fun):
    fun.solution = True
    return fun


class ErreurEntréeVisible(Exception):
    def __init__(self, entree, etu, ens):
        self.entree = entree
        self.etu = etu
        self.ens = ens

class ErreurEntréeInvisible(Exception):
    pass

class ExceptionEntréeInvisible(Exception):
    def __init__(self, ex_interne):
        self.ex_interne = ex_interne

class ExceptionEntréeVisible(Exception):
    def __init__(self, entree, ex, ens):
        self.entree = entree
        self.etu = etu
        self.ens = ens
        self.ex_interne = ex
