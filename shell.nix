with (import <nixpkgs> {});

(python3.withPackages (ps: [ps.docker ps.setuptools ps.cbor])).env
