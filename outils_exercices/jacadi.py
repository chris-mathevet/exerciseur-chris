from outils_exercices.voile import ErreurVoilée

def solution(fun):
    fun.solution = True
    return fun


class ErreurEntréeVisible(ErreurVoilée):
    def __init__(self, entree, etu, ens):
        self.entree = entree
        self.etu = etu
        self.ens = ens

    def messages(self):
        return "Sur l'entrée {}, vous renvoyez {} alors que la valeur attendue était {}".format(self.entree, self.etu, self.ens)

class ErreurEntréeInvisible(ErreurVoilée):
    def __init__(self):
        pass

    def messages(self):
        return "Sur une entrée invisible, vous ne retournez pas la bonne valeur."

def liste_messages(en_tête, messages):
    res = [en_tête]
    res += ["<ul>\n"]
    res += ["<li>" + m + "</li>\n" for m in messages]
    res += ["</ul>\n"]
    return res

class ExceptionEntréeVisible(ErreurVoilée):
    def __init__(self, entree, ens, e_type, e_value, e_traceback):
        self.entree = entree
        self.ens = ens
        super().__init__(e_type, e_value, e_traceback)

    def messages(self):
        en_tête = "Sur l'entrée {}, vous levez une l'exception imprévue {!r}".format(self.entree, self.e_interne)
        return liste_messages(en_tête, super().messages())
    
class ExceptionEntréeInvisible(ErreurVoilée):
    def messages(self):
        en_tête = ["Sur une entrée invisible, vous levez une l'exception imprévue {!r}".format(self.e_interne)]
        return liste_messages(en_tête, super().messages())

class FonctionÉtuManquante(Exception):
    def __init__(self, nom_fonction):
        self.nom_f = nom_fonction
