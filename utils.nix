{ pkgs }: {
    password-file = passwords: let
        contents = pkgs.lib.attrsets.foldlAttrs (acc: name: value: acc + "${name} ${value}\n") "" passwords;
    in pkgs.writeText "passwords.txt" contents;

    servers-file = servers: let
        contents = builtins.toJSON servers;
    in pkgs.writeText "servers.json" contents;

    server-from = server: {
        inherit (server.lib) version exe;
        setup = server.lib.setup {};
    };
}
