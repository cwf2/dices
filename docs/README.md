# DICES REST API

The DICES database tracks direct speech in Greek and Latin epic poetry —
who speaks to whom, in what context, across roughly 50 poems from Homer to
Late Antiquity.

**Base URL:** `https://db.dices.mta.ca/api/`

For the full, current list of endpoints, fields, and search parameters,
see the live interactive docs:

- **Swagger UI:** https://db.dices.mta.ca/api/docs/
- **OpenAPI schema:** https://db.dices.mta.ca/api/schema/

These are generated directly from the Django models and filter
definitions, so they can't drift out of sync with what the API actually
supports the way hand-written documentation can.

## Data model

- **Author** — an ancient author (e.g. Homer)
- **Work** — a poem, with a language (`greek`/`latin`) and an author
- **Character** — a mythological or historical figure who can speak or be
  addressed (e.g. Athena)
- **Character instance** — a specific appearance of a character in a
  particular context. The same `Character` may have several instances
  across (or even within) works — for example, "Athena disguised as
  Mentor" is a distinct instance from "Athena in her own form," and a
  `CharacterInstance` carries a `disguise` description and a `changed`
  flag for cases like this. An instance with no underlying `Character`
  (`anon=true`) represents a speaker or addressee who isn't individually
  identified, such as an anonymous soldier.
- **Speech** — a single, continuous turn of direct discourse, with a
  `type` (`S` soliloquy, `M` monologue, `D` dialogue, `G` general),
  speaker(s), addressee(s), and a line range (`l_fi`/`l_la`) in the work
- **Speech cluster** — a group of speeches that form a single exchange or
  conversation; a speech's `part` and `level` describe its position
  within its cluster (`level` 0 = main narrative, 1+ = embedded speech
  within a speech)

## Speech tags

Speeches can carry one or more tags describing rhetorical function
(challenge, command, lament, prayer, threat, etc.). The current set of
tag codes is available via the live schema at `/api/schema/`, under the
`tags` field of the speech filter/serializer.

## Public IDs and URNs

Every record has a `public_id` — a short, stable hex identifier used to
build a citable URN of the form:

```
https://db.dices.mta.ca/app/{ModelName}/{public_id}
```

## Python client

For programmatic access, see
[dices-client](https://github.com/cwf2/dices-client), which wraps the API
described above.
