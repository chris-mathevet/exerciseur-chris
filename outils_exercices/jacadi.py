from outils_exercices.voile import ErreurVoilée, VoilePudique
import sys

this = sys.modules[__name__]
this.fonctions_ens = None
this.nom_fonction_ens = None

def solution(fun):
    import inspect

    fun.solution = True
    this.fonction_ens = fun
    this.nom_fonction_ens = fun.__name__
    module_ens = inspect.getmodule(this.fonction_ens)
    fun.entrees_visibles = module_ens.entrees_visibles
    fun.entrees_invisibles = module_ens.entrees_invisibles

    def teste_fonction_etu(f_etu):

        for e in fun.entrees_visibles:
            s_ens = this.fonction_ens(*e)
            def décore_exc(e_ty, e_val, e_tb):
                return ExceptionEntréeVisible(fun.__name__, e, s_ens, e_ty, e_val, e_tb)
            with VoilePudique(décore_exc):
                s_etu = f_etu(*e)
            if s_etu != s_ens:
                raise ErreurEntréeVisible(fun.__name__, e, s_etu, s_ens)

    fun.test_fonction_etu = teste_fonction_etu

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

        return self.message

    def __str__(self):
        return self.messages()


class ErreurEntréeInvisible(ErreurVoilée):
    def __init__(self):
        pass

    def messages(self):
        return "Sur une entrée invisible, vous ne retournez pas la bonne valeur."

def liste_messages(en_tête, messages):
    res = en_tête
    res += "<ul>\n"
    res += "".join("<li>" + m + "</li>\n" for m in messages)
    res += "</ul>\n"
    return res

class ExceptionEntréeVisible(ErreurVoilée):
    def __init__(self, nom_fonction, entree, ens, e_type, e_value, e_traceback):
        self.entree = entree
        self.ens = ens
        self.nom_fonction = nom_fonction
        super().__init__(e_type, e_value, e_traceback)

    def en_tête(self):
        arguments = ", ".join([repr(a) for a in self.entree])
        appel =  "{}({})".format(self.nom_fonction, arguments)
        return "L'appel {}, lève une l'exception imprévue {!r}".format(appel, self.e_interne)

    def messages(self):
        return liste_messages(self.en_tête(), super().messages())

    def __str__(self):
        return self.en_tête()

class ExceptionEntréeInvisible(ErreurVoilée):
    def messages(self):
        en_tête = "Sur une entrée invisible, vous levez une l'exception imprévue {!r}".format(self.e_interne)
        return liste_messages(en_tête, super().messages())

class FonctionÉtuManquante(Exception):
    def __init__(self, nom_fonction):
        self.nom_f = nom_fonction
