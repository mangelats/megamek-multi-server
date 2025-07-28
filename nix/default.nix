{ pkgs, std }: let
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
          export QUART_QUART_AUTH_DURATION="86400" # 24 hours
          export MEGAMEK_MULTI_SERVER_SERVERS="${servers-file}"
          export MEGAMEK_MULTI_SERVER_PASSWORDS="${passwords-file}"
          ${python}/bin/python -m megamek_multi_server
        '';
      }
    ) {
      python = packages.python;
      servers = {
        "Stock MegaMek v0.49.19" = lib.v0_49_19.server;
        "Stock MegaMek v0.49.20" = lib.v0_49_20.server;
        "Stock MegaMek v0.50.06" = lib.v0_50_06.server;
      };
      passwords = {
        # test => password
        test = "scrypt:32768:8:1$lWV55EaDMutmo8c7$aa5600942ddcda2ae2e1dedfad51618336fa7314b931b920e3fd680d5b3b9f98973b1f8b1761a60d5d560afc1da57b7c615d82b75c44cfc552c1e254e0290e56";
      };
    };
    
    app = pkgs.python3Packages.buildPythonPackage rec {
      pname = "megamek_multi_server";
      version = "0.2.2";
      src = pkgs.fetchFromGitHub {
        owner = "mangelats";
        repo = "megamek-multi-server";
        rev = "ec5dc6fb2002ae4519f7163663b284b9ec63dc7a";
        hash = "sha256-8+zwsfi+0pF9VeHmI6+U+sMls+fbPp12d3HwlrvwyzI=";
      };
      propagatedBuildInputs = [ packages.python ];
      
      pyproject = true;
      build-system = [
        pkgs.python3Packages.pdm-backend
      ];
    };
    
    prod = pkgs.lib.makeOverridable ({ python, servers, passwords, passwords-file, hypercorn-config }: let
        passwords-file' = if passwords != null then
          (utils.password-file passwords)
        else
          passwords-file
        ;
        servers-file = utils.servers-file servers;
        hypercorn-config-file = pkgs.writeText "hypercorn-config.toml" (std.serde.toTOML hypercorn-config);
      in pkgs.writeShellApplication {
        name = "megamek-multi-server";
        text = ''
          export QUART_QUART_AUTH_DURATION="86400" # 24 hours
          export MEGAMEK_MULTI_SERVER_SERVERS="''${MEGAMEK_MULTI_SERVER_SERVERS:-${servers-file}}"
          export MEGAMEK_MULTI_SERVER_PASSWORDS="''${MEGAMEK_MULTI_SERVER_PASSWORDS:-${passwords-file'}}"
          ${python}/bin/hypercorn --config "${hypercorn-config-file}" megamek_multi_server:app
        '';
      }
    ) rec {
      python = packages.python.override { extra-dependencies = ps: [ packages.app ps.hypercorn ]; };
      servers = {
        "Stock MegaMek v0.49.20" = lib.v0_49_20.server;
        "Stock MegaMek v0.50.06" = lib.v0_50_06.server;
      };
      passwords = null;
      passwords-file = pkgs.writeText "passwords.txt" ""; # No logins by default
      hypercorn-config = {
        bind = "localhost:80";
      };
    };

    gen-pass = pkgs.writers.writePython3Bin "gen-pass" { libraries = [ pkgs.python3Packages.werkzeug ]; } ''
      from werkzeug.security import generate_password_hash
      from getpass import getpass

      if __name__ == '__main__':
          name = input("Username: ")
          password = getpass("Password (hidden): ")
          hash = generate_password_hash(password)
          print("Password file entry:")
          print(f"{name} {hash}")
    '';
  };

  apps = {
    dev = {
      type = "app";
      program = "${packages.dev}/bin/megamek-multi-server-dev";
      meta.description = "Run app in development mode.";
    };
    gen-pass = {
      type = "app";
      program = "${packages.gen-pass}/bin/gen-pass";
      meta.description = "Open script to generate password entries";
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
}
