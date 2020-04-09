def résultat(code_etu):
    return {
        "_valide": True,
        "_messages": ["T'es un·e champion·ne", "C'est exactement '" + str(code_etu) + "' que j'attendais"],
    }

class ToujoursContent:
    def évalue(self, code_étu):
        return résultat(code_étu)
