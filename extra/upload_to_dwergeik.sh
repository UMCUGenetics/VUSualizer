#!/bin/bash

for file in DN*.xlsx
do
    scp ./${file} user@dwergeik.op.umcutrecht.nl:/data/vusualizer/VUSualizer/extra/input
    sleep 5
done