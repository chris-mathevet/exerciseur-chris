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

