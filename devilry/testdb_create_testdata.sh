#!/bin/sh

python manage.py dumpdata auth.user --indent=4 > core/fixtures/testusers.json
python manage.py dumpdata core.node --indent=4 > core/fixtures/testnodes.json
python manage.py dumpdata core.subject --indent=4 > core/fixtures/testsubjects.json
python manage.py dumpdata core.period --indent=4 > core/fixtures/testperiods.json
