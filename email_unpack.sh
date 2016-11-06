#!/bin/bash

mkdir -p messages
zcat podesta-emails.mbox-2016-11-06.gz | formail -ds sh -c 'cat > messages/$FILENO.eml'
