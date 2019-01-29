#!/usr/bin/env bash
source /home/kyfq/.virtualenvs/dms/bin/activate
cd /home/kyfq/MyPython/PycharmProjects/dms/DMS
uwsgi --reload uwsgi.pid
/etc/init.d/nginx restart
