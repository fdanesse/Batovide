#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   Widget_Setup.py por:
#       Cristian García     <cristian99garcia@gmail.com>
#       Ignacio Rodriguez   <nachoel01@gmail.com>
#       Flavio Danesse      <fdanesse@gmail.com>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os

import gtk
import gobject
import gtksourceview2
import pango

from Widgets import My_FileChooser


def get_boton(stock, tooltip):
    """
    Devuelve un botón generico.
    """

    boton = gtk.ToolButton(stock)
    boton.set_tooltip_text(tooltip)
    boton.TOOLTIP = tooltip

    return boton


def get_separador(draw=False, ancho=0, expand=False):
    """
    Devuelve un separador generico.
    """

    separador = gtk.SeparatorToolItem()
    separador.props.draw = draw
    separador.set_size_request(ancho, -1)
    separador.set_expand(expand)

    return separador


class DialogoSetup(gtk.Dialog):
    """
    Dialogo para presentar Información de Instaladores.
    """

    __gtype_name__ = 'DialogoSetup'

    def __init__(self, parent_window=None, proyecto=None):

        gtk.Dialog.__init__(self,
            title="Construyendo instaladores.",
            parent=parent_window,
            flags=gtk.DIALOG_MODAL,
            buttons=("Cerrar", gtk.RESPONSE_ACCEPT))

        self.set_size_request(640, 480)
        self.set_border_width(15)

        self.notebook = Notebook_Setup(proyecto)

        self.vbox.pack_start(self.notebook, True, True, 0)

        self.maximize()


class Notebook_Setup(gtk.Notebook):
    """
    Contenedor de Información de Instaladores gnome y sugar.
    """

    __gtype_name__ = 'Notebook_Setup'

    def __init__(self, proyecto):

        gtk.Notebook.__init__(self)

        self.set_scrollable(True)

        self.proyecto = proyecto

        self.gnome_notebook = Gnome_Notebook(proyecto)
        self.sugar_notebook = Sugar_Notebook(proyecto)

        box = gtk.VBox()

        gnome_widget_icon = Widget_icon(tipo="gnome", proyecto=proyecto)

        box.pack_start(gnome_widget_icon, False, False, 0)
        box.pack_start(self.gnome_notebook, True, True, 0)

        self.append_page(box, gtk.Label("Proyecto gnome"))

        box = gtk.VBox()

        sugar_widget_icon = Widget_icon(tipo="sugar", proyecto=proyecto)

        box.pack_start(sugar_widget_icon, False, False, 0)
        box.pack_start(self.sugar_notebook, True, True, 0)

        self.append_page(box, gtk.Label("Proyecto Sugar"))

        self.show_all()

        gnome_widget_icon.connect("iconpath", self.__set_icon, "gnome")
        sugar_widget_icon.connect("iconpath", self.__set_icon, "sugar")

        gnome_widget_icon.connect("make", self.__make, "gnome")
        sugar_widget_icon.connect("make", self.__make, "sugar")

    def __make(self, widget, tipo):
        """
        Construye los instaladores.
        """

        if tipo == "gnome":
            self.gnome_notebook.make()

        elif tipo == "sugar":
            self.sugar_notebook.make()

        dialog = DialogoInfoInstall(
            parent_window=self.get_toplevel(),
            distpath=os.path.join(self.proyecto["path"], "dist"))

        dialog.run()

        dialog.destroy()

    def __set_icon(self, widget, iconpath, valor):
        """
        Setea el icono de la aplicación.
        """

        if valor == "gnome":
            self.gnome_notebook.setup_install(iconpath)

        elif valor == "sugar":
            self.sugar_notebook.setup_install(iconpath)


