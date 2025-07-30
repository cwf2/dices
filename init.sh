#!/bin/sh

#
# set default values, secrets
#

echo "Setting environment variables"

DJANGO_HOSTNAME="localhost"
DJANGO_ADMIN_PW=$(tr -dc 'a-zA-Z0-9~!@#$%^&*_-' < /dev/urandom | head -c 16)
DJANGO_SECRET_KEY=$(tr -dc 'a-zA-Z0-9~!@#$%^&*_-' < /dev/urandom | head -c 32)
DICES_USER=$(id -un)
DICES_GRP=$(id -gn)
DICES_ROOT=$(pwd)
DICES_APP_USER="deiphobe"
DICES_APP_USER_PW="taliadixit"

echo "DJANGO_HOSTNAME=$DJANGO_HOSTNAME"
echo "DJANGO_ADMIN_PW=$DJANGO_ADMIN_PW"
echo "DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY"
echo "DICES_USER=$DICES_USER"
echo "DICES_GRP=$DICES_GRP"
echo "DICES_ROOT=$DICES_ROOT"
DICES_APP_USER="cyllenius"
DICES_APP_USER_PW="uerbareferre"

#
# write .env to dices dir
#

echo "Writing environment variables to .env"

cat > "$DICES_ROOT/.env" <<END_HERE
#
# dotenv configuration file
#
DJANGO_HOSTNAME=$DJANGO_HOSTNAME
DJANGO_ADMIN_PW=$DJANGO_ADMIN_PW
DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY
#
END_HERE

#
# setup database
#

echo "Initializing database"

python manage.py flush --noinput
python manage.py migrate
python manage.py loaddata data/speechdb.json
python manage.py addtestuser deiphobe $TEST_USER_PASS
