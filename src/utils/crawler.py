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
import re
import sys
import socket
import tempfile
from src.utils import menu
from src.utils import settings
from src.utils import common
from src.core.injections.controller import checks
from src.core.requests import headers
from socket import error as SocketError
from src.core.requests import redirection
from src.thirdparty.six.moves import http_client as _http_client
from src.thirdparty.six.moves import input as _input
from src.thirdparty.six.moves import urllib as _urllib
from src.thirdparty.colorama import Fore, Back, Style, init
from src.thirdparty.beautifulsoup.beautifulsoup import BeautifulSoup


def init_global_vars():
  global crawled_hrefs
  crawled_hrefs = []
  global sitemap_loc
  sitemap_loc = []
  global visited_hrefs
  visited_hrefs = []
  global new_crawled_hrefs
  new_crawled_hrefs = []

"""
Change the crawling depth level.
"""
def set_crawling_depth():
  while True:
    message = "Do you want to change the crawling depth level (" + str(menu.options.crawldepth) + ")? [y/N] > "
    message = common.read_input(message, default="N", check_batch=True)
    if message in settings.CHOICE_YES or message in settings.CHOICE_NO:
      break  
    elif message in settings.CHOICE_QUIT:
      raise SystemExit()
    else:
      common.invalid_option(message)  
      pass
      
  # Change the crawling depth level.
  if message in settings.CHOICE_YES:
    while True:
      message = "Please enter the crawling depth level: > "
      message = common.read_input(message, default="1", check_batch=True)
      menu.options.crawldepth = message
      return


"""
Normalize crawling results.
"""
def normalize_results(output_href):
  results = []
  while True:
    message = "Do you want to normalize crawling results? [Y/n] > "
    message = common.read_input(message, default="Y", check_batch=True)
    if message in settings.CHOICE_YES:
      seen = set()
      for target in output_href:
        value = "%s%s%s" % (target, '&' if '?' in target else '?', target or "")
        match = re.search(r"/[^/?]*\?.+\Z", value)
        if match:
          key = re.sub(r"=[^=&]*", "=", match.group(0)).strip("&?")
          if '=' in key and key not in seen:
            results.append(target)
            seen.add(key)
      return results
    elif message in settings.CHOICE_NO:
      return output_href
    elif message in settings.CHOICE_QUIT:
      raise SystemExit()
    else:
      common.invalid_option(message)  
      print(settings.print_error_msg(err_msg))
      pass


"""
Store crawling results to a temporary file.
"""
def store_crawling(output_href):
  while True:
    message = "Do you want to store crawling results to a temporary file "
    message += "(for eventual further processing with other tools)? [y/N] > "
    message = common.read_input(message, default="N", check_batch=True)
    if message in settings.CHOICE_YES:
      filename = tempfile.mkstemp(suffix=".txt")[1]
      info_msg = "Writing crawling results to a temporary file '" + str(filename) + "'."
      print(settings.print_info_msg(info_msg))
      with open(filename, "a") as crawling_results:
        for url in output_href:
          crawling_results.write(url + "\n")
      return
    elif message in settings.CHOICE_NO:
      return
    elif message in settings.CHOICE_QUIT:
      raise SystemExit()
    else:
      common.invalid_option(message)  
      pass  


"""
Check for URLs in sitemap.xml.
"""
def sitemap(url):
  try:
    if not url.endswith(".xml"):
      if not url.endswith("/"):
        url = url + "/"
      url = _urllib.parse.urljoin(url, "sitemap.xml")
    response = request(url)
    content = checks.page_encoding(response, action="decode")
    for match in re.finditer(r"<loc>\s*([^<]+)", content or ""):
      url = match.group(1).strip()
      if url not in sitemap_loc:
        sitemap_loc.append(url)
      if url.endswith(".xml") and "sitemap" in url.lower():
        while True:
          warn_msg = "A sitemap recursion detected (" + url + ")."
          print(settings.print_warning_msg(warn_msg))
          message = "Do you want to follow? [Y/n] > "
          message = common.read_input(message, default="Y", check_batch=True)
          if message in settings.CHOICE_YES:
            sitemap(url)
            break
          elif message in settings.CHOICE_NO:
            break
          elif message in settings.CHOICE_QUIT:
            raise SystemExit()
          else:
            common.invalid_option(message)  
            pass
    no_usable_links(sitemap_loc)
    return sitemap_loc
  except:
    if not menu.options.crawldepth:
      raise SystemExit()
    pass


