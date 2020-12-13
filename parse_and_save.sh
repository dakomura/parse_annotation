#!/bin/bash

set -euo

ndpa=$1
outannot=/tmp
outpatch=$2
s=${3:-512} #size in original WSI
p=${4:-256} #output pixel size
n=${5:-20} #number of output image per WSI


echo input $ndpa
echo output dir $outpatch
echo $s pix in WSI to $p pix output
echo $n images per WSI

ndpi=${ndpa%.*}

annotfile=`basename $ndpi .ndpi`.annot.txt
outpatch=$outpatch/`basename $ndpi .ndpi`
WSIpath=`dirname "$ndpi"`

echo $WSIpath
echo $outpatch/$annotfile

if [ ! -d "$outpatch" ]; then
	python parse_annotation.py "$ndpi" "$outannot"
	python ndpi_save.py "$outannot/$annotfile"  "$WSIpath" "$outpatch" -s $s -p $p -n $n
fi
