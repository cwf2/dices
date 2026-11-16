# Digital Initiative for Classics: Epic Speeches

DICES is a database of metadata on direct speech representation in Greek and Latin epic poetry. It contains information about who says what to whom in epics from Homer to Late Antiquity, including over 4,700 speeches, 1,000 characters, and nearly 60 poems.

- **Project Website**: [dices.mta.ca](https://dices.mta.ca)
- **Database Search**: [db.dices.mta.ca](https://db.dices.mta.ca)
- **Python Client**: [github.com/cwf2/dices-client](https://github.com/cwf2/dices-client)

This repository contains the Django backend that powers the server.

## Using the data

- **Browse** the database at [db.dices.mta.ca](https://db.dices.mta.ca), where speeches can be searched by work, speaker, addressee, type, and tag.
- **Query the API** at `https://db.dices.mta.ca/api/` (read-only JSON; interactive documentation at `/api/docs/`). The [Python client](https://github.com/cwf2/dices-client) wraps it.
- **Cite or download a release.** Versioned archives of the whole database are deposited on Borealis: [doi:10.5683/SP3/N8LS2Y](https://doi.org/10.5683/SP3/N8LS2Y). The current release number and date are shown at `/app/meta/`.
- **Token-level data.** Parsed and speech-annotated token tables for the same texts (CSV) are on Zenodo: [doi:10.5281/zenodo.24230236](https://doi.org/10.5281/zenodo.24230236).

## Running a local copy

```sh
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

By default the server uses a SQLite database in `data/`. Set `DJANGO_DB=postgres` (and the `POSTGRES_*` variables described in `dices/settings.py`) to use PostgreSQL instead. Settings can also be placed in a `.env` file.

## Backups

`scripts/backup.sh` makes a timestamped, compressed backup of the database in `backups/` (a consistent online copy for SQLite, `pg_dump` for PostgreSQL) and is meant to be run from cron.

## License

Code is released under the [MIT License](LICENSE).
