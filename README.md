
Guts
====
 
Lightweight declarative YAML and XML data binding for Python

Usage
-----

`playlist.py`:

```python
from guts import *

class Song(Object):
    name = String.T()
    album = String.T(default='')
    artist = String.T(default='')
    year = Int.T(optional=True)

class Playlist(Object):
    xmltagname = 'playlist'
    name = String.T(default='Untitled Playlist')
    comment = String.T(optional=True)
    song_list = List.T(Song.T())
```

These classes come with automatic `__init__`:

```pycon
>>> from playlist import *
>>> song1 = Song(name='Metropolis', artist='Kraftwerk')
>>> song2 = Song(name='I Robot', artist='The Alan Parsons Project', album='I Robot')
>>> playlist = Playlist(song_list=[song1,song2])
```

They serialize to YAML:

```pycon
>>> print song1.dump()
--- !playlist.Song
name: Metropolis
artist: Kraftwerk
```

They also serialize to XML:

```pycon
>>> print playlist.dump_xml()
<playlist>
  <name>Untitled Playlist</name>
  <song>
    <name>Metropolis</name>
    <artist>Kraftwerk</artist>
  </song>
  <song>
    <name>I Robot</name>
    <album>I Robot</album>
    <artist>The Alan Parsons Project</artist>
  </song>
</playlist>
```

Objects can validate themselves:

```pycon
>>> song1.validate()
>>> song2.year = 1977
>>> song2.validate()
>>> song2.year = 'abc'
>>> song2.validate()
Traceback (most recent call last):
...
guts.ValidationError: year: "abc" is not of type int
```

Objects can regularize themselves:

```pycon
>>> song2.year = '1977'
>>> song2.validate(regularize=True)
>>> song2.year
1977
>>> type(song2)
<type 'int'>
```

They also deserialize from YAML and XML:

```pycon
>>> playlist2 = load_string(playlist.dump())
>>> playlist3 = load_xml_string(playlist.dump_xml())
```
Incremental loading of large XML files is supported with the `guts.load_xml()` function, which is built as an iterator yielding Guts objects.

This module comes with a rudimentary code generator `xmlschema-to-guts` to turn (some) XML Schema definitions (XSD) into Python modules containing Guts class hierarchies. 

Here is an example using the first example in the W3C XML Schema Primer. The Schema shall be defined in `po.xsd`:

```xml
<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">

  <xsd:annotation>
    <xsd:documentation xml:lang="en">
     Purchase order schema for Example.com.
     Copyright 2000 Example.com. All rights reserved.
    </xsd:documentation>
  </xsd:annotation>

  <xsd:element name="purchaseOrder" type="PurchaseOrderType"/>

  <xsd:element name="comment" type="xsd:string"/>

  <xsd:complexType name="PurchaseOrderType">
    <xsd:sequence>
      <xsd:element name="shipTo" type="USAddress"/>
      <xsd:element name="billTo" type="USAddress"/>
      <xsd:element ref="comment" minOccurs="0"/>
      <xsd:element name="items"  type="Items"/>
    </xsd:sequence>
    <xsd:attribute name="orderDate" type="xsd:date"/>
  </xsd:complexType>

  <xsd:complexType name="USAddress">
    <xsd:sequence>
      <xsd:element name="name"   type="xsd:string"/>
      <xsd:element name="street" type="xsd:string"/>
      <xsd:element name="city"   type="xsd:string"/>
      <xsd:element name="state"  type="xsd:string"/>
      <xsd:element name="zip"    type="xsd:decimal"/>
    </xsd:sequence>
    <xsd:attribute name="country" type="xsd:NMTOKEN"
                   fixed="US"/>
  </xsd:complexType>

  <xsd:complexType name="Items">
    <xsd:sequence>
      <xsd:element name="item" minOccurs="0" maxOccurs="unbounded">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="productName" type="xsd:string"/>
            <xsd:element name="quantity">
              <xsd:simpleType>
                <xsd:restriction base="xsd:positiveInteger">
                  <xsd:maxExclusive value="100"/>
                </xsd:restriction>
              </xsd:simpleType>
            </xsd:element>
            <xsd:element name="USPrice"  type="xsd:decimal"/>
            <xsd:element ref="comment"   minOccurs="0"/>
            <xsd:element name="shipDate" type="xsd:date" minOccurs="0"/>
          </xsd:sequence>
          <xsd:attribute name="partNum" type="SKU" use="required"/>
        </xsd:complexType>
      </xsd:element>
    </xsd:sequence>
  </xsd:complexType>

  <!-- Stock Keeping Unit, a code for identifying products -->
  <xsd:simpleType name="SKU">
    <xsd:restriction base="xsd:string">
      <xsd:pattern value="\d{3}-[A-Z]{2}"/>
    </xsd:restriction>
  </xsd:simpleType>

</xsd:schema>
```

