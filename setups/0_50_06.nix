{ pkgs }: let
    lib = pkgs.lib;

    # Used JDK for this version
    jdk = pkgs.jdk21_headless;


    # Utils
    utils = import ./utils.nix { inherit lib; };
    
    # Source for the entire MegaMek application
    version = "0.50.06";
    src = pkgs.fetchzip {
        url = "https://github.com/MegaMek/megamek/releases/download/v${version}/megamek-${version}.tar.gz";
        hash = "sha256-1gPe34RFgHsL+wx9HmqpFHlSKUqFeFYkq1SJQwv4I1Y=";
    };
    classpath = utils.classpath src [
        "lib/MegaMek.jar"
        "lib/jackson-databind-2.18.3.jar"
        "lib/jackson-annotations-2.18.3.jar"
        "lib/jackson-dataformat-yaml-2.18.3.jar"
        "lib/jackson-core-2.18.3.jar"
        "lib/flatlaf-extras-3.5.4.jar"
        "lib/flatlaf-3.5.4.jar"
        "lib/jakarta.mail-2.0.1.jar"
        "lib/xstream-1.4.21.jar"
        "lib/commons-io-2.18.0.jar"
        "lib/jaxb-runtime-4.0.5.jar"
        "lib/jaxb-core-4.0.5.jar"
        "lib/jakarta.xml.bind-api-4.0.2.jar"
        "lib/commons-collections4-4.5.0-M3.jar"
        "lib/commons-text-1.13.0.jar"
        "lib/commons-lang3-3.17.0.jar"
        "lib/log4j-core-2.24.3.jar"
        "lib/log4j-api-2.24.3.jar"
        "lib/freemarker-2.3.34.jar"
        "lib/commonmark-0.24.0.jar"
        "lib/gifencoder-0.10.1.jar"
        "lib/icu4j-77.1.jar"
        "lib/sentry-log4j2-8.3.0.jar"
        "lib/sentry-8.3.0.jar"
        "lib/snakeyaml-2.3.jar"
        "lib/jsvg-1.4.0.jar"
        "lib/jakarta.activation-2.0.1.jar"
        "lib/mxparser-1.2.2.jar"
        "lib/angus-activation-2.0.2.jar"
        "lib/jakarta.activation-api-2.1.3.jar"
        "lib/xmlpull-1.1.3.1.jar"
        "lib/txw2-4.0.5.jar"
        "lib/istack-commons-runtime-4.1.2.jar"
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
in {
    packages = { inherit src check-deps; };
    apps = {
        check-deps = {
            type = "app";
            program = "${check-deps}/bin/check-megamek-deps";
            meta.description = "Check dependencies linked";
        };
    };
    lib = rec {
        inherit version exe;
        meks = pkgs.stdenvNoCC.mkDerivation {
            name = "megamek-0.50-meks";
            src = src;
            installPhase = ''cp -r data/mekfiles/ $out'';
        };
        boards = pkgs.stdenvNoCC.mkDerivation {
            name = "megamek-0.50-boards";
            src = src;
            installPhase = ''cp -r data/boards/ $out'';
        };
        config = lib.makeOverridable ({ gameoptions, derivation-name }: pkgs.stdenvNoCC.mkDerivation {
            name = derivation-name;
            src = src;
            installPhase = ''
                mkdir -p $out
                cp sentry.properties $out
                cp mmconf/bot.properties $out
                cp mmconf/log4j2.xml $out
                cp mmconf/munitionLoadoutSettings.xml $out
                cp mmconf/princessBehaviors.xml $out
                cp mmconf/princess_bot.properties $out
            '' + (if gameoptions != null then ''
                cp "${gameoptions}" "$out/gameoptions.xml"
            '' else "");
        }) {
            derivation-name = "megamek-0.50-config";
            # Unlike other configurations MegaMek has its gameoptions defaults
            #   in the code instead of a file with default values.
            gameoptions = null;
        };
        setup = let
            default = { inherit meks boards config; };
            f = { meks, boards, config }: with utils.setup; [
                (mkdir "data/logs")
                (link "${meks}" "data/mekfiles")
                (link "${boards}" "data/boards")
                (link "${config}" "mmconf")
            ];
        in lib.makeOverridable f default;
    };
}
