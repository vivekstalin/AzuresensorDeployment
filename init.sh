#!/bin/bash
while [ ! -f /var/log/cloud-init-output.log ] ;
do
      sleep 2
done
echo "/var/log/cloud-init-output.log file found"
while ! grep "Finished vNSP deployment" /var/log/cloud-init-output.log
do
  sleep 5;
done
echo "\"Finished vNSP init setup\" string found"
python cloudAPIAutomation_Azure.py
