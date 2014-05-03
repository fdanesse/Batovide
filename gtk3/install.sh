#!/bin/sh

TARGET=$HOME/Batovide
rm -rf $TARGET

echo "Copiando archivos en $TARGET"
cp . -a $TARGET

chmod 755 $TARGET/IdeMain.py
chmod 755 $TARGET/Iconos/batovi.png

echo "Configurando tipos MIME"
mkdir -p $HOME/.local/share/applications/
mkdir -p $HOME/.local/share/mime/packages/
cp $TARGET/mimetypes.xml $HOME/.local/share/mime/packages/Batovide.xml
update-mime-database $HOME/.local/share/mime/

echo "Instalando icono en el menú"
sed "s:REPLACE:$TARGET:" $TARGET/Batovide.desktop -i
cp $TARGET/Batovide.desktop $HOME/.local/share/applications/
update-desktop-database $HOME/.local/share/applications/

COMPLETED="Batovide se ha instalado correctamente"

echo $COMPLETED
