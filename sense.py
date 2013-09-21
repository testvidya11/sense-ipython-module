import os
import IPython
import simplejson
import requests
import futures
threadPoolSize=10

__all__ = ["install", "networkInfo", "getAuth", "networkInfo", "launchWorkers", "getWorkers", "stopWorkers"]

def expandCliArgument(arg, value=None):
    if len(arg) == 1:
        dashedArg = "-" + arg
        if value is not None:
          return dashedArg + " " + value
    else:
        dashedArg = "--" + arg
        if value is not None:
          return dashedArg + "=" + value
    return dashedArg

def install(packageName, flags=[], arguments={}):
    """
    Installs the named package to the current project using pip.
    
    > sense.install("beautifulsoup")
    
    The flags list, if provided, will be passed to pip as flags.
    For example, 
    
    > ["U", "use-mirrors"] 
    
    translates to 
    
    > -U --use-mirrors
    
    The arguments dict, if provided, will be passed to pip as 
    command-line arguments. For example, 
    
    > {"d": "./downloads", "mirrors": "http://URL"} 
    
    translates to 
    
    > -d ./downloads --mirrors=http://URL
    """
    flagString = " ".join([expandCliArgument(v) for v in flags])
    argString = " ".join([expandCliArgument(k,v) for k,v in arguments.iteritems()])
    os.system("pip install %s --user"%packageName + " " + flagString + " " + argString)
    
def getAuth():
    if "SENSE_API_TOKEN" in os.environ:
        return {"user": os.environ["SENSE_API_TOKEN"], "pass": ""}
    elif ("SENSE_USERNAME" in os.environ) and ("SENSE_PASSWORD" in os.environ):
        return {"user": os.environ["SENSE_USERNAME"], "password": os.environ["SENSE_PASSWORD"]}
    else:
        raise RuntimeError("Either set environment variable SENSE_API_TOKEN, or else SENSE_USERNAME and SENSE_PASSWORD")

def networkInfo():
    portMapping = {}
    i = 1
    while ("SENSE_PORT" + str(i)) in os.environ:
        portMapping[os.environ["SENSE_PORT" + str(i)]] = os.environ["SENSE_PORT" + str(i) + "_PUBLIC"]
        i = i + 1
    portMapping["22"] = os.environ["SENSE_SSH_PORT_PUBLIC"]
    return {
            "public_dns": os.environ["SENSE_DNS_PUBLIC"],
            "public_port_mapping": portMapping,
            "ssh_password": os.environ["SENSE_SSH_PASSWORD"],
            "project_ip": os.environ["SENSE_PROJECT_IP"]
           }

def launchWorkers(n, size, engine="sense-ipython-engine", startupScript="", startupCode="", env={}):
    
    requestBody = {
        "name": "Worker for IPython dashboard" + os.environ["SENSE_DASHBOARD_ID"],
        "engine": engine,
        "size": size,
        "startupScript": startupScript,
        "startupCode": startupCode,
        "env": env,
        "master_id": os.environ["SENSE_DASHBOARD_ID"]
    }
    url = "https://api.senseplatform.com/users/" + os.environ["SENSE_OWNER_ID"] + "/projects/" + os.environ["SENSE_PROJECT_ID"] + "/dashboards"
    auth = getAuth()
    
    # The n launch requests are done concurrently in a thread pool for lower
    # latency.
    def launchWorker(i):
        return requests.post(url, data=requestBody, auth=(auth["user"], auth["pass"])).json()
    pool = futures.ThreadPoolExecutor(threadPoolSize)
    responses = [pool.submit(launchWorker, i) for i in xrange(n)]
    return map(lambda x: x.result(), futures.wait(responses)[0])

def getWorkers():
    
    if os.environ["SENSE_MASTER_ID"] == "":
        masterId = os.environ["SENSE_DASHBOARD_ID"]
    else:
        masterId = os.environ["SENSE_MASTER_ID"]
    
    masterId = int(masterId)
    auth = getAuth()
    url = "https://api.senseplatform.com/users/" + os.environ["SENSE_OWNER_ID"] + "/projects/" + os.environ["SENSE_PROJECT_ID"] + "/dashboards/"
    response = requests.get(url, auth=(auth["user"], auth["pass"])).json()
    
    def isWorker(dashboard):
        return dashboard["status"] == "running" and (dashboard["id"] == masterId or dashboard["master_id"] == masterId)
    
    return filter(isWorker, response)    

def stopWorkers(*ids):

    if len(ids) == 0:
        ids_ = filter(lambda x: x["master_id"] is not None, getWorkers())
        ids_ = map(lambda x: x["id"], ids_)
        stopWorkers(*ids_)
    else:
        baseUrl = "https://api.senseplatform.com/users/" + os.environ["SENSE_OWNER_ID"] + "/projects/" + os.environ["SENSE_PROJECT_ID"] + "/dashboards/";
        requestBody = {"status": "stopped"}
        auth = getAuth()
        
        # The stop requests are done concurrently in a thread pool for lower latency.
        def stopWorker(id):
            return requests.patch(baseUrl + str(id), data=requestBody, auth=(auth["user"], auth["pass"])).json()

        pool = futures.ThreadPoolExecutor(threadPoolSize)
        responses = [pool.submit(stopWorker, id) for id in ids]
        return map(lambda x: x.result(), futures.wait(responses)[0])
