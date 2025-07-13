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
        mm0_49 = import ./servers/0_49.nix { inherit pkgs; };
        mm0_50 = import ./servers/0_50.nix { inherit pkgs; };
        lib = pkgs.lib;
        prefix = prefix: with lib.attrsets; mapAttrs' (name: value: nameValuePair (prefix+"-"+name) value);

        python3 = pkgs.python3.override {
          self = python3;
          packageOverrides = pyfinal: pyprev: {
            quart-auth = pyfinal.callPackage ./quart-auth.nix { };
          };
        };
        py = (python3.withPackages (ps: [
          # Base
          ps.pydantic
          ps.aiofiles
          ps.aioshutil

          ps.quart
          ps.quart-auth
          ps.hypercorn
        ]));

        config = {
          base_path = "";
          available_configs = {
            "0.49" = mm0_49.config;
            "0.50" = mm0_50.config;
          };
        };
        config_file = pkgs.writeText "config.json" ( builtins.toJSON config);
        dev = pkgs.writeShellApplication {
          name = "megamech-multi-server-dev";

          text = ''
            cd ./src
            export MEGAMEK_MULTI_SERVER_CONFIG="${config_file}"
            ${py}/bin/python -m megamek-multi-server ${config_file}
          '';
        };
        prod = pkgs.writeShellApplication {
          name = "megamech-multi-server";

          text = ''
            cd ./src
            export MEGAMEK_MULTI_SERVER_CONFIG="${config_file}"
            ${py}/bin/hypercorn megamek-multi-server:app
          '';
        };
        prod-app = {
          type = "app";
            program = "${prod}/bin/megamech-multi-server";
            meta.description = "MegaMek multi-server";
        };
      in
      {
        packages = (prefix "mm-0_49" mm0_49.packages) // (prefix "mm-0_50" mm0_50.packages) // {
          inherit dev prod py;
          default = prod;
        };
        apps = (prefix "mm-0_49" mm0_49.apps) // (prefix "mm-0_50" mm0_50.apps) // {
          dev = {
            type = "app";
            program = "${dev}/bin/megamech-multi-server-dev";
            meta.description = "Run app in development mode.";
          };
          prod = prod-app;
          default = prod-app;
        };
        devShells.default = pkgs.mkShellNoCC {
          packages = [
            py
            pkgs.mypy
          ];
        };
      }
    );
}
