{ pkgs }: pkgs.lib.makeOverridable (
{ extra-dependencies }: let
    python3 = pkgs.python3.override {
        self = python3;
        packageOverrides = pyfinal: pyprev: {
            quart-auth = pyfinal.callPackage ./quart-auth.nix { };
        };
    };
    
    deps = ps: [
        # Base
        ps.pydantic
        ps.aiofiles
        ps.aioshutil

        ps.quart
        ps.quart-auth
    ] ++ (extra-dependencies ps);

in python3.withPackages deps
) {
    extra-dependencies = ps: [];
}
