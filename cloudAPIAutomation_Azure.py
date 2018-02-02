try:
    import httplib
except ModuleNotFoundError:
    import http.client as httplib
import os
import sys
import base64
import json
import time


while not os.path.isfile("/var/log/cloud-init-output.log"):
    time.sleep(5)
    os.system("echo 'File /var/log/cloud-init-output.log not created yet.. Please Wait.'")
os.system ("echo '\nFile cloud-init-output.log is created'")



with open("/var/log/cloud-init-output.log",'r') as f:
    while not 'Finished vNSP init setup' in f.read():
        f.seek(0,0)
        time.sleep(10)
	os.system("echo 'init setup not finished yet...Please wait.'")

    os.system("echo '\nFinished vNSP init setup.'")


os.environ['DEMOFILES_PATH'] = os.path.dirname(os.path.abspath(__file__))
os.system ("echo '\nRunning script. The logs will be captured in a file:>>> testdrive.log\n'")

def write_log(msg):
    logfile = open(os.environ['DEMOFILES_PATH']+"/testdrive.log","a")
    logfile.write(time.strftime("%d/%m/%Y %H:%M:%S"))
    logfile.write("\t")
    logfile.write(str(msg))
    logfile.write("\n")
    logfile.write("\n")
    logfile.close()

def silentremove(filename):
    try:
        os.remove(filename)
    except OSError as e:
        # write_log("Error while deleting "+filename)
        # write_log(str(e))
        pass

write_log("\n")
env_file_path = os.environ['DEMOFILES_PATH']+"/demodata.txt"
while not os.path.exists(env_file_path):
    write_log("Waiting for the creation of the file " + env_file_path)
    time.sleep(1)

if os.path.isfile(env_file_path):
    env_file = open(env_file_path)
    for line in env_file.readlines():
        line = line.strip()
        if line and not line.startswith("#"):
            key = line.split("=")[0]
            value = line.replace(str(key) + "=","")
            write_log("Setting " + str(key) + " to " + str(value))
            os.environ[key] = value
    env_file.close()
else:
    write_log(env_file_path + " does not exist")

Ip= os.getenv('ISM_IP','localhost')
Port='443'
Url = Ip + ':' + Port
Accept = "application/vnd.nsm.v2.0+json"
Content_Type = "application/json"
api_username = os.getenv('API_ISM_USERNAME', 'admin')
User = api_username
Pass = os.getenv('API_ISM_PASSWD', 'admin123')

write_log(Url)
write_log(User)
write_log(Pass)
try:
    import ssl
    context = ssl._create_unverified_context()
    if Port == '443':
        Connection = httplib.HTTPSConnection(Url, context=context)
    else:
        Connection = httplib.HTTPConnection(Url)
except:
    Connection = httplib.HTTPSConnection(Url)

def get_controller_satus(added_controller_id, Connection):
    controller_url = "/sdkapi/cloud/connector/%s"%(added_controller_id)
    Connection.request("GET", controller_url,  None, Headers)
    response = Connection.getresponse()
    resultData = response.read().decode("utf-8")
    write_log(resultData)
    if resultData.find("errorMessage") != -1:
        time.sleep(10)
        return get_controller_satus(added_controller_id, Connection)
    Connection.close()
    resultObj = json.loads(resultData)
    controller_status = []
    for member in resultObj['members']:
        controller_status.append(member['status'].lower())
    return controller_status

def create_cluster(Connection, added_controller_id, retry_count = 1):
    cluster_url = "/sdkapi/cloud/0/cluster"
    data = {"name" : os.environ['CLUSTER_NAME'], "description":"Demo Cluster", "cloudConnector": str(added_controller_id), "sharedSecret" : os.environ["CLUSTER_SECRET"]}
    if os.environ['CLOUD_PLATFORM'] == "AZURE":
        data["subscription"] = os.environ["AZURE_CLUSTER_SUBSCRIPTION"]
    write_log(str(data))
    payload = json.dumps(data)
    Connection.request("POST", cluster_url,  payload, Headers)
    response = Connection.getresponse()
    resultData = response.read().decode("utf-8")
    write_log(resultData)
    Connection.close()
    if resultData.find("errorMessage") != -1:
        if resultData.find("unacceptable: cloudDomainId") != -1 and retry_count < 16:
            write_log("Error while creating the cluster. Fabric server pool creation failed so retrying after 20 seconds")
            time.sleep(20)
            write_log("Have tried cluster creation for %s time"%(retry_count))
            return create_cluster(Connection, added_controller_id, retry_count + 1)
    else:
        resultObj = json.loads(resultData)
        if resultObj.get('createdResourceId'):
            added_cluster_id = resultObj['createdResourceId']
            write_log("Cluster Created with resource id " + str(added_cluster_id))
            return added_cluster_id
    write_log("Error while creating the cluster.")
    return -1

