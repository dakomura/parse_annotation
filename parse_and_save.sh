#!/bin/bash

ndpa=$1
outannot=/tmp
outpatch=$2

ndpi=${ndpa%.*}

annotfile=`basename $ndpi .ndpi`.annot.txt
outpatch=$outpatch/`basename $ndpi .ndpi`
WSIpath=`dirname $ndpi`

echo $WSIpath
echo $outpatch/$annotfile

if [ ! -d $outpatch ]; then
	python parse_annotation.py $ndpi $outannot
	python ndpi_save.py $outannot/$annotfile  $WSIpath $outpatch -s 1024 -p 512 -n 2000
fi
