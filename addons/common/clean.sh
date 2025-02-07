#!/bin/bash

if [[ $EUID -ne 0 ]]; then
    exec sudo "$0" "$@"
fi

## declare an array variable
declare -a arr=("ospfd" "bgpd" "zebra" "python3")

## now loop through the above array
for i in "${arr[@]}"
do
    if pgrep -f $i > /dev/null; then
       echo "$i all instances will be killed"
       pkill -f $i
    else
       echo "$i is not running"
    fi
done

ip -all netns del
echo "[netns] Namespaces deleted."

rm -fr frr-logs_*
echo "[FRR-LOGS] All deleted."

