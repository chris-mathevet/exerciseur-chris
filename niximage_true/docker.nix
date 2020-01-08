with (import <nixpkgs> {});

let notre_exerciseur = python3Packages.buildPythonApplication {
    src = ./ToujoursContent;
    name = "toujoursContent";
    propagatedBuildInputs = with python3Packages; [ cbor ];
};

in
dockerTools.buildImage {
  name = "toujoursContentDocker";
  tag = "latest";

  contents = [ notre_exerciseur ];

  config = {
    Cmd = ["/bin/daemon.py"];
  };
}
