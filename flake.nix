{
  description = "Flake for the MegaMek multi-server";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        mm0_50 = import ./servers/0_50.nix { inherit pkgs; };
        lib = pkgs.lib;
        prefix = prefix: with lib.attrsets; mapAttrs' (name: value: nameValuePair (prefix+"-"+name) value);


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
        packages = prefix "mm-0_50" mm0_50.packages;
        apps = prefix "mm-0_50" mm0_50.apps;
        devShells.default = pkgs.mkShellNoCC {
          packages = deps ++ [
            pkgs.mypy
          ];
        };
      }
    );
}
