#!/usr/bin/python2.4
# Copyright (c) 2006-2008 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

'''Fast and efficient parser for XTB files.
'''


import xml.sax
import xml.sax.handler


class XtbContentHandler(xml.sax.handler.ContentHandler):
  '''A content handler that calls a given callback function for each
  translation in the XTB file.
  '''
  
  def __init__(self, callback, debug=False):
    self.callback = callback
    self.debug = debug
    # 0 if we are not currently parsing a translation, otherwise the message
    # ID of that translation.
    self.current_id = 0
    # Empty if we are not currently parsing a translation, otherwise the
    # parts we have for that translation - a list of tuples
    # (is_placeholder, text)
    self.current_structure = []
    # Set to the language ID when we see the <translationbundle> node.
    self.language = ''
  
  def startElement(self, name, attrs):
    if name == 'translation':
      assert self.current_id == 0 and len(self.current_structure) == 0, (
              "Didn't expect a <translation> element here.")
      self.current_id = attrs.getValue('id')
    elif name == 'ph':
      assert self.current_id != 0, "Didn't expect a <ph> element here."
      self.current_structure.append((True, attrs.getValue('name')))
    elif name == 'translationbundle':
      self.language = attrs.getValue('lang')

  def endElement(self, name):
    if name == 'translation':
      assert self.current_id != 0
      self.callback(self.current_id, self.current_structure)
      self.current_id = 0
      self.current_structure = []

  def characters(self, content):
    if self.current_id != 0:
      # We are inside a <translation> node so just add the characters to our
      # structure.
      #
      # This naive way of handling characters is OK because in the XTB format,
      # <ph> nodes are always empty (always <ph name="XXX"/>) and whitespace
      # inside the <translation> node should be preserved.
      self.current_structure.append((False, content))


class XtbErrorHandler(xml.sax.handler.ErrorHandler):
  def error(self, exception):
    pass
  
  def fatalError(self, exception):
    raise exception
  
  def warning(self, exception):
    pass


def Parse(xtb_file, callback_function, debug=False):
  '''Parse xtb_file, making a call to callback_function for every translation
  in the XTB file.
  
  The callback function must have the signature as described below.  The 'parts'
  parameter is a list of tuples (is_placeholder, text).  The 'text' part is
  either the raw text (if is_placeholder is False) or the name of the placeholder
  (if is_placeholder is True).
  
  Args:
    xtb_file:           file('fr.xtb')
    callback_function:  def Callback(msg_id, parts): pass
  
  Return:
    The language of the XTB, e.g. 'fr'
  '''
  # Start by advancing the file pointer past the DOCTYPE thing, as the TC
  # uses a path to the DTD that only works in Unix.
  # TODO(joi) Remove this ugly hack by getting the TC gang to change the
  # XTB files somehow?
  front_of_file = xtb_file.read(1024)
  xtb_file.seek(front_of_file.find('<translationbundle'))
  
  handler = XtbContentHandler(callback=callback_function, debug=debug)
  xml.sax.parse(xtb_file, handler)
  assert handler.language != ''
  return handler.language

