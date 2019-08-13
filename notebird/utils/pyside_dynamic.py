# Copyright (c) 2011 Sebastian Wiesner <lunaryorn@gmail.com>
# Modifications by Charl Botha <cpbotha@vxlabs.com>
# * customWidgets support (registerCustomWidget() causes segfault in
#   pyside 1.1.2 on Ubuntu 12.04 x86_64)
# * workingDirectory support in loadUi
# Modifications were made to work with PySide2

# Original version was here:
# https://github.com/lunaryorn/snippets/blob/master/qt4/designer/pyside_dynamic.py
# Current version is here:
# https://gist.github.com/cpbotha/1b42a20c8f3eb9bb7cb8

# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
"""
    How to load a user interface dynamically with PySide2.
    .. moduleauthor::  Sebastian Wiesner  <lunaryorn@gmail.com>
"""
from PySide2 import QtCore, QtUiTools


class UiLoader(QtUiTools.QUiLoader):
    def __init__(self, baseinstance, customWidgets=None):
        super().__init__(baseinstance)
        self.baseinstance = baseinstance
        self.customWidgets = customWidgets

    def createWidget(self, class_name, parent=None, name=""):
        if parent is None and self.baseinstance:
            return self.baseinstance
        else:
            if class_name in self.availableWidgets():
                widget = QtUiTools.QUiLoader.createWidget(
                    self, class_name, parent, name)
            else:
                try:
                    widget = self.customWidgets[class_name](parent)

                except (TypeError, KeyError):
                    raise Exception("No custom widget " + class_name +
                                    " in customWidgets param of UiLoader init")

            if self.baseinstance:
                setattr(self.baseinstance, name, widget)
            return widget


def load_ui(uifile, baseinstance=None, customWidgets=None,
            workingDirectory=None):
    loader = UiLoader(baseinstance, customWidgets)

    if workingDirectory is not None:
        loader.setWorkingDirectory(workingDirectory)

    widget = loader.load(uifile)
    return widget
