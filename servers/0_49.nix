{ pkgs }: let
    lib = pkgs.lib;
    jdk = pkgs.jdk21_headless;
    escapeShellArgs = lib.strings.escapeShellArgs;
    concatStringsSep = lib.strings.concatStringsSep;
    mapping = target: sources: { inherit target sources; };

    mmconf = mapping "mmconf" [
        "${src}/sentry.properties"
        "${src}/mmconf/log4j2.xml"
        "${src}/mmconf/serialkiller.xml"
    ];
    mechs = mapping "data/mechfiles" [ "${src}/data/mechfiles" ];
    maps = mapping "data/boards" [ "${src}/data/boards" ];

    libs = [
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

    src = pkgs.fetchzip {
        url = "https://github.com/MegaMek/megamek/releases/download/v0.49.19.1/megamek-0.49.19.1.tar.gz";
        hash = "sha256-8gNCKkZkPZxvxBgeRtpy2yhhxEaiiRJkHvnUAFiYY0s=";
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
        mmconf = [ mmconf ];
        mechs = [ mechs ];
        maps = [ maps ];
    };
}