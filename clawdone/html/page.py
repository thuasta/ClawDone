"""Compose the embedded mobile UI page."""

from .body import INDEX_BODY
from .script import INDEX_SCRIPT
from .styles import INDEX_CSS

INDEX_HTML = '<!doctype html>\n<html lang="en">\n<head>\n  <meta charset="utf-8">\n  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n  <title>ClawDone</title>\n  ' + "<style>" + INDEX_CSS + "</style>" + INDEX_BODY + "<script>" + INDEX_SCRIPT + "</script></html>"