""" login and set auth """
user_pass = User + ":" + Pass
authString = base64.encodestring(user_pass.encode('utf-8'))
authString = authString.decode('utf-8').replace('\n','')
Headers = {'Accept' : "%s" % Accept, "NSM-SDK-API" : "%s" % authString}
write_log("Logging in to the manager")
Connection.request("GET", "/sdkapi/session", None, Headers)                 
logResponse = Connection.getresponse()
loginData = logResponse.read()
loginObj = json.loads(loginData)
write_log(loginData)
sessionData = loginObj['session']
userData = loginObj['userId']
seesion_user = sessionData + ":" + userData
AuthSession = base64.encodestring(seesion_user.encode('utf-8')).decode('utf-8').replace('\n','')
write_log(AuthSession)
Connection.close()
""" login and set auth over """

Headers = {'Accept': "%s" % Accept, 'NSM-SDK-API': "%s" % AuthSession, 'Content-Type': "%s" % Content_Type}

""" create controller and send the signal """
connector_url = "/sdkapi/cloud/0/connector"
isHA = False
if os.getenv("CONTROLLER_CUSTOM_SERVICE_IP","").strip():
    isHA = True
data = {"name" : os.environ['CONTROLLER_NAME'], "description":"Demo Controller", "sharedSecret" : os.environ["CONTROLLER_SECRET"], "privateCommunicationSubnet" : os.environ['CONTROLLER_SUBNET'], "isHA" : isHA}
if isHA:
    data["serviceIp"] = os.getenv("CONTROLLER_CUSTOM_SERVICE_IP","")
    data["haTimeout"] = os.getenv("CONTROLLER_HA_TIMEOUT",5)
cloudDetails = {}
if os.environ['CLOUD_PLATFORM'] == "AZURE":
    cloudDetails["type"] = "AZURE"
    azureDetails = {}
    azureDetails["directoryId"] = os.environ["AZURE_DIRECTORY_ID"]
    azureDetails['applicationKey'] = os.environ["AZURE_APP_KEY"]
    azureDetails['applicationId'] = os.environ['AZURE_APP_ID']
    azureDetails['subscription'] = os.environ["AZURE_CONTROLLER_SUBSCRIPTION"]
    cloudDetails["azureDetails"] = azureDetails
else:
    cloudDetails["type"] = "AMAZON"
    awsDetails = {}
    awsDetails["region"] = os.environ["CONTROLLER_CLOUD_REGION"].upper().replace("-","_")
    awsDetails["useIAMRole"] = os.environ["USE_IAM_ROLE"] == "TRUE"
    awsDetails["accessKey"] = os.environ["CONTROLLER_CLOUD_ACCESSKEY"]
    awsDetails["secretKey"] = os.environ["CONTROLLER_CLOUD_SECRET"]
    cloudDetails['awsDetails'] = awsDetails
data['cloud'] = cloudDetails
write_log(str(data))
payload = json.dumps(data)
Connection.request("POST", connector_url,  payload, Headers)
response = Connection.getresponse()
resultData = response.read()
write_log(resultData)
Connection.close()
resultObj = json.loads(resultData)
added_controller_id = -1
if resultObj.get('createdResourceId'):
    added_controller_id = resultObj['createdResourceId']
    write_log("Controller Created with resource id " + str(added_controller_id))
    write_log("Sending the signal for controller instance launch")
    write_log("CLOUD PLATFORM TYPE is:"+str(os.environ['CLOUD_PLATFORM']))
    if os.environ['CLOUD_PLATFORM'] == "AZURE":
    	write_log("Executing Azure CLI commands to create controller vm")
        os.system("echo 'Controller VM details will be displayed below. \nPlease wait till the Controller VM gets created and configured'")
        os.system("az vm create -g "+os.environ["VMGROUP_RESOURCE_GROUP"]+" --name "+os.environ["CONTROLLER_NAME"]+" --image "+os.environ["CONTROLLER_IMAGE_ID"]+" --authentication-type ssh "+" --admin-username "+os.environ["CONTROLLER_USER_NAME"]+" --ssh-dest-key-path /home/"+os.environ["CONTROLLER_USER_NAME"]+"/.ssh/authorized_keys"+" --ssh-key-value "+"\""+os.environ["CONTROLLER_SSH_KEY"]+"\""+" --size Standard_E2_v3"+" --nics "+os.environ["DEPLOYMENT_NAME"]+"NICController"+" --location "+os.environ["VMGROUP_LOCATION"]+" --custom-data ./controller_custom_data.txt")
	write_log("Controller VM is launched")
	os.system("echo '\nSuccess. Controller VM is launched.\nPlease wait till the controller gets registered with the Manager and becomes online.'")
    # os.system("cfn-signal -s true " + os.environ["CONTROLLER_WAIT_HANDLE"])
    # os.environ['CONTROLLER_CREATED'] = "0"
