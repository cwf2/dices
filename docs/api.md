# DICES REST API Documentation

## Overview

The DICES (Digital Initiative for Classics: Epic Speeches) REST API provides programmatic access to a comprehensive database of metadata on direct speech representation in Greek and Latin epic poetry. The database contains over 4,500 speeches, 1,000 characters, and 50 poems from Homer to Late Antiquity.

**Base URL:** `https://db.dices.mta.ca/api/`

**API Version:** 1.0

## Authentication

Currently, the API endpoints are publicly accessible and do not require authentication.

## Response Format

All responses are returned in JSON format. List endpoints return an array of objects, while detail endpoints return a single object.

### Common Fields

All database records include a `public_id` field - a unique 4-character hexadecimal identifier used for generating URNs.

### URN Format

DICES URNs follow the pattern: `https://db.dices.mta.ca/app/{ModelName}/{public_id}`

Example: `https://db.dices.mta.ca/app/Character/A3F2`

## Pagination

List endpoints support pagination through query parameters:
- `limit` - Number of results per page
- `offset` - Starting position for results

## Filtering

Most endpoints support extensive filtering via query parameters. Multiple filters can be combined using standard URL query syntax (`?filter1=value1&filter2=value2`).

---

## Endpoints

### 1. Metadata

#### List Metadata
**Endpoint:** `GET /api/meta/`

Retrieves database metadata information.

**Query Parameters:**
- `name` - Filter by metadata name (exact match)

**Response Fields:**
- `id` - Unique identifier
- `public_id` - 4-character hex ID
- `name` - Metadata key name
- `value` - Metadata value
- `dices_urn` - URN for this metadata record

**Example Request:**
```
GET /api/meta/?name=version
```

**Example Response:**
```json
[
  {
    "id": 1,
    "public_id": "A1B2",
    "name": "version",
    "value": "2.0",
    "dices_urn": "https://db.dices.mta.ca/app/Metadata/A1B2"
  }
]
```

---

### 2. Authors

Ancient authors of epic works.

#### List Authors
**Endpoint:** `GET /api/authors/`

**Query Parameters:**

*Author fields:*
- `id` - Author ID
- `name` - Author name (partial match)
- `wd` - Wikidata ID
- `urn` - CTS URN

*Related work filters:*
- `lang` - Work language (`greek` or `latin`)
- `work_id` - Filter by work ID
- `work_title` - Work title (partial match)
- `work_urn` - Work URN
- `work_wd` - Work Wikidata ID

**Response Fields:**
- `id` - Unique identifier
- `public_id` - 4-character hex ID
- `name` - Author name
- `wd` - Wikidata identifier
- `urn` - CTS URN for the author
- `dices_urn` - DICES URN

**Example Request:**
```
GET /api/authors/?lang=greek
```

**Example Response:**
```json
[
  {
    "id": 1,
    "public_id": "1A2B",
    "name": "Homer",
    "wd": "Q6691",
    "urn": "urn:cts:greekLit:tlg0012",
    "dices_urn": "https://db.dices.mta.ca/app/Author/1A2B"
  }
]
```

#### Get Author Detail
**Endpoint:** `GET /api/authors/{id}/`

Returns detailed information for a specific author.

**URL Parameters:**
- `id` - The author's numeric ID

---

### 3. Works

Epic texts and poems.

#### List Works
**Endpoint:** `GET /api/works/`

**Query Parameters:**

*Work fields:*
- `id` - Work ID
- `title` - Work title (partial match)
- `wd` - Wikidata ID
- `tlg` - TLG (Thesaurus Linguae Graecae) identifier
- `urn` - CTS URN
- `lang` - Language (`greek` or `latin`)

*Related author filters:*
- `author_id` - Author ID
- `author_name` - Author name (partial match)
- `author_wd` - Author Wikidata ID
- `author_urn` - Author URN

**Response Fields:**
- `id` - Unique identifier
- `public_id` - 4-character hex ID
- `title` - Work title
- `wd` - Wikidata identifier
- `tlg` - TLG identifier
- `urn` - CTS URN
- `author` - Nested author object (depth=2)
- `lang` - Language (`greek` or `latin`)
- `dices_urn` - DICES URN

**Example Request:**
```
GET /api/works/?author_name=Homer&lang=greek
```

