{ lib }: {
    classpath =
        src: paths: lib.strings.concatStringsSep ":" (map (path: "${src}/${path}") paths);

    setup = {
        mkdir = path: { type = "mkdir"; inherit path; };
        link = source: target: { type = "link"; inherit target source; };
    };
}
