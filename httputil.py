#!/usr/bin/env python3

import urllib.request

class HTTPErrorProcessorWith300(urllib.request.HTTPErrorProcessor):
    """Process HTTP error responses."""
    handler_order = 1000  # after all other processing

    def http_response(self, request, response):
        if response.code >= 300 and response.code < 400:
            return response
        
        return super().http_response(request, response)

    https_response = http_response

class HTTPSOnlyOpener(urllib.request.OpenerDirector):
    def __init__(self, /, follow_redirects: bool = True):
        super().__init__()

        self.add_handler(urllib.request.UnknownHandler())
        self.add_handler(urllib.request.HTTPDefaultErrorHandler())
        if follow_redirects:
            self.add_handler(urllib.request.HTTPRedirectHandler())
        self.add_handler(urllib.request.HTTPSHandler())
        self.add_handler(HTTPErrorProcessorWith300())

_OPENER_DEFAULT = HTTPSOnlyOpener()
_OPENER_NO_REDIRECTS = HTTPSOnlyOpener(follow_redirects=False)

def http_make_req(url: str, /, headers: dict[str, str] = {}, follow_redirects: bool = True):
    opener = _OPENER_DEFAULT if follow_redirects else _OPENER_NO_REDIRECTS
    return opener.open(urllib.request.Request(
        url,
        headers={"User-Agent": "httputil.py (github.com/Doridian/factorio-docker)"} | headers,
    ))

def http_get_bytes(url: str, /, headers: dict[str, str] = {}, follow_redirects: bool = True) -> bytes:
    with http_make_req(url, headers=headers, follow_redirects=follow_redirects) as resp:
        return resp.read()

def http_get_str(url: str, /, headers: dict[str, str] = {}, follow_redirects: bool = True) -> str:
    with http_make_req(url, headers=headers, follow_redirects=follow_redirects) as resp:
        charset = resp.headers.get_content_charset("utf-8")
        return resp.read().decode(charset)