A corresponding XML file `po.xml` might look like this:

```xml
<?xml version="1.0"?>
<purchaseOrder orderDate="1999-10-20">
   <shipTo country="US">
      <name>Alice Smith</name>
      <street>123 Maple Street</street>
      <city>Mill Valley</city>
      <state>CA</state>
      <zip>90952</zip>
   </shipTo>
   <billTo country="US">
      <name>Robert Smith</name>
      <street>8 Oak Avenue</street>
      <city>Old Town</city>
      <state>PA</state>
      <zip>95819</zip>
   </billTo>
   <comment>Hurry, my lawn is going wild</comment>
   <items>
      <item partNum="872-AA">
         <productName>Lawnmower</productName>
         <quantity>1</quantity>
         <USPrice>148.95</USPrice>
         <comment>Confirm this is electric</comment>
      </item>
      <item partNum="926-AA">
         <productName>Baby Monitor</productName>
         <quantity>1</quantity>
         <USPrice>39.98</USPrice>
         <shipDate>1999-05-21</shipDate>
      </item>
   </items>
</purchaseOrder>
```

Using the Guts code generator 

```bash
$ xmlschema-to-guts po.xsd > po.py
```

will produce a Python module `po.py`:

```python
from guts import *

class SKU(StringPattern):
    pattern = '\\d{3}-[A-Z]{2}'


class Comment(String):
    xmltagname = 'comment'


class Quantity(Int):
    pass


class USAddress(Object):
    country = String.T(default='US', optional=True, xmlstyle='attribute')
    name = String.T()
    street = String.T()
    city = String.T()
    state = String.T()
    zip = Float.T()


class Item(Object):
    part_num = SKU.T(xmlstyle='attribute')
    product_name = String.T()
    quantity = Quantity.T()
    us_price = Float.T(xmltagname='USPrice')
    comment = Comment.T(optional=True)
    ship_date = DateTimestamp.T(optional=True)


class Items(Object):
    item_list = List.T(Item.T())


class PurchaseOrderType(Object):
    order_date = DateTimestamp.T(optional=True, xmlstyle='attribute')
    ship_to = USAddress.T()
    bill_to = USAddress.T()
    comment = Comment.T(optional=True)
    items = Items.T()


class PurchaseOrder(PurchaseOrderType):
    xmltagname = 'purchaseOrder'
```

And we can use it e.g. to parse the example XML file `po.xml` from above:

```pycon
>>> from po import *
>>> for x in load_xml(open('po.xml')):
...     print x.dump() # emits YAML
...
--- !po.PurchaseOrder
order_date: '1999-10-20'
ship_to: !po.USAddress
  name: Alice Smith
  street: 123 Maple Street
  city: Mill Valley
  state: CA
  zip: 90952.0
bill_to: !po.USAddress
  name: Robert Smith
  street: 8 Oak Avenue
  city: Old Town
  state: PA
  zip: 95819.0
comment: Hurry, my lawn is going wild
items: !po.Items
  item_list:
  - !po.Item
    part_num: 872-AA
    product_name: Lawnmower
    quantity: 1
    us_price: 148.95
    comment: Confirm this is electric
  - !po.Item
    part_num: 926-AA
    product_name: Baby Monitor
    quantity: 1
    us_price: 39.98
    ship_date: '1999-05-21'
```

