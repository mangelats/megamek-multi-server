{ pkgs }: let
    attrsets = pkgs.lib.attrsets;
in {
    password-file = passwords: let
        contents = attrsets.foldlAttrs (acc: name: value: acc + "${name} ${value}\n") "" passwords;
    in pkgs.writeText "passwords.txt" contents;

    servers-file = servers: let
        is-not-override = (n: v: n != "override" && n != "overrideDerivation");
        clean-servers = attrsets.filterAttrsRecursive is-not-override servers; 
        contents = builtins.toJSON clean-servers;
    in pkgs.writeText "servers.json" contents;
}