class Gnome_Notebook(gtk.Notebook):
    """
    Contenedor de información de instalador gnome.
    """

    __gtype_name__ = 'Gnome_Notebook'

    def __init__(self, proyecto):

        gtk.Notebook.__init__(self)

        self.set_scrollable(True)

        self.proyecto = proyecto

        self.install = Setup_SourceView()
        self.install.get_buffer().set_text("")

        self.append_page(
            self.get_scroll(self.install),
            gtk.Label("install.py"))

        self.show_all()

    def setup_install(self, iconpath):
        """
        Recolecta la información necesaria para generar los
        archivos de instalación y los presenta al usuario para
        posibles correcciones.
        """

        import commands
        import shutil
        import shelve

        ### Comenzar a generar el temporal
        activitydirpath = os.path.join("/tmp", "%s" % self.proyecto["nombre"])

        ### Borrar anteriores
        if os.path.exists(activitydirpath):
            commands.getoutput("rm -r %s" % activitydirpath)

        ### Copiar contenido del proyecto.
        shutil.copytree(self.proyecto["path"],
            activitydirpath, symlinks=False, ignore=None)

        if not self.proyecto["path"] in iconpath:
            newpath = os.path.join(activitydirpath, os.path.basename(iconpath))
            shutil.copyfile(iconpath, newpath)
            iconpath = newpath

        archivo = shelve.open("plantilla")
        text = str(archivo.get('install', ""))
        archivo.close()

        iconpath = iconpath.split(self.proyecto["path"])[-1]

        text = text.replace('mainfile', self.proyecto["main"])
        text = text.replace('iconfile', iconpath)

        self.install.get_buffer().set_text(text)

    def make(self):
        """
        Construye los archivos instaladores para su distribución.
        """

        import commands
        import zipfile

        activitydirpath = os.path.join("/tmp", "%s" % self.proyecto["nombre"])

        ### Escribir instalador.
        archivo_install = "%s/install.py" % (activitydirpath)
        install = self.__get_text(self.install.get_buffer())
        self.__escribir_archivo(archivo_install, install)

        ### Generar archivo de distribución "*.zip"
        zippath = "%s.zip" % (activitydirpath)

        ### Eliminar anterior.
        if os.path.exists(zippath):
            commands.getoutput("rm %s" % zippath)

        zipped = zipfile.ZipFile(zippath, "w")

        RECHAZAExtension = [".pyc", ".pyo", ".bak"]
        RECHAZAFiles = ["proyecto.ide", ".gitignore", "plantilla"]
        RECHAZADirs = [".git", "build", "dist"]

        ### Forzar eliminacion de dist
        for dir in os.listdir(activitydirpath):
            d = os.path.join(activitydirpath, dir)

            if os.path.isdir(d):
                if d.split("/")[-1] in RECHAZADirs:
                    commands.getoutput("rm -r %s" % d)

        for (archiveDirPath, dirNames, fileNames) in os.walk(activitydirpath):

            if not archiveDirPath.split("/")[-1] in RECHAZADirs:
                for fileName in fileNames:
                    if not fileName in RECHAZAFiles:
                        filePath = os.path.join(archiveDirPath, fileName)
                        extension = os.path.splitext(
                            os.path.split(filePath)[1])[1]

                        if not extension in RECHAZAExtension:
                            zipped.write(filePath,
                                filePath.split(activitydirpath)[1])

        zipped.close()

        distpath = os.path.join(self.proyecto["path"], "dist")

        if not os.path.exists(distpath):
            os.mkdir(distpath)

        ### Copiar el *.zip a la estructura del proyecto.
        commands.getoutput("cp %s %s" % (zippath, distpath))
        os.chmod(os.path.join(distpath,
            os.path.basename(zippath)), 0755)

        if os.path.exists(zippath):
            os.remove(zippath)
            commands.getoutput("rm -r %s" % activitydirpath)

    def __get_text(self, buffer):
        """
        Devuelve el contenido de un text buffer.
        """

        inicio, fin = buffer.get_bounds()
        texto = buffer.get_text(inicio, fin, 0)

        return texto

    def __escribir_archivo(self, archivo, contenido):
        """
        Escribe los archivos de instalación.
        """

        arch = open(archivo, "w")
        arch.write(contenido)
        arch.close()

    def get_scroll(self, sourceview):

        scroll = gtk.ScrolledWindow()

        scroll.set_policy(
            gtk.POLICY_AUTOMATIC,
            gtk.POLICY_AUTOMATIC)

        scroll.add(sourceview)

        return scroll


