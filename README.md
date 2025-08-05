# MegaMek multi-server
Small service that allows to spawn multiple [MegaMek](https://megamek.org/)
servers and close them once you are done.

It support supports multiple versions of MegaMek simultaneously.

For now all pages are in catalan (we'll see about i18n later on).

This project is in early development.

## Configuring your own server
This project is designed to be used with Nix. To make a server override the
`prod` package with the configuration you need.

Here is an example:
```nix
default = megamek-multi-server.packages.${system}.prod.override {
    servers = let
        v0_49_20 = megamek-multi-server.lib.${system}.v0_49_20;
        v0_50_06 = megamek-multi-server.lib.${system}.v0_50_06;
    in {
        "0.49.20" = v0_49_20.server;
        "0.50.06" = v0_50_06.server;
        "0.50.06 with custom options" = v0_50_06.server.override {
            gameoptions = ./gameoptions-example.xml;
        };
    };
    passwords-file = "/opt/megamek-server/passwords.txt";
    hypercorn-config = {
        # HTTPS example using Let's Encrypt
        bind = "[::]:443";
        server_names = ["example.com"];
        certfile = "/etc/letsencrypt/live/example.com/fullchain.pem";
        keyfile = "/etc/letsencrypt/live/example.com/privkey.pem";
    };
};
```

This is really flexible and you can change the configuration, the meks, and the
boards available. You can even add your own MegaMek versions as long as the
final configuration follows the expected schema (which for now is not stable and
changes version to version).

> [!NOTE]
> I consider the intermediary configuration files internal, but nothing stops
> you from creating your `config.json` and using it.
>