else:
    # os.environ['CONTROLLER_CREATED'] = "1"
    write_log("Error while creating the controller.")        
""" create controller and send signal end """
if added_controller_id > 0:
    """ wait for the controller to be online """
    controller_status = get_controller_satus(added_controller_id, Connection)
    write_log("Controller status is %s."%(controller_status))
    waitCount = 0
    while "online" not in controller_status and waitCount < 150:
        time.sleep(10)
        controller_status = get_controller_satus(added_controller_id, Connection)
        waitCount += 1
        write_log("Controller status is %s after %s seconds"%(controller_status,waitCount * 10))
    """ wait for the controller to be online end """

    if "online" in controller_status:
        """ create cluster and send the signal """
	os.system("echo '\nController Registration is successful.\n\nDoing Cluster creation in the Manager. Please wait.'")
        createVMGroup = False
        added_cluster_id = create_cluster(Connection, added_controller_id)
        """ create cluster and send signal end """
        if added_cluster_id > 0:
	    os.system("echo 'Cluster creation in Manager is successful.....'")	
            write_log("Sending the signal for sensor creation")
            write_log("CLOUD PLATFORM TYPE is:"+str(os.environ['CLOUD_PLATFORM']))
	    if os.environ['CLOUD_PLATFORM'] == "AZURE":
		write_log("Executing Azure CLI commands to create sensor vm")
                os.system("echo '\n\nPreparing for sensor launch.\n\nSensor VM details will be displayed below.\nPlease wait till the sensor VM gets created and configured'")
	        os.system("az vm create -g "+os.environ["VMGROUP_RESOURCE_GROUP"]+" --name "+os.environ["SENSOR_NAME"]+" --image "+os.environ["SENSOR_IMAGE_ID"]+" --authentication-type password "+" --admin-username "+os.environ["SENSOR_USER_NAME"]+" --admin-password "+os.environ["SENSOR_PASSWD"]+" --size Standard_F4s"+" --nics "+os.environ["DEPLOYMENT_NAME"]+"NICSensor "+" --location "+os.environ["VMGROUP_LOCATION"]+" --custom-data ./sensor_custom_data.txt")
                write_log("Sensor VM is launched. Deployment is Successful and completed")
		os.system("echo '\nSuccess. Sensor VM is launched.'")
            	
            # os.system("cfn-signal -s true " + os.environ["CLUSTER_WAIT_HANDLE"])
            if os.getenv("CREATE_VMGROUP", "FALSE") == "TRUE":
                vmgroup_url = "/sdkapi/cloud/cluster/%s/vmgroup"%(added_cluster_id)
                data = {"name" : "Demo Group", "description" : "VM Group created at the time of demo", "advancedAgentSettings" : { "inspectionMode" : "IPS" , "trafficProcessing" : "Ingress & Egress"}}
                if os.environ["CLOUD_PLATFORM"] == "AZURE":
                    data["resourceGroup"] = os.environ["VMGROUP_RESOURCE_GROUP"].split(",")
                    data["protectedObjects"] = os.environ["PROTECTED_OBJECTS"].split(",")
                else:
                    data["vpc"] = os.environ["PROTECTED_VPC"].split(",")
                    data["protectedObjects"] = os.environ["PROTECTED_OBJECTS"].split(",")
                write_log(str(data))
                payload = json.dumps(data)
                Connection.request("POST", vmgroup_url,  payload, Headers)
                response = Connection.getresponse()
                resultData = response.read()
                write_log(resultData)
                Connection.close()
                resultObj = json.loads(resultData)
                if resultObj.get('createdResourceId'):
                    # os.environ['CLUSTER_CREATED'] = "0"
                    write_log("VM Group Created with resource id " + str(resultObj['createdResourceId']))
                else:
                    write_log("Error while creating the VM Group.")
                    # os.environ['CLUSTER_CREATED'] = "1"

# silentremove(os.environ['DEMOFILES_PATH']+"/demodata.txt")
# silentremove(os.environ['DEMOFILES_PATH']+"/createCluster.pyc")
# silentremove(os.environ['DEMOFILES_PATH']+"/createCluster.py")
