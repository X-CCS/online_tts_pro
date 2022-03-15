#!/usr/bin/env bash

for i in $(seq 1 $1)
do   
  nodeName=node$i
  echo "start node="$nodeName
  logName=./logs/$nodeName.log
  echo "start node="$logName
  nohup /root/miniconda3/bin/python proxy.py $nodeName > $logName 2>&1 &
done

/root/miniconda3/bin/python server.py $1
