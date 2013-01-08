Guts
====
 
Lightweight declarative YAML and XML data binding for Python

Usage
-----

playlist.py:

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

These classes come with automatic __init__:

```python
>>> from playlist import *
>>> song1 = Song(name='Metropolis', artist='Kraftwerk')
>>> song2 = Song(name='I Robot', artist='The Alan Parsons Project', album='I Robot')
>>> playlist = Playlist(song_list=[song1,song2])
```

They serialize to YAML:

```python
>>> print song1.dump()
--- !playlist.Song
name: Metropolis
artist: Kraftwerk
```

They also serialize to XML:

```pycon
>>> print playlist.dump_xml()
<Song>
  <name>Metropolis</name>
  <artist>Kraftwerk</artist>
</Song>
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

```python
>>> song2.year = '1977'
>>> song2.validate(regularize=True)
>>> song2.year
1977
>>> type(song2)
<type 'int'>
```


