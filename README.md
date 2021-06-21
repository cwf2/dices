# dices

DICES is a database of metadata on direct speech representation in Greek and Latin epic poetry. Still in the alpha stage, the prototype currently contains early data for:
- Homer, Odyssey
- Homer, Iliad
- Apollonius, Argonautica
- Vergil, Aeneid
- Ovid, Metamorphoses
- Lucan, Civil War

## Web-based search

The database does not yet have a human-oriented web interface, but one day it will.

## Python client

A python-based client for interacting programmatically with the API is under development. The code is available at [dices-client](https://github.com/cwf2/dices-client). There are a couple of Jupyter Notebooks giving examples of its use at [dices-examples](https://github.com/cwf2/dices-examples); the latter can be tested online using Binder.

## API

The database has a machine-oriented API. This is under development and will be volatile for a while... at least through 2021. If you're not easily frustrated, an alpha version is available at https://fierce-ravine-99183.herokuapp.com/api.

### API endpoints 

#### `/speeches`

Searchable parameters:
- `id`: internal ID
- `spkr_name`: name of speaker
- `spkr_gender`: [`female`, `male`, `non-binary`, `none`], gender of speaker
- `spkr_number`: [`individual`, `collective`], number of speaker
- `spkr_being`: [`mortal`, `divine`, `creature`, `other`], type of being speaking
- `spkr_manto`: speaker's MANTO ID
- `spkr_wd`: speaker's WikiData ID
- `spkr_anon`: [`True`, `False`], whether speaker is anonymous
- `addr_*`: same as above, but for addressee
- `type`: [`S` (soliloquy), `M` (monologue), `D` (dialogue), `G` (general interlocution)], speech type
- `cluster_id`: conversation to which speech belongs
- `part`: *non-zero integer*, position (or "move") of speech within conversation
- `work_title`: (English) name of poem
- `work_urn`: work's CTS URN for edition used
- `work_wd`: work's WikiData ID
- `author_name`: (English) name of author
- `author_urn` author's CITE ID
- `author_wd` author's WikiData ID

### `/clusters`
Searchable parameters:
- `id`: internal ID

### `/instances`

Searchable parameters:
- `id`: internal ID
- `name`: name of character instance
- `gender`: [`female`, `male`, `non-binary`, `none`] gender of character instance
- `number`: [`individual`, `collective`] number of character instance
- `being`: [`mortal`, `divine`, `creature`, `other`] type of being for character instance
- `anon`: [`True`, `False`] whether character instance is anonymous
- `char_name`: name of underlying character, if different from instance name
- `char_number`: number of underlying character, if different from instance name
- `char_being`: being of underlying character, if different from instance name
- `char_gender`: gender of underlying character, if different from instance name
- `manto`: MANTO ID for underlying character
- `wd`: WikiData ID for underlying character

### `/characters`

Searchable parameters:
- `id`: internal ID
- `name`: name of character
- `gender`: [`female`, `male`, `non-binary`, `none`] gender of character
- `number`: [`individual`, `collective`] number of character
- `being`: [`mortal`, `divine`, `creature`, `other`] type of being for character
- `manto`: MANTO ID
- `wd`: WikiData ID

### `/works`

Searchable parameters:
- `id`: internal ID
- `title`: (English) title of poem
- `wd`: WikiData ID of poem
- `urn`: CTS URN of edition
- `author_name`: (English) name of author
- `author_wd`: WikiData ID of author
- `author_urn`: CITE ID of author

### `/authors`

Searchable parameters:
- `id`: internal ID
- `name`: (English) name
- `urn`: CITE ID
