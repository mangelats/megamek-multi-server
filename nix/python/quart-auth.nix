{
  lib,
  buildPythonPackage,
  fetchFromGitHub,
  pdm-backend,
  quart,
}:

buildPythonPackage rec {
  pname = "quart-auth";
  version = "0.11.0";

  src = fetchFromGitHub {
    owner = "pgjones";
    repo = "quart-auth";
    rev = "84064df3c819b37ad43afcb28fe5c0db25093eef";
    hash = "sha256-QNMw/ZOW/nfsd1fNTqkkvfrClYauiJpNhGVUFDbjAJI=";
  };
  propagatedBuildInputs = [ quart ];

  # do not run tests
  doCheck = false;

  # specific to buildPythonPackage, see its reference
  pyproject = true;
  build-system = [
    pdm-backend
  ];
}
