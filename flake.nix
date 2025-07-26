{
  description = "Flake for multiple MegaMek servers.";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
    nix-std.url = "github:chessai/nix-std";
  };

  outputs = { self, nixpkgs, flake-utils, nix-std }:
  flake-utils.lib.eachDefaultSystem (system: let
    std = nix-std.lib;
    pkgs = import nixpkgs { inherit system; };
    utils = import ./utils.nix { inherit pkgs; };
  in rec {
    lib = {
      # Note: v0.49.19.1 and v0.49.20 are incopatible even if their semver means
      #   they should be.
      v0_49_19 = import ./setups/0_49_19.nix { inherit pkgs; };
      v0_49_20 = import ./setups/0_49_20.nix { inherit pkgs; };
      v0_50_06 = import ./setups/0_50_06.nix { inherit pkgs; };
    };
    packages = {
      python = import ./python { inherit pkgs; };
      dev = pkgs.lib.makeOverridable ({ python, servers, passwords }: let
        passwords-file = utils.password-file passwords;
        servers-file = utils.servers-file servers;
      in pkgs.writeShellApplication {
            name = "megamek-multi-server-dev"; # rename to "serve"?
            text = ''
              cd ./src
              export MEGAMEK_MULTI_SERVER_SERVERS="${servers-file}"
              export MEGAMEK_MULTI_SERVER_PASSWORDS="${passwords-file}"
              ${python}/bin/python -m megamek_multi_server
            '';
          }
        ) {
          python = packages.python;
          servers = {
            "Stock MegaMek v0.49.19" = utils.server-from lib.v0_49_19;
            "Stock MegaMek v0.49.20" = utils.server-from lib.v0_49_20;
            "Stock MegaMek v0.50.06" = utils.server-from lib.v0_50_06;
          };
          passwords = {
            # test => password
            test = "scrypt:32768:8:1$lWV55EaDMutmo8c7$aa5600942ddcda2ae2e1dedfad51618336fa7314b931b920e3fd680d5b3b9f98973b1f8b1761a60d5d560afc1da57b7c615d82b75c44cfc552c1e254e0290e56";
          };
        };
      
      app = pkgs.python3Packages.buildPythonPackage rec {
        pname = "megamek_multi_server";
        version = "0.2.0";
        src = pkgs.fetchFromGitHub {
          owner = "mangelats";
          repo = "megamek-multi-server";
          rev = "4116cebb0e863d7ca2e83db88d6c03e12fdb1a93";
          hash = "sha256-UUymtVD2LJBEen16SU1/9dO8rY82uvs40zQZ5BohjR8=";
        };
        propagatedBuildInputs = [ packages.python ];
        
        pyproject = true;
        build-system = [
          pkgs.python3Packages.pdm-backend
        ];
      };
      
      prod = pkgs.lib.makeOverridable ({ python, servers, passwords, passwords-file, quart-config }: let
          passwords-file' = if passwords != null then
            (utils.password-file passwords)
          else
            passwords-file
          ;
          servers-file = utils.servers-file servers;
          quart-config-file = pkgs.writeText "quart-config.toml" (std.serde.toTOML quart-config);
        in pkgs.writeShellApplication {
          name = "megamek-multi-server";
          text = ''
            if [ -n "$QUART_SECRET_KEY" ]; then
              >&2 echo "Please set a QUART_SECRET_KEY"
              exit 1
            fi
            export MEGAMEK_MULTI_SERVER_SERVERS="''${MEGAMEK_MULTI_SERVER_SERVERS:-${servers-file}}"
            export MEGAMEK_MULTI_SERVER_PASSWORDS="''${MEGAMEK_MULTI_SERVER_PASSWORDS:-${passwords-file'}}"
            ${python}/bin/hypercorn --config "${quart-config-file} megamek_multi_server:app"
          '';
        }
      ) rec {
        python = packages.python.override { extra-dependencies = ps: [ packages.app ps.hypercorn ]; };
        servers = {
          "Stock MegaMek v0.49.20" = utils.server-from lib.v0_49_20;
          "Stock MegaMek v0.50.06" = utils.server-from lib.v0_50_06;
        };
        passwords = null;
        passwords-file = pkgs.writeText "passwords.txt" ""; # No logins by default
        quart-config = {
          bind = "localhost:80";
        };
      };
    };

    apps = {
      dev = {
        type = "app";
        program = "${packages.dev}/bin/megamek-multi-server-dev";
        meta.description = "Run app in development mode.";
      };
    };

    devShells.default = pkgs.mkShellNoCC {
      packages = [
        packages.python
        pkgs.mypy
        pkgs.isort
        pkgs.black
      ];
    };
  });
}
