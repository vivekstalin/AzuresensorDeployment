#!/bin/bash
while [ ! -f /var/log/cloud-init-output.log ] ;
do
      sleep 2
done
echo "/var/log/cloud-init-output.log file found"
while ! grep "Finished vNSP init setup" /var/log/cloud-init-output.log
do
  sleep 5
done
echo "\"Finished vNSP init setup\" string found"
cp -r /root/demodata.txt .
cp -r /root/controller_custom_data.txt .
cp -r /root/sensor_custom_data.txt .
chmod 777 *
python cloudAPIAutomation_Azure.py
echo "Finished cloudAPIAutomation_Azure.py execution"
