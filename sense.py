"""
.. module:: sense
   :platform: Ubuntu
   :synopsis: Utility functions to help you get the most out of IPython on `Sense <https://www.senseplatform.com>`.

.. moduleauthor:: Anand Patil <anand@senseplatform.com>
"""

import os
import IPython
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
    """Installs the named package to the current project using `pip. <http://www.pip-installer.org/>`
    
    Parameters
    ----------
    packageName: str 
        The name of the `Python package <https://pypi.python.org/pypi>` to install.
    flags: list, optional 
        Command line flags for pip.
    arguments: list, optional 
        Command line agruments for pip.

    >>> sense.install("beautifulsoup")
    
    The flags list, if provided, will be passed to pip as flags.
    For example, 
    
    >>> ["U", "use-mirrors"] 
    
    translates to 
    
    >>> -U --use-mirrors
    
    The arguments dict, if provided, will be passed to pip as 
    command-line arguments. For example, 
    
    >>> {"d": "./downloads", "mirrors": "http://URL"} 
    
    translates to 
    
    >>> -d ./downloads --mirrors=http://URL
    """
    flagString = " ".join([expandCliArgument(v) for v in flags])
    argString = " ".join([expandCliArgument(k,v) for k,v in arguments.iteritems()])
    os.system("pip install %s --user"%packageName + " " + flagString + " " + argString)
    
def getAuth():
    """Returns the username and password to use with the `Sense REST API. <https://docs.senseplatform.com/api/rest>`

    Returns
    -------
    dict
        A dict with keys 'user' and 'pass'.

    On Sense, this function will 'just work'. If you use it locally, you'll
    need to set either SENSE_API_TOKEN or SENSE_USERNAME and SENSE_PASSWORD
    in the environment.
    """
    if "SENSE_API_TOKEN" in os.environ:
        return {"user": os.environ["SENSE_API_TOKEN"], "pass": ""}
    elif ("SENSE_USERNAME" in os.environ) and ("SENSE_PASSWORD" in os.environ):
        return {"user": os.environ["SENSE_USERNAME"], "password": os.environ["SENSE_PASSWORD"]}
    else:
        raise RuntimeError("Either set environment variable SENSE_API_TOKEN, or else SENSE_USERNAME and SENSE_PASSWORD")

def networkInfo():
    """Returns the current dashboard's networking information.

    Returns
    -------
    dict 
        A dict with keys public_dns, public_port_mapping, ssh_password 
        and project_ip. public_port_mapping is a dict whose keys and 
        values are integers.

    The project IP address is only accessible to other dashboards in the
    same project. Any port can be accessed via the project IP address.

    The public DNS, public port mapping and SSH password tell you how
    the current dashboard can be contacted from outside the project.

    Only ports that are keys of public_port_mapping can be accessed via 
    the public DNS. However, contacting dashboards via the public DNS 
    gives better network performance than the project IP, and should be
    preferred when possible.

    If you run a service on port 3000, for example, it 
    can be accessed from outside the dashboard on the public DNS on port 
    ``public_port_mapping[3000]``.

    The dashboard's SSH daemon is listening on the public DNS on port
    ``public_port_mapping[22]``, and will accept the SSH password. 
    """
    portMapping = {}
    i = 1
    while ("SENSE_PORT" + str(i)) in os.environ:
        portMapping[int(os.environ["SENSE_PORT" + str(i)])] = int(os.environ["SENSE_PORT" + str(i) + "_PUBLIC"])
        i = i + 1
    portMapping["22"] = os.environ["SENSE_SSH_PORT_PUBLIC"]
    return {
            "public_dns": os.environ["SENSE_DNS_PUBLIC"],
            "public_port_mapping": portMapping,
            "ssh_password": os.environ["SENSE_SSH_PASSWORD"],
            "project_ip": os.environ["SENSE_PROJECT_IP"]
           }

def launchWorkers(n, size, engine="sense-ipython-engine", startupScript="", startupCode="", env={}):
    """Launches worker dashboards.
    
    Parameters
    ----------
    n: int 
        The number of dashboards to launch.
    size: str 
        The dashboard size, for example "small", "medium" or "large".
    engine: str, optional 
        The name of the `npm <http://npmjs.org>` module to use as the engine.
    startupScript: str, optional 
        The name of a Python source file the dashboard should execute as soon as it starts up.
    startupCode: str, optional 
        Python code the dashboard should execute as soon as it starts up. Don't provide both startupScript and startupCode.
    env: dict, optional 
        Environment variables to set in the dashboard.

    Returns
    -------
    list
        A list of dicts of the form described in `the REST API. <http://help.senseplatform.com/api/rest#retrieve-dashboard>`
    """

    if os.environ["SENSE_MASTER_ID"] != "":
        raise RuntimeError("launchWorkers should only be called from master dashboards.")

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
    """Returns information on all the workers that share a master with the
    current dashboard, as well as the master.

    Returns
    -------
    list
        A list of dicts of the form described in `the REST API. <http://help.senseplatform.com/api/rest#retrieve-dashboard>`
    """
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
    """Stops the given dashboards.

    Parameters
    ----------
    ids: int, optional
        The id numbers of the dashboards to stop. If not provided, all worker
        dashboards that share a master with the current dashboard will be
        stopped.

    Returns
    -------
    list
        A list of dicts of the form described in `the REST API. <http://help.senseplatform.com/api/rest#retrieve-dashboard>`
    """
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
