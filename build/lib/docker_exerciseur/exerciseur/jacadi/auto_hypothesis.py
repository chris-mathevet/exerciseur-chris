import hypothesis

class PasAssezSpécifique(Exception):
    pass

class Ingérable(Exception):
    pass

def infère_stratégie_en_combinant(entrées):
    strat = None
    for e in entrées:
        try:
            strat = infère_stratégie(e)
        except PasAssezSpécifique:
            pass
    if strat:
        return strat
    else:
        raise PasAssezSpécifique

def infère_stratégie(entrée):
    t = type(entrée)
    if t == int:
        return "hypothesis.strategies.integers()"
    elif t == str:
        return "hypothesis.strategies.text(string.printable)"
    elif t == bool:
        return "hypothesis.strategies.booleans()"
    elif t == list:
        strat_élems = infère_stratégie_en_combinant(entrée)
        return "hypothesis.strategies.lists({})".format(strat_élems)
    elif t == tuple:
        strats_élems = tuple(infère_stratégie(e) for e in entrée)
        return "hypothesis.strategies.tuples({})".format(", ".join(strats_élems))
    elif t == dict:
        strat_clés = infère_stratégie_en_combinant(entrée.keys())
        strat_valeurs = infère_stratégie_en_combinant(entrée.values())
        return "hypothesis.strategies.dictionaries({}, {})".format(strat_clés, strat_valeurs)
    elif t == set:
        strat_elems = infère_stratégie_en_combinant(entrée)
        return "hypothesis.strategies.sets({})".format(strat_elems)
    else:
        raise Ingérable("Impossible d'inférer un testeur Hypothesis pour les valeurs de type {} comme {}".format(t, entrée))
    
