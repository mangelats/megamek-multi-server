{ pkgs }: pkgs.lib.makeOverridable (
{ extra-dependencies }: let
    python3 = pkgs.python313.override {
        self = python3;
        packageOverrides = pyfinal: pyprev: {
            quart-auth = pyfinal.callPackage ./quart-auth.nix { };
        };
    };
    
    deps = ps: [
        # Base
        ps.psutil
        ps.types-psutil
        ps.aiofiles
        ps.aioshutil
        ps.pydantic
        ps.werkzeug

        ps.quart
        ps.quart-auth
    ] ++ (extra-dependencies ps);

in python3.withPackages deps
) {
    extra-dependencies = ps: [];
}