**Example Response:**
```json
[
  {
    "id": 1,
    "public_id": "2C3D",
    "title": "Iliad",
    "wd": "Q8275",
    "tlg": "tlg0012.tlg001",
    "urn": "urn:cts:greekLit:tlg0012.tlg001",
    "lang": "greek",
    "author": {
      "id": 1,
      "public_id": "1A2B",
      "name": "Homer",
      "wd": "Q6691",
      "urn": "urn:cts:greekLit:tlg0012",
      "dices_urn": "https://db.dices.mta.ca/app/Author/1A2B"
    },
    "dices_urn": "https://db.dices.mta.ca/app/Work/2C3D"
  }
]
```

#### Get Work Detail
**Endpoint:** `GET /api/works/{id}/`

Returns detailed information for a specific work.

**URL Parameters:**
- `id` - The work's numeric ID

---

### 4. Characters

Epic characters appearing in speeches.

#### List Characters
**Endpoint:** `GET /api/characters/`

**Query Parameters:**

*Character fields:*
- `id` - Character ID
- `name` - Character name (partial match)
- `being` - Being type: `mortal`, `divine`, `creature`, or `other`
- `number` - Number: `individual` or `collective`
- `gender` - Gender: `male`, `female`, `x` (mixed/non-binary), or `none` (unknown/N/A)
- `wd` - Wikidata ID
- `manto` - MANTO (Mythology ANnotation TOol) ID
- `tt` - ToposText ID

*Related work/author filters:*
- `work_id` - Filter by work ID
- `work_title` - Work title (partial match)
- `work_urn` - Work URN
- `work_wd` - Work Wikidata ID
- `work_lang` - Work language (`greek` or `latin`)
- `author_id` - Author ID
- `author_name` - Author name (partial match)
- `author_wd` - Author Wikidata ID
- `author_urn` - Author URN

*Character instance filters:*
- `inst_name` - Instance name (partial match)
- `inst_gender` - Instance gender
- `inst_number` - Instance number
- `inst_being` - Instance being type

*Speech filters:*
- `speech_type` - Speech type (`S`, `M`, `D`, or `G`)
- `speech_part` - Speech part number

**Response Fields:**
- `id` - Unique identifier
- `public_id` - 4-character hex ID
- `name` - Character name
- `being` - Being type
- `number` - Individual or collective
- `gender` - Gender
- `wd` - Wikidata identifier
- `manto` - MANTO identifier
- `tt` - ToposText identifier
- `notes` - Additional notes
- `dices_urn` - DICES URN

**Example Request:**
```
GET /api/characters/?gender=female&being=divine
```

**Example Response:**
```json
[
  {
    "id": 42,
    "public_id": "3E4F",
    "name": "Athena",
    "being": "divine",
    "number": "individual",
    "gender": "female",
    "wd": "Q37122",
    "manto": "ath01",
    "tt": "Athena",
    "notes": "",
    "dices_urn": "https://db.dices.mta.ca/app/Character/3E4F"
  }
]
```

#### Get Character Detail
**Endpoint:** `GET /api/characters/{id}/`

Returns detailed information for a specific character.

**URL Parameters:**
- `id` - The character's numeric ID

---

### 5. Character Instances

Character instances represent specific manifestations of characters in particular contexts (e.g., "Athena disguised as Mentor" vs. "Athena as herself").

#### List Character Instances
**Endpoint:** `GET /api/instances/`

**Query Parameters:**

*Instance fields:*
- `id` - Instance ID
- `name` - Instance name (partial match)
- `display` - Display name (partial match)
- `being` - Being type
- `number` - Individual or collective
- `gender` - Gender
- `anon` - Anonymous speaker (boolean: `true` or `false`)
- `context` - Context description (partial match)

*Related character filters:*
- `char_id` - Character ID
- `char_name` - Character name (partial match)
- `char_gender` - Character gender
- `char_number` - Character number
- `char_being` - Character being type
- `wd` - Character Wikidata ID
- `manto` - Character MANTO ID

*Related work/author filters:*
- `work_id` - Work ID
- `work_title` - Work title (partial match)
- `work_urn` - Work URN
- `work_wd` - Work Wikidata ID
- `work_lang` - Work language
- `author_id` - Author ID
- `author_name` - Author name (partial match)
- `author_wd` - Author Wikidata ID
- `author_urn` - Author URN

*Speech filters:*
- `speech_type` - Speech type
- `speech_part` - Speech part

