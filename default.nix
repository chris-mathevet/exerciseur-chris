{pkgs ? (import <nixpkgs> {})}:

with pkgs;

python3Packages.buildPythonPackage rec {
  pname = "docker-exerciseur";
  version = "0.0.1";

  propagatedBuildInputs = with python3Packages; [docker cbor setuptools];

  src = ./.;

  doCheck = false;

}
