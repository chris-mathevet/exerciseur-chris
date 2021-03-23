import code_etu

def test_1():
    return "Vous passez avec brio le test 1"

def test_deux():
    assert 2 + 2 == 4

def test_trois():
    assert code_etu.a == 5, "Damnation, a ne vaut pas 5"
