import junit.framework.*;

public class TestPersonnage extends TestCase{

    private String [] noms = {"a", "", "toto", "gimli", "legolas"};
    private int [] barbes = {65, 0, 23, 14, 54};
    private int [] oreilles = {15, 10, 14, 7, 2};


    public void testPersonnage() throws Exception { 
        for(int i = 0; i<5; i++)
        {
            Personnage p = new Personnage(noms[i], barbes[i], oreilles[i]);
            assertEquals( "La méthode getNom ne semble pas correcte",noms[i],p.getNom());
            assertEquals( "La méthode getBarbe ne semble pas correcte",barbes[i],p.getBarbe());
            assertEquals( "La méthode tailleOreilles ne semble pas correcte",oreilles[i],p.tailleOreilles());
        }
    }
}

