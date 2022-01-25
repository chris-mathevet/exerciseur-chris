with (import <nixpkgs> {});

(python3.withPackages (ps:
[
  ps.docker
  ps.setuptools
  ps.cbor
  ps.nose2
  ps.hypothesis
  ps.mypy
  ps.jinja2
])).env
