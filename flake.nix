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
        
        deps = (ps: [
          # Base
          ps.pydantic
          ps.aiofiles
          ps.aioshutil

          ps.quart
          ps.quart-auth
        ]);
        py = (python3.withPackages deps);

        config = {
          base_path = "";
          available_configs = {
            "0.49" = mm0_49.config;
            "0.50" = mm0_50.config;
          };
        };
        config-file = pkgs.writeText "config.json" ( builtins.toJSON config);
        dev-passwords = pkgs.writeText "passwords.txt" ''
          test scrypt:32768:8:1$lWV55EaDMutmo8c7$aa5600942ddcda2ae2e1dedfad51618336fa7314b931b920e3fd680d5b3b9f98973b1f8b1761a60d5d560afc1da57b7c615d82b75c44cfc552c1e254e0290e56
        '';
        dev = pkgs.writeShellApplication {
          name = "megamech-multi-server-dev";

          text = ''
            cd ./src
            export MEGAMEK_MULTI_SERVER_CONFIG="${config-file}"
            export MEGAMEK_MULTI_SERVER_PASSWORDS="${dev-passwords}"
            ${py}/bin/python -m megamek_multi_server
          '';
        };
        package = pkgs.python3Packages.buildPythonPackage rec {
          pname = "megamek_multi_server";
          version = "0.1.0";
          src = pkgs.fetchFromGitHub {
            owner = "mangelats";
            repo = "megamek-multi-server";
            rev = "e8c6ca7367e61b1ba604dedcfccba8d3f4f38897";
            hash = "sha256-1HsVwcjYkhBn+88ZtDBKuYp8NvfKTsddHNPQ/NGo7XQ=";
          };
          propagatedBuildInputs = [ py ];
          
          pyproject = true;
          build-system = [
            pkgs.python3Packages.pdm-backend
          ];
        };
        prod-python = python3.withPackages (p: (deps p) ++ [
          package
          p.hypercorn
        ]);
        prod = pkgs.writeShellApplication {
          name = "megamech-multi-server";

          text = ''
            export MEGAMEK_MULTI_SERVER_CONFIG="${config-file}"
            if [ -n "$1" ]; then
              export MEGAMEK_MULTI_SERVER_PASSWORDS="$1"
            fi

            ${prod-python}/bin/hypercorn megamek_multi_server:app
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
          default = package;
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
            pkgs.isort
            pkgs.black
          ];
        };
      }
    );
}
