#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   JAMediaTerminal.py por:
#       Flavio Danesse      <fdanesse@gmail.com>
#                           CeibalJAM! - Uruguay

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
import sys
import mimetypes

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from gi.repository import GdkPixbuf
from gi.repository import Vte
from gi.repository import Pango

BASEPATH = os.path.dirname(__file__)

def get_boton(stock, tooltip):
    """Devuelve un botón generico."""

    boton = Gtk.ToolButton.new_from_stock(stock)
    boton.set_tooltip_text(tooltip)
    boton.TOOLTIP = tooltip
    
    return boton

def get_separador(draw = False, ancho = 0, expand = False):
    """Devuelve un separador generico."""
    
    separador = Gtk.SeparatorToolItem()
    separador.props.draw = draw
    separador.set_size_request(ancho, -1)
    separador.set_expand(expand)
    
    return separador

class JAMediaTerminal(Gtk.Box):
    """
    Terminal (NoteBook + Vtes) + Toolbar.
    """
    
    __gsignals__ = {
    "ejecucion":(GObject.SIGNAL_RUN_FIRST,
        GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,)),
    "reset":(GObject.SIGNAL_RUN_FIRST,
        GObject.TYPE_NONE, [])}
        
    def __init__(self):
        
        Gtk.Box.__init__(self,
            orientation = Gtk.Orientation.VERTICAL)
        
        self.notebook = NoteBookTerminal()
        self.toolbar = ToolbarTerminal()
        
        self.pack_start(self.notebook, True, True, 0)
        self.pack_start(self.toolbar, False, False, 0)
        
        self.show_all()
        
        self.toolbar.connect('accion', self.__accion_terminal)
        self.toolbar.connect('reset', self.__reset_terminal)
        
        self.notebook.agregar_terminal()
        self.notebook.connect("reset", self.__re_emit_reset)
        
    def __re_emit_reset(self, widget):
        """
        Cuando se resetea una terminal.
        """
        
        self.emit("reset")
        
    def __reset_terminal(self, widget, interprete):
        """
        Resetea la terminal en interprete según valor.
        """
        
        self.notebook.reset_terminal(interprete = interprete)
        
    def __accion_terminal(self, widget, accion):
        """
        Soporte para clipboard.
        """
        
        self.notebook.accion_terminal(accion)
        
    def ejecutar(self, archivo):
        """
        Ejecuta un archivo en una nueva terminal.
        """
        
        if os.path.exists(archivo):

            path = os.path.basename(archivo)
            
            terminal = self.notebook.agregar_terminal(
                path=path,
                interprete='/bin/bash',
                ejecutar=archivo)
        
            self.emit("ejecucion", terminal)
    
    def ejecute_script(self, dirpath, interprete, path_script, param):
        """
        Ejecuta un script con parámetros, en la terminal activa
        
        Por ejemplo:
            python setup.py sdist
            
            dirpath     =   directorio base donde se encuentra setup.py
            interprete  =   python en este caso
            path_script =   dirpath + 'setup.py'
            param       =   'sdist' en est caso
        """
        
        terminal = self.notebook.get_children()[self.notebook.get_current_page()].get_child()
        
        pty_flags = Vte.PtyFlags(0)
        
        terminal.fork_command_full(
            pty_flags,
            dirpath,
            (interprete, path_script, param),
            "", 0, None, None)
            
