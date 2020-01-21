entrees_visibles = [([],),
                    ([-5,4,3],),
                    ([-12,4,3],)
]
entrees_invisibles = [
        ([14,23,10,8,7],),
        ([-4,1,-4,3,8],)
]

@solution
def pairesMajoritaires(liste):
    """
    permet de savoir si une liste d'entiers contient une majorité 
    de nombres paires ou non
    paramètre: liste une liste d'entiers
    resultat: 1 si les paires sont majoritaires, -1 si ce sont les impaires
              0 en cas d'égalité
    """
    # je choisis for elem in liste car je dois parcourir tous les éléments
    # d'une seule liste pour obtenir le résultat
    cpt=0
    for nb in liste: 
    #invariant: cpt contient la différence entre le nombre d'entiers paires et
    #           et le nombres d'entiers impaires déjà énumérés
        if nb%2==0:
            cpt+=1
        else:
            cpt-=1
    if cpt>0:
        res=1
    elif cpt<0:
        res=-1
    else:
        res=0
    return res