class Sugar_Notebook(gtk.Notebook):
    """
    Contenedor de información de instalador sugar.
    """

    __gtype_name__ = 'Sugar_Notebook'

    def __init__(self, proyecto):

        gtk.Notebook.__init__(self)

        self.set_scrollable(True)

        self.proyecto = proyecto

        self.activity_sourceview = Setup_SourceView()
        self.setup_sourceview = Setup_SourceView()

        self.append_page(
            self.get_scroll(self.activity_sourceview),
            gtk.Label("activity.info"))

        self.append_page(
            self.get_scroll(self.setup_sourceview),
            gtk.Label("setup.py"))

        self.show_all()

    def get_scroll(self, sourceview):

        scroll = gtk.ScrolledWindow()

        scroll.set_policy(
            gtk.POLICY_AUTOMATIC,
            gtk.POLICY_AUTOMATIC)

        scroll.add(sourceview)

        return scroll

    def setup_install(self, iconpath):
        """
        Recolecta la información necesaria para generar los
        archivos de instalación y los presenta al usuario para
        posibles correcciones.
        """

        import commands
        import shutil

        main_path = os.path.join(self.proyecto["path"], self.proyecto["main"])
        extension = os.path.splitext(os.path.split(main_path)[1])[1]
        main_name = self.proyecto["main"].split(extension)[0]

        extension = os.path.splitext(os.path.split(iconpath)[1])[1]
        newiconpath = os.path.basename(iconpath).split(extension)[0]

        activity = "[Activity]\nname = %s\nactivity_version = %s\nbundle_id = org.laptop.%s\nicon = %s\nexec = sugar-activity %s.%s -s\nmime_types =\nlicense = %s\nsummary = " % (self.proyecto["nombre"], self.proyecto["version"], self.proyecto["nombre"], newiconpath, main_name, main_name, self.proyecto["licencia"])
        setup = "#!/usr/bin/env python\n\nfrom sugar3.activity import bundlebuilder\nbundlebuilder.start()"

        ### Comenzar a generar el temporal
        activitydirpath = os.path.join(
            "/tmp", "%s.activity" % self.proyecto["nombre"])
        activityinfodirpath = os.path.join(activitydirpath, "activity")

        ### Borrar anteriores
        if os.path.exists(activitydirpath):
            commands.getoutput("rm -r %s" % activitydirpath)

        ### Copiar contenido del proyecto.
        shutil.copytree(self.proyecto["path"],
            activitydirpath, symlinks=False, ignore=None)

        ### Escribir archivos de instalación.
        if not os.path.exists(activityinfodirpath):
            os.mkdir(activityinfodirpath)

        newpath = os.path.join(activityinfodirpath,
            os.path.basename(iconpath))
        shutil.copyfile(iconpath, newpath)

        self.activity_sourceview.get_buffer().set_text(activity)
        self.setup_sourceview.get_buffer().set_text(setup)

    def make(self):
        """
        Construye los archivos instaladores para su distribución.
        """

        import commands
        import zipfile

        activitydirpath = os.path.join(
            "/tmp", "%s.activity" % self.proyecto["nombre"])
        activityinfodirpath = os.path.join(activitydirpath, "activity")

        infopath = os.path.join(activityinfodirpath, "activity.info")
        setuppath = os.path.join(activitydirpath, "setup.py")

        activity = self.__get_text(self.activity_sourceview.get_buffer())
        setup = self.__get_text(self.setup_sourceview.get_buffer())

        self.__escribir_archivo(infopath, activity)
        self.__escribir_archivo(setuppath, setup)

        ### Borrar archivos innecesarios
        nombre = self.proyecto["nombre"]
        desktop = "%s.desktop" % nombre

        borrar = ["MANIFEST", desktop, "setup.cfg"]

        for file in borrar:
            path = os.path.join(activitydirpath, file)

            if os.path.exists(path):
                os.remove(path)

        ### Generar archivo de distribución "*.xo"
        zippath = "%s.xo" % (activitydirpath)

        if os.path.exists(zippath):
            commands.getoutput("rm %s" % zippath)

        zipped = zipfile.ZipFile(zippath, "w")

        RECHAZAExtension = [".pyc", ".pyo", ".bak"]
        RECHAZAFiles = ["proyecto.ide", ".gitignore"]
        RECHAZADirs = [".git", "build", "dist"]

        ### Forzar eliminacion de dist
        for dir in os.listdir(activitydirpath):
            d = os.path.join(activitydirpath, dir)

            if os.path.isdir(d):
                if d.split("/")[-1] in RECHAZADirs:
                    commands.getoutput("rm -r %s" % d)

        for (archiveDirPath, dirNames, fileNames) in os.walk(activitydirpath):
            if not archiveDirPath.split("/")[-1] in RECHAZADirs:
                for fileName in fileNames:
                    if not fileName in RECHAZAFiles:
                        filePath = os.path.join(archiveDirPath, fileName)
                        extension = os.path.splitext(os.path.split(filePath)[1])[1]

                        if not extension in RECHAZAExtension:
                            zipped.write(filePath, filePath.split(activitydirpath)[1])

        zipped.close()

        distpath = os.path.join(self.proyecto["path"], "dist")

        if not os.path.exists(distpath):
            os.mkdir(distpath)

        ### Copiar el *.xo a la estructura del proyecto.
        commands.getoutput("cp %s %s" % (zippath, distpath))
        os.chmod(os.path.join(distpath, os.path.basename(zippath)), 0755)

        if os.path.exists(zippath):
            os.remove(zippath)
            commands.getoutput("rm -r %s" % activitydirpath)

    def __get_text(self, buffer):
        """
        Devuelve el contenido de un text buffer.
        """

        inicio, fin = buffer.get_bounds()
        texto = buffer.get_text(inicio, fin, 0)

        return texto

    def __escribir_archivo(self, archivo, contenido):
        """
        Escribe los archivos de instalación.
        """

        arch = open(archivo, "w")
        arch.write(contenido)
        arch.close()