class NoteBookTerminal(Gtk.Notebook):
    """
    Notebook Contenedor de Terminales.
    """
    
    __gsignals__ = {
    "reset":(GObject.SIGNAL_RUN_FIRST,
        GObject.TYPE_NONE, [])}
        
    def __init__(self):
        
        Gtk.Notebook.__init__(self)
        
        self.set_scrollable(True)
        
        self.show_all()
        
        self.connect('switch_page', self.__switch_page)
        
    def agregar_terminal(self, path = os.environ["HOME"],
        interprete = "/bin/bash", ejecutar = None):
        """
        Agrega una nueva Terminal al Notebook.
        """
        
        ### Label.
        hbox = Gtk.HBox()
        
        imagen = Gtk.Image.new_from_stock(Gtk.STOCK_CLOSE, Gtk.IconSize.MENU)
        
        boton = Gtk.Button()
        boton.set_relief(Gtk.ReliefStyle.NONE)
        boton.set_size_request(12, 12)
        boton.set_image(imagen)
        
        text = "bash"
        
        if "bash" in interprete:
            text = "bash"
            
        elif "python" in interprete:
            text = "python"
            
        if "ipython" in interprete: text = "ipython"
            
        label = Gtk.Label(text)

        hbox.pack_start(label, False, False, 0)
        hbox.pack_start(boton, False, False, 0)
        
        ### Area de Trabajo.
        terminal = Terminal(
            path=path,
            interprete=interprete,
            archivo=ejecutar)
            
        scroll = Gtk.ScrolledWindow()

        scroll.set_policy(
            Gtk.PolicyType.AUTOMATIC,
            Gtk.PolicyType.AUTOMATIC)

        scroll.add(terminal)
        
        self.append_page(scroll, hbox)

        label.show()
        boton.show()
        imagen.show()
        
        self.show_all()
        
        boton.connect("clicked", self.__cerrar)
        terminal.connect("reset", self.__re_emit_reset)
        
        self.set_current_page(-1)
        
        return terminal
    
    def __re_emit_reset(self, widget):
        """
        Cuando se resetea una terminal.
        """
        
        self.emit("reset")
        
    def __switch_page(self, widget, widget_child, indice):
        """
        Cuando el usuario selecciona una lengüeta en el notebook.
        """
        
        widget_child.child_focus(True)
        
    def reset_terminal(self, path = os.environ["HOME"],
        interprete = "/bin/bash"):
        """
        Resetea la terminal activa, a un determinado interprete.
        """
        
        if not self.get_children():
            self.agregar_terminal(path, interprete)
            return
        
        text = "bash"
        
        if "bash" in interprete:
            text = "bash"
            
        elif "python" in interprete:
            text = "python"

        if "ipython" in interprete: text = "ipython"
        
        label = self.get_tab_label(self.get_children()[self.get_current_page()]).get_children()[0]
        label.set_text(text)
        
        terminal = self.get_children()[self.get_current_page()].get_child()
        terminal.set_interprete(path = path, interprete = interprete)
        
    def accion_terminal(self, accion):
        """
        Soporte para clipboard y agregar una terminal nueva.
        """
        
        if self.get_children():
            terminal = self.get_children()[self.get_current_page()].get_child()
            terminal.child_focus(True)
            
            if accion == 'copiar':
                if terminal.get_has_selection():
                    terminal.copy_clipboard()
                    
            elif accion == 'pegar':
                terminal.paste_clipboard()
                
            elif accion == "agregar":
                self.agregar_terminal()
            
        else:
            self.agregar_terminal()
            
            terminal = self.get_children()[self.get_current_page()].get_child()
            terminal.child_focus(True)
            
            if accion == 'copiar':
                if terminal.get_has_selection():
                    terminal.copy_clipboard()
                    
            elif accion == 'pegar':
                terminal.paste_clipboard()
        
    def __cerrar(self, widget):
        """
        Cerrar la terminal a través de su botón cerrar.
        """
        
        notebook = widget.get_parent().get_parent()
        paginas = notebook.get_n_pages()
        
        for indice in range(paginas):
            boton = self.get_tab_label(self.get_children()[indice]).get_children()[1]
            
            if boton == widget:
                self.remove_page(indice)
                break
        
class Terminal(Vte.Terminal):
    """
    Terminal Configurable en distintos intérpretes.
    """
    
    __gsignals__ = {
    "reset":(GObject.SIGNAL_RUN_FIRST,
        GObject.TYPE_NONE, [])}
        
    def __init__(self,
        path = os.environ["HOME"],
        interprete = "/bin/bash",
        archivo = None):
        
        Vte.Terminal.__init__(self)
        
        self.set_encoding('utf-8')
        font = 'Monospace ' + str(10)
        self.set_font(Pango.FontDescription(font))
        
        self.set_colors(
            Gdk.color_parse('#ffffff'),
            Gdk.color_parse('#000000'),[])
        
        self.path = path
        self.interprete = interprete
        
        self.show_all()

        self.__reset(archivo=archivo)
        
    def do_child_exited(self):
        """
        Cuando se hace exit en la terminal,
        esta se resetea.
        """
        
        self.__reset()
        self.emit("reset")
        
    def set_interprete(self, path = os.environ["HOME"],
        interprete = "/bin/bash"):
        """
        Setea la terminal a un determinado interprete.
        """
        
        self.path = path
        self.interprete = interprete

        self.__reset()
        
    def __reset(self, archivo = None):
        """
        Reseteo de la Terminal.
        """
        
        if archivo:
            interprete = "/bin/bash"
            
            try:
                if "python" in mimetypes.guess_type(archivo)[0]:
                    interprete = "python"
                    
                    if os.path.exists(os.path.join("/bin", interprete)):
                        interprete = os.path.join("/bin", interprete)
                        
                    elif os.path.exists(os.path.join("/usr/bin", interprete)):
                        interprete = os.path.join("/usr/bin", interprete)
                        
                    elif os.path.exists(os.path.join("/sbin", interprete)):
                        interprete = os.path.join("/sbin", interprete)
                        
                    elif os.path.exists(os.path.join("/usr/local", interprete)):
                        interprete = os.path.join("/usr/local", interprete)
                        
            except:
                return self.set_interprete() ### Cuando se ejecuta un archivo no ejecutable
                
            path = os.path.dirname(archivo)
            
            pty_flags = Vte.PtyFlags(0)
            
            self.fork_command_full(
                    pty_flags,
                    path,
                    (interprete,archivo),
                    "", 0, None, None)
                    
        else:
            interprete = self.interprete
            path = self.path
        
            pty_flags = Vte.PtyFlags(0)
            
            self.fork_command_full(
                    pty_flags,
                    path,
                    (interprete,),
                    "", 0, None, None)
        
        self.child_focus(True)

