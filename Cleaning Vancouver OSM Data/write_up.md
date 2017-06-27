
# Cleaning OpenStreetMap Data for the Vancouver Area

### The Dataset

[Mapzen](https://mapzen.com/) hosts premade extracts of street map data for a large number of metropolitan areas that are available for download in a variety of formats. The [dataset](https://mapzen.com/data/metro-extracts/metro/vancouver_canada/) I am working with is an OpenStreetMap XML extract of downtown Vancouver BC and the surrounding area. I chose this dataset to work with because Vancouver is the most densely populated urban area near where I live and its OSM extract contains a large amount of data for a very small geographic region.

### Cleaning the Data
#### Dealing with Missing User Data
The first problem I encountered with preparing the data for insertion into an SQL database were nodes with missing 'user' and 'uid' attributes:

```xml
<node changeset="96018" id="30353302" lat="49.306653" lon="-123.1351983"
timestamp="2007-06-14T16:54:46Z" version="1">
```
This is required information for the table schema so I decided to deal with this by assigning all nodes with missing user information a 'user' attribute of 'MISSING_USER' and a 'uid' of -1



```python
# from shape_element in process_osm.py
if 'user' not in element.attrib:
    element.attrib['user'] = 'MISSING_USER'
if 'uid' not in element.attrib:
    element.attrib['uid'] = -1
```

#### Cleaning Street Types

There were two primary issues encountered with the street address data:

* Inconsistent capitalization, abbreviation and misspelling of street types (e.g. 'St.', 'street', 'steet' all used in place of 'Street')
* The city name 'Vancouver' added to the end of the address

To deal with this I used regular expressions to substitute any incorrect street type formats to the correct format using a dictionary to map the values. The function is recursive because some fields had multiple errors (e.g. 'Main St. Vancouver' needs to have Vancouver removed and St. changed to Street to become 'Main Street').


```python
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

street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

def update_name(name):
    m = street_type_re.search(name)
    if m:
        street_type = m.group()
        if street_type not in expected and street_type in map_street_types:
            name = re.sub(street_type, map_street_types[street_type], name)
            name = update_name(name)
    return name
```

** Cleaning Postal Codes **

As with the street address data, postal codes had a number of consistency and validity issues:

* Codes prefixed with the province code of BC
* Inconsistent use of whitespace and capitalization
* The same code entered multiple times in different formats (e.g. 'v5k 1z2; V5K1Z2')
* Obviously invalid codes with fewer than 6 alphanumeric characters

To deal with these issues a function was written to take postal codes and return them in a consistent format (e.g. V5K 1Z8).
Invalid postal codes were returned as None and not added to the database.


```python
nonalpha_re = re.compile('\W')

def format_postal_code(code):
    # strip any BC prefix
    if code[0:2].upper() == 'BC':
        code = code[2:]
    # strip all non alphanumeric characters
    code = re.sub(nonalpha_re, "", code)
    # insert a space to the middle of the code
    code = code[0:3] + ' ' + code[3:]
    return code.upper()[0:7] if len(code) > 6 else None

```

### Querying the Data

Now that the data is cleaned and loaded into an SQL database it is straightforward to begin querying and exploring the data.

#### File Sizes
```
vancouver_canada.osm: 180,094KB
vancouver.sqlite:     100,835KB
nodes.csv:             69,738KB
nodes_tags.csv:         1,463KB
ways.csv:               9,781KB
ways_nodes.csv:        24,447KB
ways_tags.csv:          7,961KB
```

#### Number of Unique Nodes


```python
%%sql
SELECT COUNT(*) FROM nodes;

```

    Done.
    




<table>
    <tr>
        <th>COUNT(*)</th>
    </tr>
    <tr>
        <td>810187</td>
    </tr>
</table>



#### Number of Unique Ways


```python
%%sql
SELECT COUNT(*) FROM ways;
```

    Done.
    




<table>
    <tr>
        <th>COUNT(*)</th>
    </tr>
    <tr>
        <td>156709</td>
    </tr>
</table>



#### Number of Unique Users


```python
%%sql
SELECT COUNT(DISTINCT(e.uid))          
FROM (SELECT uid FROM nodes UNION ALL SELECT uid FROM ways) e;
```

    Done.
    




<table>
    <tr>
        <th>uid))</th>
    </tr>
    <tr>
        <td>873</td>
    </tr>
</table>



#### Number of Restaurants



```python
%%sql
SELECT COUNT(*) FROM nodes_tags WHERE value = 'restaurant'
```

    Done.
    




<table>
    <tr>
        <th>COUNT(*)</th>
    </tr>
    <tr>
        <td>727</td>
    </tr>
</table>



#### Top 10 Contributing Users


```python
%%sql
SELECT e.user, COUNT(*) as num
FROM (SELECT user FROM Nodes UNION ALL SELECT user FROM ways) e
GROUP BY e.user
ORDER BY num DESC
LIMIT 10;
```

    Done.
    




<table>
    <tr>
        <th>user</th>
        <th>num</th>
    </tr>
    <tr>
        <td>keithonearth</td>
        <td>338684</td>
    </tr>
    <tr>
        <td>michael_moovelmaps</td>
        <td>113131</td>
    </tr>
    <tr>
        <td>still-a-worm</td>
        <td>97103</td>
    </tr>
    <tr>
        <td>treeniti2</td>
        <td>74995</td>
    </tr>
    <tr>
        <td>pdunn</td>
        <td>41727</td>
    </tr>
    <tr>
        <td>muratc3</td>
        <td>37074</td>
    </tr>
    <tr>
        <td>WBSKI</td>
        <td>31363</td>
    </tr>
    <tr>
        <td>rbrtwhite</td>
        <td>22235</td>
    </tr>
    <tr>
        <td>Siegbaert</td>
        <td>21377</td>
    </tr>
    <tr>
        <td>pnorman</td>
        <td>19732</td>
    </tr>
</table>



### Additional Areas for Exploration

#### What Cryptocurrencies Are Accepted

The number of places that several different popular cryptocurrencies are accepted:


```python
%%sql
SELECT key, COUNT(*) as num
FROM nodes_tags
WHERE (key='bitcoin' or key='litecoin' or key='dogecoin' or 
       key = 'ethereum' or key = 'dash') and value = 'yes'
GROUP BY key
ORDER BY num DESC
```

    Done.
    




<table>
    <tr>
        <th>key</th>
        <th>num</th>
    </tr>
    <tr>
        <td>bitcoin</td>
        <td>50</td>
    </tr>
    <tr>
        <td>litecoin</td>
        <td>3</td>
    </tr>
    <tr>
        <td>dogecoin</td>
        <td>2</td>
    </tr>
</table>



There are a lot of cryptocurrencies out there so it would be nice to be able to see which ones are accepted without having to manually search for each cryptocurrency by name as above. One way to improve the functionality of the database in this respect would be to download a large list of cryptocurrency names, then see where these names appear as keys when processing the OSM file and tag the node with a new 'cryptocurrency' tag. One difficulty with implementing this is the large variety of ways a single currency can be referred to as. For instance, BTC, XBT and Bitcoin could all indicate a place accepts Bitcoin. To deal with this, any key containing cryptocurrency information would have to be audited and cleaned, similar to how address types and postal codes were.
