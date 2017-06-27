#!/usr/bin/env python
# -*- coding: utf-8 -*-

# script for auditing and replacing street types in an OSM file
import re

# list of valid street types
expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons", "Kingsway", "Way", "Highway", "Broadway", "Crescent", "Alley"]

# mapping from incorrectly formatted street types to the correct format
map_street_types = {'St.' : 'Street',
                    'street' : 'Street',
                    'Rd.' : 'Road',
                    'St' : 'Street',
                    'steet' : 'Street',
                    'E' : 'East',
                    'N' : 'North',
                    'W' : 'West',
                    'S' : 'South',
                    'Blvd' : 'Boulevard',
                    'Ave' : 'Avenue',
                    'Vancouver': ''}

# regex to match the address type of a given address string
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

# adds the street name to a dictionary of street_type:street_names if the street_name is not an expected street_type
def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)

# determines whether a given element is a street address tag            
def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")

# parses an osmfile to find street address tags that do not have an expected street type. returns these tags
# in a dictionary mapping the incorrectly formatted street type to the set of all street names using this street type	
def audit(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    osm_file.close()
    return street_types

# takes a street name and returns it with the street type correctly formatted
def update_name(name):
    m = street_type_re.search(name)
    if m:
        street_type = m.group()
        if street_type not in expected and street_type in map_street_types:
            name = re.sub(street_type, map_street_types[street_type], name)
            name = update_name(name)
    return name