class ToolbarTerminal(Gtk.Toolbar):
    """
    Toolbar de JAMediaTerminal.
    """
    
    __gtype_name__ = 'ToolbarTerminal'
    
    __gsignals__ = {
    "accion":(GObject.SIGNAL_RUN_FIRST,
        GObject.TYPE_NONE, (GObject.TYPE_STRING,)),
    "reset":(GObject.SIGNAL_RUN_FIRST,
        GObject.TYPE_NONE, (GObject.TYPE_STRING,))}
        
    def __init__(self):
        
        Gtk.Toolbar.__init__(self,
            orientation = Gtk.Orientation.HORIZONTAL)
            
        ### Interpretes disponibles.
        bash_path = None
        python_path = None
        
        paths = os.environ["PATH"].split(':')
        
        for path in paths:
            if 'bash' in os.listdir(path):
                bash_path = os.path.join(path, 'bash')
                
            if 'python' in os.listdir(path):
                python_path = os.path.join(path, 'python')
                
            if bash_path and python_path: break
        
        for path in paths:
            if 'ipython' in os.listdir(path):
                python_path = os.path.join(path, 'ipython')
        
        ### Construcción.
        boton = get_boton(Gtk.STOCK_COPY, "Copiar")
        boton.connect("clicked", self.__emit_accion, "copiar")
        self.insert(boton, -1)
        
        boton = get_boton(Gtk.STOCK_PASTE, "Pegar")
        boton.connect("clicked", self.__emit_accion, "pegar")
        self.insert(boton, -1)
        
        self.insert(get_separador(draw = False,
            ancho = 0, expand = True), -1)
            
        ### Botón Agregar.
        archivo = os.path.join(
            BASEPATH,
            "Iconos", "acercar.png")
            
        boton = Gtk.ToolButton()
        imagen = Gtk.Image()
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(archivo, 24, 24)
        imagen.set_from_pixbuf(pixbuf)
        boton.set_icon_widget(imagen)
        imagen.show()
        boton.show()

        boton.set_tooltip_text("Agregar")
        boton.connect("clicked", self.__emit_accion, "agregar")
        self.insert(boton, -1)
        
        self.insert(get_separador(draw = False,
            ancho = 10, expand = False), -1)
            
        ### Botón bash.
        archivo = os.path.join(
            BASEPATH,
            "Iconos", "bash.png")
            
        boton = Gtk.ToolButton()
        imagen = Gtk.Image()
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(archivo, 24, 24)
        imagen.set_from_pixbuf(pixbuf)
        boton.set_icon_widget(imagen)
        imagen.show()
        boton.show()

        boton.set_tooltip_text("Bash")
        boton.connect("clicked", self.__emit_reset, bash_path)
        self.insert(boton, -1)
        
        ### Botón python.
        archivo = os.path.join(
            BASEPATH,
            "Iconos", "python.png")
            
        boton = Gtk.ToolButton()
        imagen = Gtk.Image()
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(archivo, 24, 24)
        imagen.set_from_pixbuf(pixbuf)
        boton.set_icon_widget(imagen)
        imagen.show()
        boton.show()

        boton.set_tooltip_text("python")
        boton.connect("clicked", self.__emit_reset, python_path)
        self.insert(boton, -1)
        
        self.show_all()
        
    def __emit_reset(self, widget, path):
        
        self.emit('reset', path)
        
    def __emit_accion(self, widget, accion):
        
        self.emit('accion', accion)
