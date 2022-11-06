#!/usr/bin/env python
# encoding: UTF-8

"""
This file is part of Commix Project (https://commixproject.com).
Copyright (c) 2014-2021 Anastasios Stasinopoulos (@ancst).

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

For more see the file 'readme/COPYING' for copying permission.
"""

import re
import sys
import random
import string

from src.utils import settings

"""
About: Adds uninitialized bash variables between the characters of each command of the generated payloads.
Notes: This tamper script works against *nix targets.
Reference: https://www.secjuice.com/web-application-firewall-waf-evasion/
"""

__tamper__ = "uninitializedvariable"

if not settings.TAMPER_SCRIPTS[__tamper__]:
  settings.TAMPER_SCRIPTS[__tamper__] = True

def tamper(payload):
  def add_uninitialized_variable(payload):
    settings.TAMPER_SCRIPTS[__tamper__] = True
    rep = {
            "${uv}I${uv}F${uv}S": "IFS",
            "${uv}i${uv}f": "if", 
            "${uv}t${uv}h${uv}e${uv}n": "then",
            "${uv}e${uv}l${uv}s${uv}e": "else",
            "${uv}f${uv}i": "fi",
            "${uv}s${uv}t${uv}r": "str",
            "${uv}c${uv}m${uv}d": "cmd",
            "${uv}c${uv}ha${uv}r": "char"
          }
    payload = re.sub(r'([b-zD-Z])', r"${uv}\1", payload)
    rep = dict((re.escape(k), v) for k, v in rep.items())
    pattern = re.compile("|".join(rep.keys()))
    payload = pattern.sub(lambda m: rep[re.escape(m.group(0))], payload)
    return payload

  if settings.TARGET_OS != "win":
    if settings.EVAL_BASED_STATE != False:
      if settings.TRANFROM_PAYLOAD == None:
        settings.TRANFROM_PAYLOAD = False
        warn_msg = "The dynamic code evaluation technique, does not support the '"+ __tamper__  +".py' tamper script."
        sys.stdout.write("\r" + settings.print_warning_msg(warn_msg))
        sys.stdout.flush() 
        print
    else:
      settings.TRANFROM_PAYLOAD = True
      if settings.TRANFROM_PAYLOAD:
        payload = add_uninitialized_variable(payload)

  else:
    if settings.TRANFROM_PAYLOAD == None:
      settings.TRANFROM_PAYLOAD = False
      warn_msg = "Windows target host(s), does not support the '"+ __tamper__  +".py' tamper script."
      sys.stdout.write("\r" + settings.print_warning_msg(warn_msg))
      sys.stdout.flush() 
      print

  return payload
  