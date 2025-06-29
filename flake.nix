{
  description = "megamek.necronomicons.com";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        lib = pkgs.lib;

        deps = [
          (pkgs.python3.withPackages (ps: [
            # Base
            ps.flask
            ps.flask_login
          ]
          ))
        ];
      in
      {
        packages = rec {
        };
        devShells.default = pkgs.mkShellNoCC {
            packages = deps ++ [
              pkgs.mypy
            ];
        };
      }
    );
}
