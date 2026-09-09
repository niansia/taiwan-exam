"""Fail-closed input checks for local, self-contained exam rendering.

This is defense in depth, not an operating-system sandbox or antivirus verdict.
Only installed measurement code may run; input documents are static data.
"""
from __future__ import annotations

import base64
import hashlib
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from bs4 import BeautifulSoup, Doctype

MAX_DOCUMENT_BYTES = 20_000_000
SVG_TAGS = set('svg g defs title desc path rect line polyline polygon circle ellipse text tspan textPath marker clipPath mask linearGradient radialGradient stop pattern use'.lower().split())


def check_css(value: str) -> None:
    # Exact fragment references are needed for SVG arrowheads and clip paths.
    remainder = re.sub(r'url\(\s*[\"\']?#[A-Za-z_][\w:.-]*[\"\']?\s*\)', '', value, flags=re.I)
    if '\\' in remainder or re.search(r'url\s*\(|@import|image-set\s*\(|expression\s*\(|-moz-binding', remainder, re.I):
        raise ValueError('External/dynamic CSS resources are not allowed in exam rendering')


def validate_svg(source: str) -> str:
    if len(source.encode('utf-8')) > MAX_DOCUMENT_BYTES:
        raise ValueError('SVG exceeds the rendering size limit')
    if re.search(r'<!DOCTYPE|<!ENTITY|<\?', source, re.I):
        raise ValueError('SVG declarations/entities/processing instructions are not allowed')
    try:
        root = ET.fromstring(source)
    except ET.ParseError as exc:
        raise ValueError('Malformed SVG: ' + str(exc)) from exc
    if root.tag not in ('svg', '{http://www.w3.org/2000/svg}svg'):
        raise ValueError('Expected an SVG document')
    for node in root.iter():
        tag = node.tag
        if tag.startswith('{'):
            namespace, tag = tag[1:].split('}', 1)
            if namespace != 'http://www.w3.org/2000/svg':
                raise ValueError('Foreign SVG namespaces are not allowed')
        if tag.lower() not in SVG_TAGS:
            raise ValueError('Unsupported or active SVG element: ' + tag)
        for key, value in node.attrib.items():
            name = key.rsplit('}', 1)[-1].lower()
            if name.startswith('on') or name in ('base', 'src'):
                raise ValueError('Active SVG attributes are not allowed')
            if name == 'href' and not re.fullmatch(r'#[A-Za-z_][\w:.-]*', value):
                raise ValueError('SVG references must remain within the same figure')
            check_css(value)
    return source


def validate_image(data: bytes, mime: str) -> None:
    if len(data) > MAX_DOCUMENT_BYTES:
        raise ValueError('Image exceeds the rendering size limit')
    if mime == 'image/svg+xml':
        validate_svg(data.decode('utf-8-sig'))
        return
    signatures = {
        'image/png': data.startswith(b'\x89PNG\r\n\x1a\n'),
        'image/jpeg': data.startswith(b'\xff\xd8\xff'),
        'image/gif': data.startswith((b'GIF87a', b'GIF89a')),
        'image/webp': data.startswith(b'RIFF') and data[8:12] == b'WEBP',
    }
    if not signatures.get(mime, False):
        raise ValueError('Image bytes do not match the declared image format')


def prepare_html(source: str, *, measurement_script: str = '') -> str:
    """Check static input and allow exactly the caller's installed probe script."""
    if len(source.encode('utf-8')) > MAX_DOCUMENT_BYTES:
        raise ValueError('HTML exceeds the rendering size limit')
    soup = BeautifulSoup(source, 'html.parser')
    for tag in soup.find_all(True):
        if tag.name in {'script', 'iframe', 'frame', 'frameset', 'object', 'embed', 'base', 'form', 'input', 'button', 'textarea', 'select', 'foreignobject', 'animate', 'set', 'audio', 'video', 'source'}:
            raise ValueError('Active HTML element is not allowed: ' + tag.name)
        if tag.name == 'meta' and tag.get('http-equiv'):
            raise ValueError('Input HTTP-equivalent metadata is not allowed')
        for key, raw in tag.attrs.items():
            value = ' '.join(raw) if isinstance(raw, list) else str(raw or '')
            if key.lower().startswith('on') or key.lower() in {'srcdoc', 'srcset', 'action', 'formaction', 'ping', 'background', 'poster'}:
                raise ValueError('Active HTML attribute is not allowed: ' + key)
            if key in ('src', 'href', 'xlink:href'):
                if value.startswith('#'):
                    continue
                if tag.name == 'link' and value == 'data:,' and tag.get('rel') == ['icon']:
                    continue
                match = re.fullmatch(r'data:(image/(?:png|jpeg|gif|webp|svg\+xml));base64,([A-Za-z0-9+/=\s]+)', value)
                if tag.name != 'img' or key != 'src' or not match:
                    raise ValueError('Exam HTML may only load embedded image data')
                validate_image(base64.b64decode(match[2], validate=True), match[1])
            if key == 'style':
                check_css(value)
        if tag.name == 'style':
            check_css(tag.get_text())
    for svg in soup.find_all('svg'):
        validate_svg(str(svg))
    if soup.html is None:
        wrapper = BeautifulSoup('<html lang="zh-Hant"><head></head><body></body></html>', 'html.parser')
        for node in list(soup.contents):
            if not isinstance(node, Doctype):
                wrapper.body.append(node.extract())
        soup = wrapper
    elif any(str(node).strip() for node in soup.contents if node is not soup.html and not isinstance(node, Doctype)):
        raise ValueError('HTML content outside the document root is not supported')
    if soup.html.head is None:
        soup.html.insert(0, soup.new_tag('head'))
    script_policy = "'none'"
    if measurement_script:
        if '</script' in measurement_script.lower():
            raise ValueError('Measurement script must be a script body, not markup')
        digest = base64.b64encode(hashlib.sha256(measurement_script.encode('utf-8')).digest()).decode('ascii')
        script_policy = "'sha256-" + digest + "'"
        script = soup.new_tag('script')
        script.string = measurement_script
        (soup.body or soup.html).append(script)
    policy = soup.new_tag('meta')
    policy['http-equiv'] = 'Content-Security-Policy'
    policy['content'] = ("default-src 'none'; img-src data:; style-src 'unsafe-inline'; "
                         "script-src " + script_policy + "; base-uri 'none'; form-action 'none'; object-src 'none'")
    soup.html.head.insert(0, policy)
    return str(soup)


def browser_flags(temporary: Path) -> list[str]:
    """Use a dedicated fresh profile; never disable Chromium's sandbox."""
    profile = temporary / 'browser-profile'
    profile.mkdir(exist_ok=False)
    return ['--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
            '--disable-extensions', '--disable-background-networking',
            '--disable-sync', '--no-proxy-server', f'--user-data-dir={profile}']
