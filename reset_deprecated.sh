#!/bin/bash

# This simply removes all items in 'Data' and 'SourceData' and copies the contents of 'temp_copy'
# to 'Import'. Used for testing 'Convert/convert_script.py'
#
# This script should only be run from within its containing directory.

# preserve READMEs
mv Data/README.md Data_README.md
mv SourceData/README.md SourceData_README.md

rm -rf Data/*
rm -f SourceData/*

# put READMEs back
mv Data_README.md Data/README.md
mv SourceData_README.md SourceData/README.md

rsync temp_copy/* Import/.