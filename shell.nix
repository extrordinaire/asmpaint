{ pkgs ? import <nixpkgs> {} }:

let
  libPaths = [
    pkgs.gtk2
    pkgs.mesa
    pkgs.xorg.libX11
    pkgs.xorg.libXext
    pkgs.xorg.libXrender
    pkgs.xorg.libXtst
    pkgs.xorg.libXi
    pkgs.xorg.libXrandr
    pkgs.xorg.libXcursor
    pkgs.xorg.libXdamage
    pkgs.xorg.libXfixes
    pkgs.xorg.libXcomposite
    pkgs.alsa-lib
    pkgs.fontconfig
    pkgs.freetype
    pkgs.gnome2.GConf
    pkgs.glib
  ];

in pkgs.mkShell {
  buildInputs = libPaths;

  shellHook = ''
    export LD_LIBRARY_PATH=${
      builtins.concatStringsSep ":" (map (p: "${p}/lib") libPaths)
    }:$LD_LIBRARY_PATH

    echo "✅ Environment ready. Now run: ./processing-3.5.4/processing"
  '';
}
