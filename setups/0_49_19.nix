{ pkgs }: let
    # Used JDK for this version
    jdk = pkgs.jdk21_headless;

    # Utils
    utils = import ./utils.nix { lib = pkgs.lib; };
    
    # Source for the entire MegaMek application
    version = "0.49.19.1";
    src = pkgs.fetchzip {
        url = "https://github.com/MegaMek/megamek/releases/download/v${version}/megamek-${version}.tar.gz";
        hash = "sha256-8gNCKkZkPZxvxBgeRtpy2yhhxEaiiRJkHvnUAFiYY0s=";
    };
    classpath = utils.classpath src [
        "MegaMek.jar"
        "lib/jackson-databind-2.14.2.jar"
        "lib/jackson-annotations-2.14.2.jar"
        "lib/jackson-dataformat-yaml-2.14.2.jar"
        "lib/jackson-core-2.14.2.jar"
        "lib/flatlaf-3.0.jar"
        "lib/SerialKiller-master-SNAPSHOT.jar"
        "lib/jakarta.mail-2.0.1.jar"
        "lib/xstream-1.4.20.jar"
        "lib/jaxb-runtime-4.0.2.jar"
        "lib/jaxb-core-4.0.2.jar"
        "lib/jakarta.xml.bind-api-4.0.0.jar"
        "lib/commons-text-1.10.0.jar"
        "lib/log4j-core-2.20.0.jar"
        "lib/freemarker-2.3.31.jar"
        "lib/snakeyaml-1.33.jar"
        "lib/commons-collections-3.2.2.jar"
        "lib/commons-configuration-1.10.jar"
        "lib/commons-lang-2.6.jar"
        "lib/commons-logging-1.2.jar"
        "lib/jakarta.activation-2.0.1.jar"
        "lib/mxparser-1.2.2.jar"
        "lib/angus-activation-2.0.0.jar"
        "lib/jakarta.activation-api-2.1.1.jar"
        "lib/commons-lang3-3.12.0.jar"
        "lib/log4j-api-2.20.0.jar"
        "lib/xmlpull-1.1.3.1.jar"
        "lib/txw2-4.0.2.jar"
        "lib/istack-commons-runtime-4.1.1.jar"
    ];
    exe = [
        "${jdk}/bin/java"
        "-Xmx512m"
        "--add-opens"
        "java.base/java.util=ALL-UNNAMED"
        "--add-opens"
        "java.base/java.util.concurrent=ALL-UNNAMED"
        "-Dsun.awt.disablegrab=true"
        "-classpath"
        classpath
        "megamek.MegaMek"
    ];

    # Package to check that the server meets all dependencies
    check-deps = pkgs.writeShellApplication {
        name = "check-megamek-deps";
        text = ''
        ${jdk}/bin/jdeps \
            --multi-release base \
            --missing-deps \
            -classpath "${classpath}" \
            "${src}/lib/MegaMek.jar"
        '';
    };
in rec {
    packages = { inherit src check-deps; };
    apps = {
        check-deps = {
            type = "app";
            program = "${check-deps}/bin/check-megamek-deps";
            meta.description = "Check dependencies linked";
        };
    };

    server = pkgs.lib.makeOverridable ({ meks, boards, config, gameoptions, setup, game }: let
        config' = if gameoptions != null
            then config.override { inherit gameoptions; }
            else config;
    in {
        inherit version exe game;
        setup = if setup != null
            then setup
            else lib.mkSetup {
                inherit meks boards;
                config = config';
            };
    }) {
        inherit (lib) meks boards config;
        gameoptions = null;
        setup = null;
        game = null;
    };

    lib = {
        inherit version exe;
        meks = pkgs.stdenvNoCC.mkDerivation {
            pname = "megamek-meks";
            inherit version;
            src = src;
            installPhase = ''cp -r data/mechfiles/ $out'';
        };
        boards = pkgs.stdenvNoCC.mkDerivation {
            pname = "megamek-boards";
            inherit version;
            src = src;
            installPhase = ''cp -r data/boards/ $out'';
        };
        config = pkgs.lib.makeOverridable ({ gameoptions, derivation-name }: pkgs.stdenvNoCC.mkDerivation {
            name = derivation-name;
            src = src;
            installPhase = ''
                mkdir -p $out
                cp mmconf/bot.properties $out
                cp mmconf/log4j2.xml $out
                cp mmconf/princessBehaviors.xml $out
                cp mmconf/princess_bot.properties $out
                cp mmconf/serialkiller.xml $out
            '' + (if gameoptions != null then ''
                cp "${gameoptions}" "$out/gameoptions.xml"
            '' else "");
        }) {
            derivation-name = "megamek-config-${version}";
            # Unlike other configurations MegaMek has its gameoptions defaults
            #   in the code instead of a file with default values.
            gameoptions = null;
        };
        mkSetup = {meks, boards, config}: with utils.setup; [
            (mkdir "logs")
            (mkdir "data")
            (link "${meks}" "data/mechfiles")
            (link "${boards}" "data/boards")
            (link "${config}" "mmconf")
        ];
    };
}
