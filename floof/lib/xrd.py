"""
Taken from: https://github.com/jcarbaugh/python-xrd

LICENSE:

Copyright (c) 2009, Jeremy Carbaugh

All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer in the documentation
      and/or other materials provided with the distribution.
    * Neither the name of Jeremy Carbaugh nor the names of its contributors may be
      used to endorse or promote products derived from this software without
      specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

from xml.dom.minidom import getDOMImplementation, parseString, Node
import datetime
import iso8601

try:
    import json
except ImportError:
    import simplejson as json

__author__ = "Jeremy Carbaugh (jcarbaugh@gmail.com)"
__version__ = "0.1"
__copyright__ = "Copyright (c) 2009 Jeremy Carbaugh"
__license__ = "BSD"

XRD_NAMESPACE = "http://docs.oasis-open.org/ns/xri/xrd-1.0"

def _get_text(root):
    text = ''
    for node in root.childNodes:
        if node.nodeType == Node.TEXT_NODE and node.nodeValue:
            text += node.nodeValue
        else:
            text += _get_text(node)
    return text.strip() or None

def _clean_dict(d):
    for key in d.keys():
        if not d[key]:
            del d[key]

# json parser/renderer

def _parse_json(content):

    def expires_handler(key, val, obj):
        obj.expires = iso8601.parse_date(val)

    def subject_handler(key, val, obj):
        obj.subject = val

    def alias_handler(key, val, obj):
        for alias in val:
            obj.aliases.append(alias)

    def property_handler(key, val, obj):
        for prop in val:
            prop_type = prop.keys()[0]
            prop_value = prop.values()[0]
            obj.properties.append(Property(prop_type, prop_value))

    def title_handler(key, val, obj):
        for title in val:
            title_lang = title.keys()[0]
            if title_lang == 'default':
                title_lang = None
            title_value = title.values()[0]
            obj.titles.append(Title(title_value, title_lang))

    def link_handler(key, val, obj):
        for link in val:
            l = Link()
            l.rel = link.get('rel', None)
            l.type = link.get('type', None)
            l.href = link.get('href', None)
            l.template = link.get('template', None)
            if 'title' in link:
                title_handler('title', link['title'], l)
            if 'property' in link:
                property_handler('property', link['property'], l)
            obj.links.append(l)

    def namespace_handler(key, val, obj):
        for namespace in val:
            ns = namespace.keys()[0]
            ns_uri = namespace.values()[0]
            obj.attributes.append(Attribute("xmlns:%s" % ns, ns_uri))

    handlers = {
        'expires': expires_handler,
        'subject': subject_handler,
        'alias': alias_handler,
        'property': property_handler,
        'link': link_handler,
        'title': title_handler,
        'namespace': namespace_handler,
    }

    def unknown_handler(key, val, obj):
        if ':' in key:
            (ns, name) = key.split(':')
            key = "%s:%s" % (ns, name.capitalize())
        obj.elements.append(Element(key, val))

    doc = json.loads(content)

    xrd = XRD()
    xrd.attributes.append(Attribute("xmlns", XRD_NAMESPACE))

    for key, value in doc.iteritems():
        handler = handlers.get(key, unknown_handler)
        handler(key, value, xrd)

    return xrd

def _render_json(xrd):

    doc = {
        "alias": [],
        "link": [],
        "namespace": [],
        "property": [],
        "title": [],
    }

    list_keys = doc.keys()

    for attr in xrd.attributes:
        if attr.name.startswith("xmlns:"):
            ns = attr.name.split(":")[1]
            doc['namespace'].append({ ns: attr.value})

    if xrd.expires:
        doc['expires'] = xrd.expires.isoformat()

    if xrd.subject:
        doc['subject'] = xrd.subject

    for alias in xrd.aliases:
        doc['alias'].append(alias)

    for prop in xrd.properties:
        doc['property'].append({ prop.type: prop.value })

    for link in xrd.links:

        link_doc = {
            'title': [],
            'property': [],
        }

        if link.rel:
            link_doc['rel'] = link.rel

        if link.type:
            link_doc['type'] = link.type

        if link.href:
            link_doc['href'] = link.href

        if link.template:
            link_doc['template'] = link.template

        for prop in link.properties:
            link_doc['property'].append({ prop.type: prop.value })

        for title in link.titles:
            lang = title.xml_lang or "default"
            link_doc['title'].append({ lang: title.value })

        _clean_dict(link_doc)

        doc['link'].append(link_doc)

    for elem in xrd.elements:
        doc[elem.name.lower()] = elem.value

    _clean_dict(doc)

    return json.dumps(doc)

# xml parser/renderer

def _parse_xml(content):

    def expires_handler(node, obj):
        obj.expires = iso8601.parse_date(_get_text(node))

    def subject_handler(node, obj):
        obj.subject = _get_text(node)

    def alias_handler(node, obj):
        obj.aliases.append(_get_text(node))

    def property_handler(node, obj):
        obj.properties.append(Property(node.getAttribute('type'), _get_text(node)))

    def title_handler(node, obj):
        obj.titles.append(Title(_get_text(node), node.getAttribute('xml:lang')))

    def link_handler(node, obj):
        l = Link()
        l.rel = node.getAttribute('rel')
        l.type = node.getAttribute('type')
        l.href = node.getAttribute('href')
        l.template = node.getAttribute('template')
        obj.links.append(l)

    handlers = {
        'Expires': expires_handler,
        'Subject': subject_handler,
        'Alias': alias_handler,
        'Property': property_handler,
        'Link': link_handler,
        'Title': title_handler,
    }

    def unknown_handler(node, obj):
        obj.elements.append(Element(
            name=node.tagName,
            value=_get_text(node),
        ))

    def handle_node(node, obj):
        handler = handlers.get(node.nodeName, unknown_handler)
        if handler and node.nodeType == node.ELEMENT_NODE:
            handler(node, obj)

    doc = parseString(content)
    root = doc.documentElement

    xrd = XRD(root.getAttribute('xml:id'))

    for name, value in root.attributes.items():
        if name != 'xml:id':
            xrd.attributes.append((name, value))

    for node in root.childNodes:
        handle_node(node, xrd)
        if node.nodeName == 'Link':
            link = xrd.links[-1]
            for child in node.childNodes:
                handle_node(child, link)

    return xrd


def _render_xml(xrd):

    doc = getDOMImplementation().createDocument(XRD_NAMESPACE, "XRD", None)
    root = doc.documentElement
    root.setAttribute('xmlns', XRD_NAMESPACE)

    if xrd.xml_id:
        root.setAttribute('xml:id', xrd.xml_id)

    for attr in xrd.attributes:
        root.setAttribute(attr.name, attr.value)

    if xrd.expires:
        node = doc.createElement('Expires')
        node.appendChild(doc.createTextNode(xrd.expires.isoformat()))
        root.appendChild(node)

    if xrd.subject:
        node = doc.createElement('Subject')
        node.appendChild(doc.createTextNode(xrd.subject))
        root.appendChild(node)

    for alias in xrd.aliases:
        node = doc.createElement('Alias')
        node.appendChild(doc.createTextNode(alias))
        root.appendChild(node)

    for prop in xrd.properties:
        node = doc.createElement('Property')
        node.setAttribute('type', prop.type)
        if prop.value:
            node.appendChild(doc.createTextNode(unicode(prop.value)))
        else:
            node.setAttribute('xsi:nil', 'true')
        root.appendChild(node)

    for element in xrd.elements:
        node = doc.createElement(element.name)
        node.appendChild(doc.createTextNode(element.value))
        root.appendChild(node)

    for link in xrd.links:

        if link.href and link.template:
            raise ValueError('only one of href or template attributes may be specified')

        link_node = doc.createElement('Link')

        if link.rel:
            link_node.setAttribute('rel', link.rel)

        if link.type:
            link_node.setAttribute('type', link.type)

        if link.href:
            link_node.setAttribute('href', link.href)

        if link.template:
            link_node.setAttribute('template', link.template)

        for title in link.titles:
            node = doc.createElement('Title')
            node.appendChild(doc.createTextNode(unicode(title)))
            if title.xml_lang:
                node.setAttribute('xml:lang', title.xml_lang)
            link_node.appendChild(node)

        for prop in link.properties:
            node = doc.createElement('Property')
            node.setAttribute('type', prop.type)
            if prop.value:
                node.appendChild(doc.createTextNode(unicode(prop.value)))
            else:
                node.setAttribute('xsi:nil', 'true')
            link_node.appendChild(node)

        root.appendChild(link_node)

    return doc

#
# special XRD types
#

class Attribute(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value
    def __str__(self):
        return u"%s=%s" % (self.name, self.value)

class Element(object):
    def __init__(self, name, value, attrs=None):
        self.name = name
        self.value = value
        self.attrs = attrs or { }

class Title(object):
    def __init__(self, value, xml_lang=None):
        self.value = value
        self.xml_lang = xml_lang
    def __eq__(self, value):
        return str(self) == value
    def __str__(self):
        if self.xml_lang:
            return u"%s:%s" % (self.xml_lang, self.value)
        return self.value

class Property(object):
    def __init__(self, type_, value=None):
        self.type = type_
        self.value = value
    def __eq__(self, value):
        return str(self) == value
    def __str__(self):
        if self.value:
            return u"%s:%s" % (self.type, self.value)
        return self.type

#
# special list types
#

class ListLikeObject(list):
    def __setitem__(self, key, value):
        value = self.item(value)
        super(ListLikeObject, self).__setitem__(key, value)
    def append(self, value):
        value = self.item(value)
        super(ListLikeObject, self).append(value)
    def extend(self, values):
        values = (self.item(value) for value in values)
        super(ListLikeObject, self).extend(values)

class AttributeList(ListLikeObject):
    def item(self, value):
        if isinstance(value, (list, tuple)):
            return Attribute(*value)
        elif not isinstance(value, Attribute):
            raise ValueError('value must be an instance of Attribute')
        return value

class ElementList(ListLikeObject):
    def item(self, value):
        if not isinstance(value, Element):
            raise ValueError('value must be an instance of Type')
        return value

class TypeList(ListLikeObject):
    def item(self, value):
        if isinstance(value, basestring):
            return Type(value)
        elif not isinstance(value, Type):
            raise ValueError('value must be an instance of Type')
        return value

class TitleList(ListLikeObject):
    def item(self, value):
        if isinstance(value, basestring):
            return Title(value)
        elif isinstance(value, (list, tuple)):
            return Title(*value)
        elif not isinstance(value, Title):
            raise ValueError('value must be an instance of Title')
        return value

class LinkList(ListLikeObject):
    def item(self, value):
        if not isinstance(value, Link):
            raise ValueError('value must be an instance of Link')
        return value

class PropertyList(ListLikeObject):
    def item(self, value):
        if isinstance(value, basestring):
            return Property(value)
        elif isinstance(value, (tuple, list)):
            return Property(*value)
        elif not isinstance(value, Property):
            raise ValueError('value must be an instance of Property')
        return value

#
# Link object
#

class Link(object):

    def __init__(self, rel=None, type_=None, href=None, template=None):
        self.rel = rel
        self.type = type_
        self.href = href
        self.template = template
        self._titles = TitleList()
        self._properties = []

    def get_titles(self):
        return self._titles
    titles = property(get_titles)

    def get_properties(self):
        return self._properties
    properties = property(get_properties)

#
# main XRD class
#

class XRD(object):

    def __init__(self, xml_id=None, subject=None):
        self.xml_id = xml_id
        self.subject = subject
        self._expires = None
        self._aliases = []
        self._properties = PropertyList()
        self._links = LinkList()
        self._signatures = []

        self._attributes = AttributeList()
        self._elements = ElementList()

    # ser/deser methods

    @classmethod
    def parse(cls, xrd): # deprecate this method!!!
        return _parse_xml(xrd)

    @classmethod
    def parse_jrd(cls, jrd):
        return _parse_json(jrd)

    @classmethod
    def parse_xrd(cls, xrd):
        return _parse_xml(xrd)

    def to_json(self):
        return _render_json(self)

    def to_xml(self):
        return _render_xml(self)

    # helper methods

    def find_link(self, rels, attr=None):
        if not isinstance(rels, (list, tuple)):
            rels = (rels,)
        for link in self.links:
            if link.rel in rels:
                if attr:
                    return getattr(link, attr, None)
                return link

    # custom elements and attributes

    def get_elements(self):
        return self._elements
    elements = property(get_elements)

    def get_attributes(self):
        return self._attributes
    attributes = property(get_attributes)

    # defined elements and attributes

    def get_expires(self):
        return self._expires
    def set_expires(self, expires):
        if not isinstance(expires, datetime.datetime):
            raise ValueError('expires must be a datetime object')
        self._expires = expires
    expires = property(get_expires, set_expires)

    def get_aliases(self):
        return self._aliases
    aliases = property(get_aliases)

    def get_properties(self):
        return self._properties
    properties = property(get_properties)

    def get_links(self):
        return self._links
    links = property(get_links)

    def get_signatures(self):
        return self._signatures
    signatures = property(get_links)