**Response Fields:**
- `id` - Unique identifier
- `public_id` - 4-character hex ID
- `name` - Instance name
- `display` - Display name
- `being` - Being type
- `number` - Individual or collective
- `gender` - Gender
- `char` - Nested character object (depth=1)
- `disguise` - Disguise description
- `anon` - Whether speaker is anonymous
- `notes` - Additional notes
- `context` - Context description
- `dices_urn` - DICES URN

**Example Request:**
```
GET /api/instances/?char_name=Athena&anon=false
```

**Example Response:**
```json
[
  {
    "id": 84,
    "public_id": "4G5H",
    "name": "Athena",
    "display": "Athena",
    "being": "divine",
    "number": "individual",
    "gender": "female",
    "char": {
      "id": 42,
      "public_id": "3E4F",
      "name": "Athena",
      "being": "divine",
      "number": "individual",
      "gender": "female",
      "wd": "Q37122",
      "manto": "ath01",
      "tt": "Athena",
      "notes": "",
      "dices_urn": "https://db.dices.mta.ca/app/Character/3E4F"
    },
    "disguise": "",
    "anon": false,
    "notes": "",
    "context": "Iliad",
    "dices_urn": "https://db.dices.mta.ca/app/CharacterInstance/4G5H"
  }
]
```

#### Get Character Instance Detail
**Endpoint:** `GET /api/instances/{id}/`

Returns detailed information for a specific character instance.

**URL Parameters:**
- `id` - The instance's numeric ID

---

### 6. Speeches

Individual direct speech instances in epic texts.

#### List Speeches
**Endpoint:** `GET /api/speeches/`

**Query Parameters:**

*Speech fields:*
- `id` - Speech ID
- `type` - Speech type:
  - `S` - Soliloquy
  - `M` - Monologue
  - `D` - Dialogue
  - `G` - General
- `tags` - Speech tag type (see Speech Tags section below)
- `seq` - Sequence number
- `part` - Part number
- `level` - Nesting level
- `l_fi` - First line (partial match)
- `l_la` - Last line (partial match)

*Speaker (character instance) filters:*
- `spkr_inst_id` - Speaker instance ID
- `spkr_inst_name` - Speaker instance name (partial match)
- `spkr_inst_gender` - Speaker instance gender
- `spkr_inst_number` - Speaker instance number
- `spkr_inst_being` - Speaker instance being type
- `spkr_anon` - Speaker is anonymous (boolean)

*Speaker (character) filters:*
- `spkr_id` - Speaker character ID
- `spkr_name` - Speaker character name (partial match)
- `spkr_gender` - Speaker character gender
- `spkr_number` - Speaker character number
- `spkr_being` - Speaker character being type
- `spkr_manto` - Speaker MANTO ID
- `spkr_wd` - Speaker Wikidata ID
- `spkr_tt` - Speaker ToposText ID

*Addressee (character instance) filters:*
- `addr_inst_id` - Addressee instance ID
- `addr_inst_name` - Addressee instance name (partial match)
- `addr_inst_gender` - Addressee instance gender
- `addr_inst_number` - Addressee instance number
- `addr_inst_being` - Addressee instance being type
- `addr_anon` - Addressee is anonymous (boolean)

*Addressee (character) filters:*
- `addr_id` - Addressee character ID
- `addr_name` - Addressee character name (partial match)
- `addr_gender` - Addressee character gender
- `addr_number` - Addressee character number
- `addr_being` - Addressee character being type
- `addr_manto` - Addressee MANTO ID
- `addr_wd` - Addressee Wikidata ID
- `addr_tt` - Addressee ToposText ID

*Cluster filter:*
- `cluster_id` - Speech cluster ID

*Work filters:*
- `work_id` - Work ID
- `work_title` - Work title (partial match)
- `work_urn` - Work URN
- `work_wd` - Work Wikidata ID
- `work_lang` - Work language

*Author filters:*
- `author_id` - Author ID
- `author_name` - Author name (partial match)
- `author_wd` - Author Wikidata ID
- `author_urn` - Author URN

**Response Fields:**
- `id` - Unique identifier
- `public_id` - 4-character hex ID
- `cluster` - Nested cluster object (depth=3)
- `work` - Nested work object (depth=3)
- `type` - Speech type
- `seq` - Sequence number in the work
- `l_fi` - First line reference
- `l_la` - Last line reference
- `spkr` - Array of speaker instances (depth=3)
- `addr` - Array of addressee instances (depth=3)
- `spkr_notes` - Notes about speakers
- `addr_notes` - Notes about addressees
- `part` - Part number (for multi-part speeches)
- `level` - Nesting level (0=main narrative, 1=embedded, etc.)
- `notes` - Additional notes
- `tags` - Array of speech tags
- `dices_urn` - DICES URN

