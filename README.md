# Sense Package for IPython

Utility functions to help get the most out of [IPython](http://ipython.org) 
on [Sense.](https://www.senseplatform.com)

[![Build Status](https://travis-ci.org/SensePlatform/sense-ipython-module.png)](https://travis-ci.org/SensePlatform/sense-ipython-module)

This package complements Sense's [REST API](https://help.senseplatform.com/api/rest)
by wrapping and simplifying the actions that are most commonly used within 
dashboards, such as launching and stopping workers.  This package remains relatively
basic and is meant primarily to support packages that implement 
higher-level approaches to cluster computing in Python.

## Installation

This package is preinstalled on Sense. To install it elsewhere, use

```
python setup.py install
```

## Example

This example launches several worker dashboards and communicates with them 
using [ZMQ](https://learning-0mq-with-pyzmq.readthedocs.org/en/latest/).
over the project's secure private network.

It illustrates installing packages, getting network information, launching dashboards,
and communicating securely over the project's private network.


```python
import time
import sense
sense.install('zmq')
import zmq

# Create server
context = zmq.Context()
socket = context.socket(zmq.REP)
address = "tcp://" + sense.network_info().project_ip + ":5000"
socket.bind(address)

worker_code = """
import os
import zmq
import sense

# Connect to the master
context = zmq.Context()
print "Connecting to master..."
socket = context.socket(zmq.REQ)
socket.connect(os.environ['SERVER'])

# Send a message
socket.send("Sense is so easy!")

# Wait for a reply
message = socket.recv()
print "Received reply: ", message
"""

workers = sense.launch_workers(n=3, size="small", startup_code=worker_code, env={"SERVER": address})

# Listen for worker messages.
for i in range(0, 3)
    #  Wait for next request from client
    message = socket.recv()
    print "Received request: ", message
    time.sleep (1)  
    socket.send("I agree.")

```

# API

## Package Management

### sense.install(package_name, flags=[], arguments={}):

Installs the named package to the current project using [pip](http://www.pip-installer.org).

The `install` function uses [pip](www.pip-installer.org) to install packages 
to the user account. On Sense, that means it installs them to the project, 
and future dashboards launched from the same project, such as workers, can import them. For 
example:

```
sense.install("zmq")
```

You can use the following options to customize the installation:

* `flags`: A list of strings to pass to pip as flags. For example, 
  `["U", "use-mirrors"]` would translate to the command-line flags
  `-U --use-mirrors`.
* `arguments`: A dict containing arguments to pass to pip. For example,
  `{"d": "./downloads", "mirrors": "http://URL"}` would translate to
  the command-line arguments `-d ./downloads --mirrors=http://URL`.


## Networking

### sense.get_network()

Gets the current dashboard's networking information.


The `get_network()` function returns useful contact information for the
dashboard in the form of a dict with keys `public_dns`,
`public_port_mapping`, `ssh_password` and `project_ip`. `public_port_mapping`
is a dict whose  keys and values are integers. This information is
useful for ssh'ing into the dashboard and for communicating between dashboards
in a cluster.

Every project has it's own virtual private network.  The project IP address
is only accessible to other dashboards in the same project. Any port can be 
accessed via the project IP address.

The public DNS, public port mapping and SSH password tell you how the
current dashboard can be contacted from outside the project. Only
ports that are keys of public_port_mapping can be accessed via the
public DNS.  If you run a service on port 3000, for example, it  can be accessed
from outside the dashboard on the public DNS on port
`public_port_mapping[3000]`.

Contacting dashboards via their public DNS gives better network performance 
than the project IP but requires attention to security.

If required, you can ssh to dashboards using the public DNS on port
`public_port_mapping[22]`, using username `sense` and the `ssh_password`.

## Cluster Management

In Sense, clusters are groups of dashboards with the same master dashboard.  Worker
dashboards multiplex their output to the master dashboard and are cleaned up
automatically when a master dashboard is stopped or fails.  These features
make it dramatically easier to manage, monitor and debug distributed applications
on Sense.

### sense.launch_workers(n, size="small", engine="sense-ipython-engine", startup_script="", startup_code="", env={})
    
Launch a worker dashboard into the cluster.

The parameters of `launch_workers` are:

* `n`: The number of workers to launch.
* `size` (optional): The size of the workers, for example "small", "medium" or "large".
* `engine` (optional): The name of the [npm](http://npmjs.org) module to use
  as the engine. Defaults to "sense-ipython-engine", but workers can run other
  engines too.
* `startup_script` (optional): A Python script file that the worker should
  execute on launch. 
* `startup_code` (optional): Python code that the worker should execute on 
  launch. `startup_script` has precedence over `startup_code`.
* `env` (optional): A map containing environment variables that should be
  set on the workers. This is generally the preferred way to a master's contact
  information information to workers.

The return value is a list of dicts. Each dict describes one of the workers
you just launched and contains keys such as `id`, `engine`, `status`, etc. 
The full format is documented [here.](http://help.senseplatform.com/api/rest#retrieve-dashboard)

### sense.list_workers()

Get list of workers in cluster.

This function returns a list of dicts like those returned by `launch_workers()`. 
One dict is returned for each dashboard that either shares a master with the current
dashboard.

### sense.stop_workers(*ids)

Stop workers.

You stop workers with `stop_workers(id1, id2, ...)`.
To stop all workers that share a master with the current dashboard, and
reduce the cluster to a single interactive master dashboard, you can
simply call `stop_workers()`. The return value is the same kind of 
object as that returned by `get_workers()` and `launch_workers()`.

## Rich Dashboard Output

IPython provides its own [rich display system](http://nbviewer.ipython.org/urls/raw.github.com/ipython/ipython/1.x/examples/notebooks/Part%205%20-%20Rich%20Display%20System.ipynb), 
so unlike its [R](http://github.com/SensePlatform/sense-r-module) 
and [JavaScript](http://github.com/SensePlatform/sense-js-module) 
counterparts this package does not provide any rich output functions.

Just use IPython's rich display system to display HTML, images and more
in a dashboard.

## REST API

Sense has a powerful REST API that gives you complete programmatic control
over virtually every aspect of Sense.

### sense.get_auth()

Get authentication information for REST API.

Most REST calls require authentication.  The `get_auth()` function 
returns the basic authentication information in a dict with keys `user` and 
`password`. You can then supply this information your HTTP client of choice, such 
as the  Python package `requests` to make authenticated REST API calls. 

```python
import sense
import requests
auth = sense.get_auth()
url = "https://api.senseplatform.com/users/" + os.environ["SENSE_OWNER_ID"] + "/projects/" + os.environ["SENSE_PROJECT_ID"]
response = requests.get(url, auth=(auth["user"], auth["password"])).json()
```

The environmental variables used in this example are common to all dashboards,
across all engines, and are documented [here](https://docs.senseplatform.com/getting-started/#environment).

By default `get_auth()` uses `SENSE_API_TOKEN` for authentication. This
token restricts access to the project the dashboard is executing in. For access across projects,
you can pass in credentials manually or set `SENSE_USERNAME` and `SENSE_PASSWORD` in the environment.
To better understand these options, you can read the 
<a href="http://help.senseplatform.com/security">Project Security</a> documentation.

# Support

* Email: support@senseplatform.com
* Google Group: https://groups.google.com/forum/?fromgroups#!forum/sense-users
* IRC: `#senseplatform` on `irc.freenode.net`

# License

MIT
