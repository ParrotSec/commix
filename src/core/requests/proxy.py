#!/usr/bin/env python
# encoding: UTF-8

"""
This file is part of Commix Project (https://commixproject.com).
Copyright (c) 2014-2022 Anastasios Stasinopoulos (@ancst).

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
 
For more see the file 'readme/COPYING' for copying permission.
"""

import sys
import socket
from src.utils import menu
from src.utils import settings
from src.core.requests import headers
from src.thirdparty.six.moves import urllib as _urllib
from src.thirdparty.colorama import Fore, Back, Style, init
from src.thirdparty.six.moves import http_client as _http_client

"""
 Check if HTTP Proxy is defined.
"""
def do_check(url):
  if settings.VERBOSITY_LEVEL != 0:
    info_msg = "Setting the HTTP proxy for all HTTP requests. "
    print(settings.print_info_msg(info_msg))
  if menu.options.data:
    request = _urllib.request.Request(url, menu.options.data.encode(settings.DEFAULT_CODEC))
  else:
     request = _urllib.request.Request(url)
  headers.do_check(request)
  request.set_proxy(menu.options.proxy, settings.PROXY_SCHEME)
  try:
    response = _urllib.request.urlopen(request, timeout=settings.TIMEOUT)
    return response
  except (_urllib.error.URLError, _urllib.error.HTTPError, _http_client.BadStatusLine) as err:
    err_msg = "Unable to connect to the target URL or proxy."
    print(settings.print_critical_msg(err_msg))
    raise SystemExit()
  except socket.timeout:
    err_msg = "The connection to target URL or proxy has timed out."
    print(settings.print_critical_msg(err_msg) + "\n")
    raise SystemExit()

"""
Use the defined HTTP Proxy
"""
def use_proxy(request):
  _ = True
  headers.do_check(request)
  request.set_proxy(menu.options.proxy, settings.PROXY_SCHEME)
  try:
    response = _urllib.request.urlopen(request, timeout=settings.TIMEOUT)
    return response
  except _urllib.error.HTTPError as err:
    if str(err.code) == settings.INTERNAL_SERVER_ERROR or str(err.code) == settings.BAD_REQUEST:
      return False 
    else:
      _ = False
  except (_urllib.error.URLError, _http_client.BadStatusLine) as err:
     _ = False
  if not _:
    err_msg = "Unable to connect to the target URL or proxy."
    print(settings.print_critical_msg(err_msg))
    raise SystemExit()


# eof 