**Example Request:**
```
GET /api/speeches/?spkr_name=Achilles&addr_name=Agamemnon&work_title=Iliad
```

**Example Response:**
```json
[
  {
    "id": 123,
    "public_id": "5I6J",
    "type": "D",
    "seq": 45,
    "l_fi": "1.131",
    "l_la": "1.147",
    "part": 1,
    "level": 0,
    "spkr_notes": "",
    "addr_notes": "",
    "notes": "",
    "cluster": { /* nested cluster object */ },
    "work": { /* nested work object with author */ },
    "spkr": [ /* array of speaker instances */ ],
    "addr": [ /* array of addressee instances */ ],
    "tags": [
      {
        "type": "tau",
        "doubt": false
      }
    ],
    "dices_urn": "https://db.dices.mta.ca/app/Speech/5I6J"
  }
]
```

#### Get Speech Detail
**Endpoint:** `GET /api/speeches/{id}/`

Returns detailed information for a specific speech.

**URL Parameters:**
- `id` - The speech's numeric ID

---

### 7. Speech Clusters

Groups of related speeches that form conversations or exchanges.

#### List Speech Clusters
**Endpoint:** `GET /api/clusters/`

**Query Parameters:**

*Cluster fields:*
- `id` - Cluster ID
- `seq` - Sequence number

*Work filters:*
- `work_id` - Work ID
- `work_title` - Work title (partial match)
- `work_urn` - Work URN
- `work_wd` - Work Wikidata ID

*Author filters:*
- `author_id` - Author ID
- `author_name` - Author name (partial match)
- `author_wd` - Author Wikidata ID
- `author_urn` - Author URN

*Speaker (instance) filters:*
- `spkr_inst_id` - Speaker instance ID
- `spkr_inst_name` - Speaker instance name (partial match)
- `spkr_inst_gender` - Speaker instance gender
- `spkr_inst_number` - Speaker instance number
- `spkr_inst_being` - Speaker instance being type
- `spkr_anon` - Speaker is anonymous (boolean)

*Speaker (character) filters:*
- `spkr_id` - Speaker character ID
- `spkr_name` - Speaker character name (partial match)
- `spkr_gender` - Speaker character gender
- `spkr_number` - Speaker character number
- `spkr_being` - Speaker character being type
- `spkr_manto` - Speaker MANTO ID
- `spkr_wd` - Speaker Wikidata ID
- `spkr_tt` - Speaker ToposText ID

*Addressee (instance) filters:*
- `addr_inst_id` - Addressee instance ID
- `addr_inst_name` - Addressee instance name (partial match)
- `addr_inst_gender` - Addressee instance gender
- `addr_inst_number` - Addressee instance number
- `addr_inst_being` - Addressee instance being type
- `addr_anon` - Addressee is anonymous (boolean)

*Addressee (character) filters:*
- `addr_id` - Addressee character ID
- `addr_name` - Addressee character name (partial match)
- `addr_gender` - Addressee character gender
- `addr_number` - Addressee character number
- `addr_being` - Addressee character being type
- `addr_manto` - Addressee MANTO ID
- `addr_wd` - Addressee Wikidata ID
- `addr_tt` - Addressee ToposText ID

**Response Fields:**
- `id` - Unique identifier
- `public_id` - 4-character hex ID
- `seq` - Sequence number
- `speeches` - Array of speech objects (nested depth=3)
- `dices_urn` - DICES URN

**Example Request:**
```
GET /api/clusters/?spkr_name=Achilles&work_title=Iliad
```

**Example Response:**
```json
[
  {
    "id": 25,
    "public_id": "6K7L",
    "seq": 12,
    "speeches": [
      {
        "id": 123,
        "public_id": "5I6J"
      },
      {
        "id": 124,
        "public_id": "7M8N"
      }
    ],
    "dices_urn": "https://db.dices.mta.ca/app/SpeechCluster/6K7L"
  }
]
```

#### Get Speech Cluster Detail
**Endpoint:** `GET /api/clusters/{id}/`

Returns detailed information for a specific speech cluster.

**URL Parameters:**
- `id` - The cluster's numeric ID

---

## Speech Tags

Speeches can be tagged with categorical labels describing their rhetorical function. Available tag types:

