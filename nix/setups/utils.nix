{ lib }: {
    classpath =
        src: paths: lib.strings.concatStringsSep ":" (map (path: "${src}/${path}") paths);

    setup = {
        mkdir = path: { type = "mkdir"; inherit path; };
        link = source: target: { type = "link"; inherit target source; };
    };

    heap-size = { min ? null, max ? null }: builtins.filter (v: v != null) [
        (if min == null then null else "-Xms${min}")
        (if max == null then null else "-Xmx${max}")
    ];
}
