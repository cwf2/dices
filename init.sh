#!/bin/sh
python manage.py migrate
python manage.py flush --noinput
python manage.py loaddata data/speechdb.json
python manage.py addtestuser deiphobe $TEST_USER_PASS