| Code | Description |
|------|-------------|
| `cha` | Challenge |
| `com` | Command |
| `con` | Consolation |
| `del` | Deliberation |
| `des` | Desire and Wish |
| `exh` | Exhortation and Self-Exhortation |
| `far` | Farewell |
| `gre` | Greeting and Reception |
| `inf` | Information and Description |
| `inv` | Invitation |
| `ins` | Instruction |
| `lam` | Lament |
| `lau` | Praise and Laudation |
| `mes` | Message |
| `nar` | Narration |
| `ora` | Prophecy, Oracular Speech, and Interpretation |
| `per` | Persuasion |
| `pra` | Prayer |
| `que` | Question |
| `req` | Request |
| `res` | Reply to Question |
| `tau` | Taunt |
| `thr` | Threat |
| `vit` | Vituperation |
| `vow` | Promise and Oath |
| `war` | Warning |
| `und` | Undefined |

Each tag has an optional `doubt` field (boolean) indicating uncertainty about the categorization.

---

## Choice Field Values

### Language
- `greek` - Greek
- `latin` - Latin

### Character Being
- `mortal` - Mortal
- `divine` - Divine
- `creature` - Mythical Creature
- `other` - Other

### Character Number
- `individual` - Individual
- `collective` - Collective

### Character Gender
- `male` - Male
- `female` - Female
- `x` - Mixed/non-binary
- `none` - Unknown/not-applicable

### Speech Type
- `S` - Soliloquy (character speaking to self)
- `M` - Monologue (character speaking to others without response)
- `D` - Dialogue (two-way conversation)
- `G` - General (speech to a group)

---

## Query Parameter Syntax

### Partial Matching
Text filters (e.g., `name`, `title`) support partial matching. For example:
```
/api/characters/?name=Ath
```
Returns all characters whose name contains "Ath" (Athena, Athenian, etc.)

### Exact Matching
Numeric and choice fields require exact matches:
```
/api/works/?lang=greek
/api/characters/?gender=female
```

### Boolean Filters
Boolean fields accept `true` or `false`:
```
/api/instances/?anon=true
```

### Multiple Filters
Combine filters with `&`:
```
/api/speeches/?work_title=Iliad&spkr_gender=female&type=M
```

### Cross-Entity Filtering
Many endpoints support filtering by related entities. For example, filtering characters by the works they appear in:
```
/api/characters/?work_title=Odyssey&author_name=Homer
```

---

## Dynamic Field Selection

The API uses a custom `DynamicModelSerializer` that supports dynamic field selection and nesting depth control through query parameters:

### Field Selection
Use the `fields` parameter to specify which fields to include in the response (currently configured server-side).

### Depth Control
Serializer depth is pre-configured per endpoint:
- **Author**: depth=0 (no nested objects)
- **Work**: depth=2 (includes nested author)
- **Character**: depth=0
- **CharacterInstance**: depth=1 (includes nested character)
- **Speech**: depth=3 (includes nested work, cluster, speakers, addressees with full details)
- **SpeechCluster**: depth=3 (includes nested speeches with full details)

---

## Error Handling

### HTTP Status Codes
- `200 OK` - Request successful
- `400 Bad Request` - Invalid query parameters
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

### Error Response Format
```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## Rate Limiting

Currently, the API does not implement rate limiting. However, please be respectful of server resources and avoid making excessive requests.

---

## Examples

### Find all female divine characters in Greek works
```
GET /api/characters/?gender=female&being=divine&work_lang=greek
```

### Get all speeches by Achilles in the Iliad
```
GET /api/speeches/?spkr_name=Achilles&work_title=Iliad
```

### Find all prayers in Homer's works
```
GET /api/speeches/?tags=pra&author_name=Homer
```

### Get dialogue speeches between specific characters
```
GET /api/speeches/?type=D&spkr_name=Hector&addr_name=Andromache
```

### Find all Latin epic works
```
GET /api/works/?lang=latin
```

### Get speech clusters involving divine speakers
```
GET /api/clusters/?spkr_being=divine
```

---

## Additional Resources

- **Project Website**: [dices.mta.ca](http://dices.mta.ca)
- **Database Search Interface**: [db.dices.mta.ca](http://db.dices.mta.ca)
- **Python Client Library**: [github.com/cwf2/dices-client](https://github.com/cwf2/dices-client)
- **GitHub Repository**: [github.com/cwf2/dices](https://github.com/cwf2/dices)

---

## Support

For questions, issues, or feature requests, please open an issue on the GitHub repository.

---

*Last Updated: January 2026*
