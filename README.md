# Utilities for [IPython](http://ipython.org) on [Sense](https://senseplatform.com)

[![Build Status](https://travis-ci.org/SensePlatform/sense-ipython-module.png)](https://travis-ci.org/SensePlatform/sense-ipython-module)

This package complements Sense's [REST API](https://help.senseplatform.com/api/rest)
by wrapping and simplifying some of the most common operations, such as launching and 
stopping worker dashboards. Its primary purpose is to support other packages that implement 
higher-level approaches to cluster computing.

## Installation

This package is preinstalled on Sense. You can import it with

```python
import sense
```

To install it elsewhere use

```bash
pip install sense
```

## Example

This example launches several worker dashboards and communicates with them 
using [ZeroMQ](https://learning-0mq-with-pyzmq.readthedocs.org/en/latest/)
over the project's private network.


```python
import time
import sense

n_workers = 3

# Use 'install' to install package 'pyzmq' from PyPI to the project.
sense.install('pyzmq')
import zmq

# Create the ZeroMQ server.
context = zmq.Context()
socket = context.socket(zmq.REP)

# Use 'get_network_info' to find out the private IP address of the current
# dashboard in the project's virtual private network.
address = "tcp://" + sense.network_info()['project_ip'] + ":5000"
socket.bind(address)

# Define code the worker dashboards should execute on startup.
# Each worker will attempt to connect to the ZeroMQ server whose 
# address is stored in its 'SERVER' environment variable and then will send
# a message to the server.
worker_code = """
import os
# Because pyzmq was previously installed to the project, workers don't
# need to reinstall it.
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

# Use 'launch_workers' to start three small worker dashboards. The above
# code is sent to each, and the current dashboard's project IP address is
# stored in each worker's environment as 'SERVER', so each worker will contact
# the current dashboard.
workers = sense.launch_workers(n=n_workers, 
    size="small", 
    startup_code=worker_code, 
    env={"SERVER": address})

# Listen for worker messages.
for i in range(0, n_workers):
    #  Wait for next request from client
    message = socket.recv()
    print "Received request: ", message
    time.sleep (1)  
    socket.send("I agree.")

sense.stop_workers()
```

## API

### install

Installs a Python package to the project with [pip](http://www.pip-installer.org) 
using the [user scheme](http://docs.python.org/2/install/index.html#alternate-installation-the-user-scheme). 

```python
import sense
sense.install(package_name, flags=[], arguments={})
```

If you prefer, you can also install packages by running a shell command from 
IPython using the ! prefix:

```
!pip install pyzmq --user
```

Options:

* **flags**: A list of strings to pass to pip as flags. For example, 
  `["U", "use-mirrors"]` would translate to the command-line flags
  `-U --use-mirrors`.
* **arguments**: A dict containing arguments to pass to pip. For example,
  `{"d": "./downloads", "mirrors": "http://URL"}` would translate to
  the command-line arguments `-d ./downloads --mirrors=http://URL`.

Once installed, any of the project's dashboards can import the package.

### network_info

Returns the current dashboard's contact information 
in a dict with keys `public_dns`, `public_port_mapping`, `ssh_password` and 
`project_ip`.

```python
import sense
network_info = sense.network_info()
```

Every project has its own [virtual private network (VPN).](http://en.wikipedia.org/wiki/Virtual_private_network)
The project IP address is bound to the project VPN and is only accessible to 
other dashboards in the same project. The project VPN makes it easy to 
use cluster computing frameworks that lack built-in security features, 
such as [MPI](http://en.wikipedia.org/wiki/Message_Passing_Interface).

The public DNS hostname, public port mapping and SSH password describe how 
the current dashboard can be contacted from outside the project. The public 
port mapping is a dict whose  keys and values are integers. Only ports 
that are keys of the public port mapping can be accessed via the public DNS 
hostname.  If you run a service on port 3000, for example, it  can be accessed 
from anywhere on the internet on the public DNS hostname and port 
`public_port_mapping[3000]`.

If required, you can SSH to dashboards using the public DNS hostname and port
`public_port_mapping[22]` with username "sense" and the SSH password.

### launch_workers

Launches worker dashboards into the cluster. 

```python
import sense
 worker_info = sense.launch_workers(n, 
    size="small", 
    engine="sense-ipython-engine", 
    startup_script="", 
    startup_code="", 
    env={})
```    

In Sense, a cluster is a group of dashboards with the same master dashboard.  
Worker dashboards multiplex their outputs to the master and are cleaned up
automatically when the master is stopped or fails.  These features
make it easy to manage, monitor and debug distributed applications
on Sense.

The parameters are:

* **n**: The number of workers to launch.
* **size** (optional): The size of the workers, for example "small", "medium" or "large".
* **engine** (optional): The name of the [npm](http://npmjs.org) module to use
  as the engine. Defaults to "sense-ipython-engine", but workers can run other
  engines too.
* **startup_script** (optional): A script file that the worker should
  execute on launch. The path is relative to the project's home folder.
* **startup_code** (optional): Code that the worker should execute on 
  launch. If both are provided, startup_script has precedence over startup_code.
* **env** (optional): A dict containing environment variables that should be
  set on the workers before any code is executed. This is the preferred way 
  to send a master's contact information information to workers.

The return value is a list of dicts. Each dict describes one of the workers
that was launched and contains keys such as `"id"`, `"engine"`, `"status"`, etc. 
The full format is documented [here.](http://help.senseplatform.com/api/rest#retrieve-dashboard)

### list_workers

Returns information on the worker dashboards in the cluster in a 
list of dicts like those returned by launch_workers.

```python
import sense
worker_info = sense.list_workers()
```

### get_master

Returns information on the cluster's master dashboard in a dict like the ones returned by launch_workers.

```python
import sense
master_info = sense.get_master()
```

### stop_workers

Stops worker dashboards.

Dashboards' numerical IDs are available at key `id` in the dicts returned by 
list_workers and launch_workers. The return value is a dict of the same type.

```python
import sense

# To stop specific workers:
worker_info = sense.stop_workers(id1, id2, ...)

# To stop all workers in the cluster:
worker_info = sense.stop_workers()
```

### get_auth

Returns authentication information for the [REST API](https://help.senseplatform.com/api/rest)
as a dict with keys `"user"` and `"password"`.

Sense's REST API gives you complete programmatic 
control over virtually every aspect of Sense. Most REST calls require 
[Basic Authentication](http://docs.python-requests.org/en/latest/user/authentication/#basic-authentication).
 To make authenticated REST calls, supply 
the information returned by get_auth your HTTP client of choice, such as the 
Python [requests](http://docs.python-requests.org/) package. 

By default get_auth uses the environment variable SENSE_API_TOKEN for
authentication. This token restricts access to the current project. For access across projects, you can pass in credentials manually 
or set SENSE_USERNAME and SENSE_PASSWORD in the environment. To better 
understand these options, read the [Understanding Project Security](http://help.senseplatform.com/understanding-project-security)
documentation.

#### Authenticated REST Example

This example retrieves information about the current project:

```python
import sense
import requests
auth = sense.get_auth()
url = "https://api.senseplatform.com/users/" + os.environ["SENSE_OWNER_ID"] + \
   "/projects/" + os.environ["SENSE_PROJECT_ID"]
response = requests.get(url, auth=(auth["user"], auth["password"])).json()
```

The environment variables used in this example are common to all dashboards,
across all engines, and are documented [here](https://docs.senseplatform.com/getting-started/#environment).

## Rich Dashboard Output

IPython provides its own [rich display system](http://nbviewer.ipython.org/urls/raw.github.com/ipython/ipython/1.x/examples/notebooks/Part%205%20-%20Rich%20Display%20System.ipynb), 
so unlike its [R](http://github.com/SensePlatform/sense-r-module) 
and [JavaScript](http://github.com/SensePlatform/sense-js-module) 
counterparts this package does not provide any rich output functions. 
Use IPython's rich display system to display HTML, images and more in a dashboard.

# Support

* **Documentation**: http://help.senseplatform.com
* **Email**: support@senseplatform.com
* **Twitter**: https://twitter.com/senseplatform
* **Google Group**: https://groups.google.com/forum/?fromgroups#!forum/sense-users
* **IRC**: `#senseplatform` on `irc.freenode.net`

# License

MIT
