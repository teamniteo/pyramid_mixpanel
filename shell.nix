let
  nixpkgs = builtins.fetchTarball {
    # https://github.com/NixOS/nixpkgs/tree/nixos-21.05 on 2021-09-12
    url = "https://github.com/nixos/nixpkgs/archive/8b0b81dab17753ab344a44c04be90a61dc55badf.tar.gz";
    sha256 =  "0rj17jpjxjcibcd4qygpxbq79m4px6b35nqq9353pns8w7a984xx";
  };
  pkgs = import nixpkgs { config = { allowUnfree = true; }; };
in

pkgs.mkShell {
  name = "dev-shell";
  buildInputs = [
    pkgs.pipenv
    pkgs.codespell
  ];

  shellHook = ''
  # create virtualenv in ./.venv
  export PIPENV_VENV_IN_PROJECT=1
  # pipenv reports it needs this
  export LANG=en_US.UTF-8
  # support for building wheels:
  # https://nixos.org/nixpkgs/manual/#python-setup.py-bdist_wheel-cannot-create-.whl
  unset SOURCE_DATE_EPOCH
  '';
}
