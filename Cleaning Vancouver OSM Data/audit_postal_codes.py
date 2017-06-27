#!/usr/bin/env python
# -*- coding: utf-8 -*-

# script for auditing and formatting postal codes in an OSM file
import re

nonalpha_re = re.compile('\W')

# returns the set of postal codes used in an osm file
def audit_postal_code(osmfile):
    osm_file = open(osmfile, "r")
    postal_codes = set()
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if tag.attrib['k'] == "addr:postcode":
                    postal_codes.add(tag.attrib['v'])

    osm_file.close()
    return postal_codes

# takes a postal code and returns it in the proper format or returns None if given an invalid postal code
def format_postal_code(code):
    # strip any BC prefix
    if code[0:2].upper() == 'BC':
        code = code[2:]
    # strip all non alphanumeric characters
    code = re.sub(nonalpha_re, "", code)
    # insert a space to the middle of the code
    code = code[0:3] + ' ' + code[3:]
    return code.upper()[0:7] if len(code) > 6 else None