"""
Store the identified (valid) hrefs.
"""
def store_hrefs(href, identified_hrefs, redirection):
  set(crawled_hrefs)
  set(new_crawled_hrefs)
  if href not in crawled_hrefs:
    if (settings.DEFAULT_CRAWLING_DEPTH != 1 and href not in new_crawled_hrefs) or redirection:
      new_crawled_hrefs.append(href)
    identified_hrefs = True
    crawled_hrefs.append(href)
  return identified_hrefs


"""
Do a request to target URL.
"""
def request(url):
  try:
    # Check if defined POST data
    if menu.options.data:
      request = _urllib.request.Request(url, menu.options.data.encode(settings.DEFAULT_CODEC))
    else:
      request = _urllib.request.Request(url)
    headers.do_check(request)
    headers.check_http_traffic(request)
    response = _urllib.request.urlopen(request, timeout=settings.TIMEOUT)
    if not menu.options.ignore_redirects:
      href = redirection.do_check(request, url)
      if href != url:
        store_hrefs(href, identified_hrefs=True, redirection=True)
    return response
  except (SocketError, _urllib.error.HTTPError, _urllib.error.URLError, _http_client.BadStatusLine, _http_client.InvalidURL, Exception) as err_msg:
    if url not in settings.HREF_SKIPPED:
      settings.HREF_SKIPPED.append(url)
      settings.CRAWLED_SKIPPED_URLS_NUM += 1
      if settings.TOTAL_OF_REQUESTS != 1 and not settings.MULTI_TARGETS:
        if settings.CRAWLED_URLS_NUM != 0 and settings.CRAWLED_SKIPPED_URLS_NUM != 0:
          print(settings.SINGLE_WHITESPACE)
      checks.connection_exceptions(err_msg, url)
      if settings.VERBOSITY_LEVEL >= 2:
        print(settings.SINGLE_WHITESPACE)

"""
Enable crawler.
"""
def enable_crawler():
  message = ""
  if not settings.CRAWLING:
    while True:
      message = "Do you want to enable crawler? [y/N] > "
      message = common.read_input(message, default="N", check_batch=True)
      if message in settings.CHOICE_YES:
        menu.options.crawldepth = 1
        break  
      if message in settings.CHOICE_NO:
        break  
      elif message in settings.CHOICE_QUIT:
        raise SystemExit()
      else:
        common.invalid_option(message)  
        pass
    set_crawling_depth()

"""
Check for the existence of site's sitemap
"""
def check_sitemap():
  while True:
    message = "Do you want to check target"+ ('', 's')[settings.MULTI_TARGETS] + " for "
    message += "the existence of site's sitemap(.xml)? [y/N] > "
    message = common.read_input(message, default="N", check_batch=True)
    if message in settings.CHOICE_YES:
      settings.SITEMAP_CHECK = True
      return
    elif message in settings.CHOICE_NO:
      settings.SITEMAP_CHECK = False
      return
    elif message in settings.CHOICE_QUIT:
      raise SystemExit()
    else:
      common.invalid_option(message)  
      pass

"""
Check if no usable links found.
"""
def no_usable_links(crawled_hrefs):
  if len(crawled_hrefs) == 0:
    warn_msg = "No usable links found (with GET parameters)."
    print(settings.print_warning_msg(warn_msg))
    if not settings.MULTI_TARGETS:
      raise SystemExit()

