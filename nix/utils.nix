{ pkgs }: let
    attrsets = pkgs.lib.attrsets;
    toJSON = value: let
        is-not-override = (n: v: n != "override" && n != "overrideDerivation");
        clean = attrsets.filterAttrsRecursive is-not-override value; 
    in builtins.toJSON clean;
    
in {
    password-file = passwords: let
        contents = attrsets.foldlAttrs (acc: name: value: acc + "${name} ${value}\n") "" passwords;
    in pkgs.writeText "passwords.txt" contents;

    config-file = config: pkgs.writeText "config.json" (toJSON config);
}
