#!/bin/bash

# Sometimes on shutdown pid still exists, so delete it
rm -f /var/run/sssd.pid
/sbin/sssd --logger=stderr -d 2 -i 2>&1 &
gosu munge /usr/sbin/munged

echo "Checking demo cluster is ready"
TRY_LIMIT=10
count=0
until sbatch test_job.sbatch
do
    count=$((count+1))
    if [ "$count" = "$TRY_LIMIT" ]
    then
	break
    fi
    sleep 5s
done

scl enable ondemand -- /var/portal_venv/bin/python manage.py test