class Setup_SourceView(gtksourceview2.View):
    """
    Widget para mostrar contenido de archivos instaladores.
    """

    __gtype_name__ = 'Setup_SourceView'

    def __init__(self):

        gtksourceview2.View.__init__(self)

        self.set_buffer(gtksourceview2.Buffer())

        self.modify_font(pango.FontDescription('Monospace 10'))

        self.show_all()


class Widget_icon(gtk.Frame):
    """
    Widget que permite al usuario seleccionar el ícono de la aplicación.
    """

    __gtype_name__ = 'Widget_icon'

    __gsignals__ = {
    'iconpath': (gobject.SIGNAL_RUN_FIRST,
        gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
    'make': (gobject.SIGNAL_RUN_FIRST,
        gobject.TYPE_NONE, [])}

    def __init__(self, tipo="gnome", proyecto=None):

        gtk.Frame.__init__(self)

        self.set_label(" Selecciona un Icono para Tu Aplicación ")
        self.set_border_width(15)

        self.tipo = tipo # FIXME: tipo debe determinar que formato de ico se permite (svg para sugar)
        self.proyecto = proyecto

        toolbar = gtk.Toolbar()

        self.image = gtk.Image()
        self.image.set_size_request(50, 50)

        boton = get_boton(gtk.STOCK_OPEN, "Buscar Archivo")
        self.aceptar = gtk.Button("Construir Instalador")
        self.aceptar.set_sensitive(False)

        toolbar.insert(get_separador(draw=False, ancho=10, expand=False), -1)

        item = gtk.ToolItem()
        item.add(self.image)
        toolbar.insert(item, -1)

        toolbar.insert(get_separador(draw=False, ancho=10, expand=False), -1)

        toolbar.insert(boton, -1)

        toolbar.insert(get_separador(draw=False, ancho=0, expand=True), -1)

        item = gtk.ToolItem()
        item.add(self.aceptar)
        toolbar.insert(item, -1)

        toolbar.insert(get_separador(draw=False, ancho=10, expand=False), -1)

        self.add(toolbar)

        self.show_all()

        boton.connect("clicked", self.__open_filechooser)
        self.aceptar.connect("clicked", self.__Construir)

    def __Construir(self, widget):
        """
        Manda construir el instalador.
        """

        self.emit("make")

    def __open_filechooser(self, widget):
        """
        Abre un filechooser para seleccionar un ícono.
        """

        mime = "image/*"

        if self.tipo == "sugar":
            mime = "image/svg+xml"

        filechooser = My_FileChooser(
            parent_window=self.get_toplevel(),
            action_type=gtk.FILE_CHOOSER_ACTION_OPEN,
            title="Seleccionar Icono . . .",
            path=self.proyecto["path"],
            mime_type=[mime])

        filechooser.connect('load', self.__emit_icon_path)

    def __emit_icon_path(self, widget, iconpath):
        """
        Cuando el usuario selecciona un icono para la aplicación.
        """

        iconpath = str(iconpath).replace("//", "/")

        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(iconpath, 50, 50)
        self.image.set_from_pixbuf(pixbuf)

        self.aceptar.set_sensitive(True)
        self.emit("iconpath", iconpath)


class DialogoInfoInstall(gtk.Dialog):
    """
    Dialogo para informar al usuario donde encontrar el
    paquete de distribución de su proyecto.
    """

    __gtype_name__ = 'DialogoInfoInstall'

    def __init__(self, parent_window=None, distpath=None):

        gtk.Dialog.__init__(self,
            title="Construcción de instaladores.",
            parent=parent_window,
            flags=gtk.DIALOG_MODAL,
            buttons=("Cerrar", gtk.RESPONSE_ACCEPT))

        self.set_size_request(420, 180)
        self.set_border_width(15)

        label = gtk.Label(u"Proceso de Construcción de Instalador Culminado.\nPuedes Encontrar el Instalador de tu Proyecto en:\n\n%s" % (distpath))

        label.show()

        self.vbox.pack_start(label, True, True, 0)
