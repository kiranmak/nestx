#!/bin/bash

if [[ $EUID -ne 0 ]]; then
    exec sudo "$0" "$@"
fi

## declare an array variable
declare -a arr=("ospfd", "bgpd" "zebra" "python3" )

## now loop through the above array
for i in "${arr[@]}"
do
    pgrep -f -a "$i"
done

ip netns

