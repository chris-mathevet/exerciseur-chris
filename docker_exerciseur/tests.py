from exerciseur import *

def test_démon_empaquete_dépaquete():
    ed = ExerciseurDémonPython('exemples/ToujoursConent')
    p = ed.empaquète()
    with p as edx:
        edx.construire()
