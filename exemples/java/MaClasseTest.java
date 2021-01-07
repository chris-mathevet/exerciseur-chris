import junit.framework.*;
public class MaClasseTest extends TestCase{
      public void testCalculer() throws Exception {
              assertEquals(2,MaClasse.calculer(1,1));
                }
      public void testCalculer2() throws Exception {
              assertEquals("Sur l'entree (1,1), votre fonction n'a pas fait ce qui etait attendu",3,MaClasse.calculer(1,1));
                }
      public void testCalculer3() throws Exception {

              assertEquals("Sur l'entree (1,1), votre fonction n'a pas fait ce qui etait attendu",4,MaClasse.calculer(1,1));
                }
      public void testCalculer4() throws Exception {
              assertEquals("Sur l'entree (1,1), votre fonction n'a pas fait ce qui etait attendu",2,MaClasse.calculer(1,1));
                }
}
