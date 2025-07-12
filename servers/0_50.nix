{ pkgs }: let
    lib = pkgs.lib;
    jdk = pkgs.jdk21_headless;
    escapeShellArgs = lib.strings.escapeShellArgs;
    concatStringsSep = lib.strings.concatStringsSep;
    mapping = target: sources: { inherit target sources; };

    mmconf = mapping "mmconf" [ "${src}/sentry.properties" "${src}/mmconf/log4j2.xml" ];
    mechs = mapping "data/mekfiles" [ "${src}/data/mekfiles" ];
    maps = mapping "data/boards" [ "${src}/data/boards" ];

    libs = [
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

    src = pkgs.fetchzip {
        url = "https://github.com/MegaMek/megamek/releases/download/v0.50.06/MegaMek-0.50.06.tar.gz";
        hash = "sha256-1gPe34RFgHsL+wx9HmqpFHlSKUqFeFYkq1SJQwv4I1Y=";
    };
    classpath = (concatStringsSep ":" (map (path: "${src}/${path}") libs));
    process = [
        "${jdk}/bin/java"
        "-Xmx4096m"
        "--add-opens"
        "java.base/java.util=ALL-UNNAMED"
        "--add-opens"
        "java.base/java.util.concurrent=ALL-UNNAMED"
        "-Dsun.awt.disablegrab=true"
        "-classpath"
        "${classpath}"
        "megamek.MegaMek"
    ];

    check_deps = pkgs.writeShellApplication {
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
    packages =  { inherit src check_deps; };
    apps = {
        check_deps = {
            type = "app";
            program = "${packages.check_deps}/bin/check-megamek-deps";
            meta.description = "Check dependencies linked";
        };
    };
    config = {
        inherit process;
        mm_version = "0.50.06";
        mmconf = { default = mmconf; };
        mechs = { default = mechs; };
        maps = { default = maps; };
    };
}
