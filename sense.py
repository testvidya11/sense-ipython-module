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
thread_pool_size=10
API_URL = "https://api.senseplatform.com" or os.environ["SENSE_API_URL"]

__all__ = ["install", "network_info", "get_auth", "network_info", "launch_workers", "get_workers", "stop_workers"]

def expand_cli_arguments(arg, value=None):
    if len(arg) == 1:
        dashed_args = "-" + arg
        if value is not None:
          return dashed_args + " " + value
    else:
        dashed_args = "--" + arg
        if value is not None:
          return dashed_args + "=" + value
    return dashed_args

def install(package_name, flags=[], arguments={}):
    """Installs the named package to the current project using `pip. <http://www.pip-installer.org/>`
    
    Parameters
    ----------
    package_name: str 
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
    flag_string = " ".join([expand_cli_arguments(v) for v in flags])
    arg_string = " ".join([expand_cli_arguments(k,v) for k,v in arguments.iteritems()])
    os.system("pip install %s --user"%package_name + " " + flag_string + " " + arg_string)
    
def get_auth():
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

def network_info():
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
    gives better network performance than the project IP.

    If you run a service on port 3000, for example, it 
    can be accessed from outside the dashboard on the public DNS on port 
    ``public_port_mapping[3000]``.

    The dashboard's SSH daemon is listening on the public DNS on port
    ``public_port_mapping[22]``, and will accept the SSH password. 
    """
    port_mapping = {}
    i = 1
    while ("SENSE_PORT" + str(i)) in os.environ:
        port_mapping[int(os.environ["SENSE_PORT" + str(i)])] = int(os.environ["SENSE_PORT" + str(i) + "_PUBLIC"])
        i = i + 1
    port_mapping["22"] = os.environ["SENSE_SSH_PORT_PUBLIC"]
    return {
            "public_dns": os.environ["SENSE_DNS_PUBLIC"],
            "public_port_mapping": port_mapping,
            "ssh_password": os.environ["SENSE_SSH_PASSWORD"],
            "project_ip": os.environ["SENSE_PROJECT_IP"]
           }

def launch_workers(n, size, engine="sense-ipython-engine", startup_script="", startup_code="", env={}):
    """Launches worker dashboards.
    
    Parameters
    ----------
    n: int 
        The number of dashboards to launch.
    size: str 
        The dashboard size, for example "small", "medium" or "large".
    engine: str, optional 
        The name of the `npm <http://npmjs.org>` module to use as the engine.
    startup_script: str, optional 
        The name of a Python source file the dashboard should execute as soon as it starts up.
    startup_code: str, optional 
        Python code the dashboard should execute as soon as it starts up. Don't provide both startup_script and startup_code.
    env: dict, optional 
        Environment variables to set in the dashboard.

    Returns
    -------
    list
        A list of dicts of the form described in `the REST API. <http://help.senseplatform.com/api/rest#retrieve-dashboard>`
    """

    if os.environ["SENSE_MASTER_ID"] != "":
        raise RuntimeError("launch_workers should only be called from master dashboards.")

    request_body = {
        "name": "Worker for IPython dashboard" + os.environ["SENSE_DASHBOARD_ID"],
        "engine": engine,
        "size": size,
        "startup_script": startup_script,
        "startup_code": startup_code,
        "env": env,
        "master_id": os.environ["SENSE_DASHBOARD_ID"]
    }
    url = API_URL + "/users/" + os.environ["SENSE_OWNER_ID"] + "/projects/" + os.environ["SENSE_PROJECT_ID"] + "/dashboards"
    auth = get_auth()
    
    # The n launch requests are done concurrently in a thread pool for lower
    # latency.
    def launch_worker(i):
        return requests.post(url, data=request_body, auth=(auth["user"], auth["pass"])).json()
    pool = futures.ThreadPoolExecutor(thread_pool_size)
    responses = [pool.submit(launch_worker, i) for i in xrange(n)]
    return map(lambda x: x.result(), futures.wait(responses)[0])

def get_workers():
    """
    Get current dashboard, as well as the master.

    Returns
    -------
    list
        A list of dicts of the form described in `the REST API. <http://help.senseplatform.com/api/rest#retrieve-dashboard>`
    """
    if os.environ["SENSE_MASTER_ID"] == "":
        master_id = os.environ["SENSE_DASHBOARD_ID"]
    else:
        master_id = os.environ["SENSE_MASTER_ID"]
    
    master_id = int(master_id)
    auth = get_auth()
    url = API_URL + "/users/" + os.environ["SENSE_OWNER_ID"] + "/projects/" + os.environ["SENSE_PROJECT_ID"] + "/dashboards"
    response = requests.get(url, auth=(auth["user"], auth["pass"])).json()
    
    def is_worker(dashboard):
        return dashboard["status"] == "running" and (dashboard["id"] == master_id or dashboard["master_id"] == master_id)
    
    return filter(is_worker, response)    

def stop_workers(*ids):
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
        ids_ = filter(lambda x: x["master_id"] is not None, get_workers())
        stop_workers(*ids_)
    else:
        base_url = API_URL + "/users/" + os.environ["SENSE_OWNER_ID"] + "/projects/" + os.environ["SENSE_PROJECT_ID"] + "/dashboards";
        request_body = {"status": "stopped"}
        auth = get_auth()
        
        # The stop requests are done concurrently in a thread pool for lower latency.
        def stop_worker(id):
            return requests.patch(base_url + str(id), data=request_body, auth=(auth["user"], auth["pass"])).json()

        pool = futures.ThreadPoolExecutor(thread_pool_size)
        responses = [pool.submit(stop_worker, id) for id in ids]
        return map(lambda x: x.result(), futures.wait(responses)[0])
