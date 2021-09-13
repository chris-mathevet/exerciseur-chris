from outils_exercices.voile import ErreurVoilée

def solution(fun):
    fun.solution = True
    return fun


class ErreurEntréeVisible(ErreurVoilée):
    def __init__(self, nom_fonction, entree, etu, ens):
        self.entree = entree
        self.nom_fonction = nom_fonction
        self.etu = etu
        self.ens = ens

    def messages(self):
        arguments = ", ".join([repr(a) for a in self.entree])
        appel = "{}({})".format(self.nom_fonction, arguments)
        return "L'appel {}, renvoie {} alors que la valeur attendue était {}".format(appel, self.etu, self.ens)

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
    def __init__(self, nom_fonction, entree, ens, e_type, e_value, e_traceback):
        self.entree = entree
        self.ens = ens
        self.nom_fonction = nom_fonction
        super().__init__(e_type, e_value, e_traceback)

    def messages(self):
        arguments = ", ".join([repr(a) for a in self.entree])
        appel = "{}({})".format(self.nom_fonction, arguments)
        en_tête = "L'appel {}, lève une l'exception imprévue {!r}".format(self.entree, self.e_interne)
        return liste_messages(en_tête, super().messages())
    
class ExceptionEntréeInvisible(ErreurVoilée):
    def messages(self):
        en_tête = ["Sur une entrée invisible, vous levez une l'exception imprévue {!r}".format(self.e_interne)]
        return liste_messages(en_tête, super().messages())

class FonctionÉtuManquante(Exception):
    def __init__(self, nom_fonction):
        self.nom_f = nom_fonction
