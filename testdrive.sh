#!/bin/bash

pushd `dirname $0` > /dev/null
DEMOFILES_PATH=`pwd`
popd > /dev/null

export DEMOFILES_PATH=$DEMOFILES_PATH
echo $DEMOFILES_PATH

python $DEMOFILES_PATH/cloudAPIAutomation_Azure.py

#rm -f $DEMOFILES_PATH/cloudAPIAutomation_Azure.py
#rm -f $DEMOFILES_PATH/demodata.txt
#rm -f $DEMOFILES_PATH/testdrive.sh
