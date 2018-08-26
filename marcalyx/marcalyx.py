import re


class MarcNamespacedElement:
    SLIM = {'marc': 'http://www.loc.gov/MARC21/slim'}
    def get_namespace(self, node):
        ns_search = re.search('({(.+)})?.+', node.tag)
        if ns_search[2] == 'http://www.loc.gov/MARC21/slim':
            return ns_search[2]

        if ns_search[2] is None:
            return None

        raise UnrecognizedNamespaceError(ns_search[2])

    def find_with_ns(self, node, tag, ns):
        if ns:
            ns_str = 'marc:'
        else:
            ns_str = ''
        return node.findall("%s%s" % (ns_str, tag,), self.SLIM)
            

class Record(MarcNamespacedElement):
    def __init__(self, node):
        self.node = node

        ns = self.get_namespace(node)
        
        self.leader = self.get_leader(node, ns)
        self.fields = [ControlField(f) for f in self.find_control(node, ns)] + \
                       [DataField(f, ns) for f in self.find_data(node, ns)]



    def find_control(self, node, ns):
        return self.find_with_ns(node, 'controlfield', ns)


    def find_data(self, node, ns):
        return self.find_with_ns(node, 'datafield', ns)


    def get_leader(self, node, ns):
        leader = self.find_with_ns(node, 'leader', ns)
        return leader[0].text


    def mainEntry(self):
        return next(iter(self.tag_range("100", "1XX") or []), None)
    
    def titleStatement(self):
        return self.field('245')[0]

    
    def field(self, tag):
        return [f for f in self.fields if f.tag == tag]


    def subfield(self, tag, code):
        return [g for h in
                [f.subfield(code) for f in self.field(tag)]
                for g in h]

    
    def tag_range(self, first, last):
        return [f for f in self.fields if f.tag >= first and f.tag <= last]


    def __getitem__(self, tag):
        return self.field(tag)

    
class ControlField:
    def __init__(self, node):
        self.node = node
        self.tag = node.attrib['tag']
        self.value = node.text


    def __repr__(self):
        return "%s   %s" % (self.tag, self.value,)


class DataField(MarcNamespacedElement):
    def __init__(self, node, ns):
        self.node = node
        self.tag = node.attrib['tag']
        self.ind1 = node.attrib['ind1']
        self.ind2 = node.attrib['ind2']
        self.subfields = [SubField(s) for s in
                          self.find_with_ns(node, 'subfield', ns)]


    def subfield(self, code):
        return [s for s in self.subfields if s.code == code]
        
    def value(self):
        return ' '.join([s.value for s in self.subfields])

    
    def ind_to_s(self, i):
        if i == ' ':
            return '#'

        return i
    
    def __repr__(self):
        return "%s %s%s%s" % (self.tag,
                              self.ind_to_s(self.ind1),
                              self.ind_to_s(self.ind2),
                              ''.join([str(s) for s in self.subfields]),)


class SubField:
    def __init__(self, node):
        self.code = node.attrib['code']
        self.value = node.text

    def __repr__(self):
        return "$%s%s" % (self.code, self.value,)


class UnrecognizedNamespaceError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)    
