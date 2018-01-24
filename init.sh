#!/bin/bash
while [ ! -f /var/log/cloud-init-output.log ] ;
do
      sleep 5
      echo "File /var/log/cloud-init-output.log not created yet...Please wait."
done
echo "File /var/log/cloud-init-output.log got created"
while ! grep "Finished vNSP init setup" /var/log/cloud-init-output.log
do
  sleep 10
  echo "init setup not finished yet...Please wait."
done
echo "\"Finished vNSP init setup\" string found"
cp -r /root/demodata.txt .
cp -r /root/controller_custom_data.txt .
cp -r /root/sensor_custom_data.txt .
chmod 777 *
python cloudAPIAutomation_Azure.py
echo "Finished cloudAPIAutomation_Azure.py execution"