"""
The crawing process.
"""
def do_process(url):
  identified_hrefs = False
  if settings.VERBOSITY_LEVEL >= 2:
    print(settings.SINGLE_WHITESPACE)
  else:
    if settings.CRAWLED_SKIPPED_URLS_NUM == 0 or settings.CRAWLED_URLS_NUM != 0:
      sys.stdout.write("\r")
  # Grab the crawled hrefs.
  try:
    response = request(url)
    content = checks.page_encoding(response, action="decode")
    match = re.search(r"(?si)<html[^>]*>(.+)</html>", content)
    if match:
      content = "<html>%s</html>" % match.group(1)
    soup = BeautifulSoup(content)
    tags = soup('a')
    if not tags:
      tags = []
      tags += re.finditer(r'(?i)\s(href|src)=["\'](?P<href>[^>"\']+)', content)
      tags += re.finditer(r'(?i)window\.open\(["\'](?P<href>[^)"\']+)["\']', content)
    for tag in tags:
      href = tag.get("href") if hasattr(tag, settings.HTTPMETHOD.GET) else tag.group("href")
      if href:
        href = _urllib.parse.urljoin(url, _urllib.parse.unquote(href))
        if  _urllib.parse.urlparse(url).netloc in href:
          if (common.extract_regex_result(r"\A[^?]+\.(?P<result>\w+)(\?|\Z)", href) or "") not in settings.CRAWL_EXCLUDE_EXTENSIONS:
            if not re.search(r"\?(v=)?\d+\Z", href) and \
            not re.search(r"(?i)\.(js|css)(\?|\Z)", href):
              identified_hrefs = store_hrefs(href, identified_hrefs, redirection=False)

    no_usable_links(crawled_hrefs)
    if identified_hrefs:
      if len(new_crawled_hrefs) != 0 and settings.DEFAULT_CRAWLING_DEPTH != 1:
        return list(set(new_crawled_hrefs))
      return list(set(crawled_hrefs))
    return list("")

  except Exception as e:  # for non-HTML files and non-valid links
    pass


"""
The main crawler.
"""
def crawler(url, url_num, crawling_list):
  init_global_vars()
  if crawling_list > 1:
    _ = " (" + str(url_num) + "/" + str(crawling_list) + ")"
  else:
    _ = ""
  info_msg = "Starting crawler for target URL '" + url + "'" + _
  print(settings.print_info_msg(info_msg))
  response = request(url)
  if settings.SITEMAP_CHECK:
    enable_crawler()
  if settings.SITEMAP_CHECK is None:
    check_sitemap()
  if settings.SITEMAP_CHECK:
    output_href = sitemap(url)
  if not settings.SITEMAP_CHECK or (settings.SITEMAP_CHECK and output_href is None):
    output_href = do_process(url)
    if settings.MULTI_TARGETS and settings.DEFAULT_CRAWLING_DEPTH != 1:
      settings.DEFAULT_CRAWLING_DEPTH = 1
    while settings.DEFAULT_CRAWLING_DEPTH <= int(menu.options.crawldepth):
      info_msg = "Searching for usable "
      info_msg += "links with depth " + str(settings.DEFAULT_CRAWLING_DEPTH) + "." 
      print(settings.print_info_msg(info_msg))
      if settings.DEFAULT_CRAWLING_DEPTH == 2:
        output_href = new_crawled_hrefs
      elif settings.DEFAULT_CRAWLING_DEPTH > 2:
        output_href = new_crawled_hrefs + crawled_hrefs
      try:
        [output_href.remove(x) for x in visited_hrefs if x in output_href]
      except TypeError: 
        pass
      link = 0
      if output_href is not None:
        for url in output_href: 
          if url not in visited_hrefs:
            link += 1
            settings.CRAWLED_URLS_NUM = link
            visited_hrefs.append(url)
            do_process(url)
            info_msg = str(link)
            info_msg += "/" + str(len(output_href)) + " links visited." 
            sys.stdout.write("\r" + settings.print_info_msg(info_msg))
            sys.stdout.flush()
          if settings.VERBOSITY_LEVEL > 1:
            print(settings.SINGLE_WHITESPACE)
      if link != 0:
        print(settings.SINGLE_WHITESPACE)
      settings.DEFAULT_CRAWLING_DEPTH += 1

  output_href = crawled_hrefs
  no_usable_links(output_href)
  return output_href

# eof