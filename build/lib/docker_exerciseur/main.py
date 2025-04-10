import argparse
from docker_exerciseur import constructeur
from docker_exerciseur import testeur

parser = argparse.ArgumentParser()
parser.add_argument(
    "--verbose", help="affiche plus d'informations", action="store_true"
)

subparsers = parser.add_subparsers(dest='commande', required=True)

parser_construction = subparsers.add_parser('construit',
                                            parents=[constructeur.parser],
                                            description="Construit un oracle à partir d'un dossier source",
)

parser_test = subparsers.add_parser('test',
                                    parents=[testeur.parser],
                                    description="Teste un oracle")

def main():
    args = parser.parse_args()
    commande = args.commande
    if commande == 'test':
        testeur.main(args)
    elif commande == 'construit':
        constructeur.main(args)

if __name__ == "__main__":
    main()
