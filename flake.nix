{
  description = "Flake for multiple MegaMek servers.";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
    nix-std.url = "github:chessai/nix-std";
  };

  outputs = { self, nixpkgs, flake-utils, nix-std }:
  flake-utils.lib.eachDefaultSystem (system: let
    std = nix-std.lib;
    pkgs = import nixpkgs { inherit system; };
    outputs = import ./nix { inherit pkgs std; };
  in outputs);
}