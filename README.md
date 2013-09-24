# Package 'sense' for IPython

Utility functions to help you get the most out of [IPython](http://ipython.org) 
on [Sense.](https://www.senseplatform.com)

[![Build Status](https://travis-ci.org/SensePlatform/sense-ipython-module.png)](https://travis-ci.org/SensePlatform/sense-ipython-module)

Sense's comprehensive [REST API](https://docs.senseplatform.com/api/rest) 
lets you control most aspects of Sense, including your dashboards.
This package complements the REST API by wrapping and simplifying the
actions that are most useful from a dashboard.

## Installation

This package is preinstalled on Sense. To install it elsewhere, use

```
python setup.py install
```

## Usage

### Installing packages

The `install` function uses [pip](www.pip-installer.org) to install packages 
to the user account. On Sense, that means it installs them to the project, 
and future dashboards launched from the same project can import them. For 
example:

```
import sense
sense.install("beautifulsoup")
```

You can use the following options to customize the installation:

* `flags`: A list of strings to pass to pip as flags. For example, 
  `["U", "use-mirrors"]` would translate to the command-line flags
  `-U --use-mirrors`.
* `arguments`: A dict containing arguments to pass to pip. For example,
  `{"d": "./downloads", "mirrors": "http://URL"}` would translate to
  the command-line arguments `-d ./downloads --mirrors=http://URL`.

### Networking

The `networkInfo()` function returns useful contact information for the
dashboard in the form of a dict with keys `public_dns`,
`public_port_mapping`, `ssh_password` and `project_ip`. public_port_mapping
is a dict whose  keys and values are integers. This information is
useful for ssh'ing into the dashboard and for combining dashboards
into clusters.

The project IP address is only accessible to other dashboards in the
same project, via the project VPN. Any port can be accessed via the
project IP address.

The public DNS, public port mapping and SSH password tell you how the
current dashboard can be contacted from outside the project. Only
ports that are keys of public_port_mapping can be accessed via  the
public DNS. However, contacting dashboards via the public DNS  gives
better network performance than the project IP.

If you run a service on port 3000, for example, it  can be accessed
from outside the dashboard on the public DNS on port
``public_port_mapping[3000]``.

The dashboard's SSH daemon is listening on the public DNS on port
``public_port_mapping[22]``, and will accept the SSH password.

### Worker management

This module makes it easy to start, stop and manage worker dashboards.
Say you want to launch two medium worker dashboards that, when they
start up, import a module called `distributedFramework` and use it to
contact the current dashboard and get their share of the work. You
can use the `launchWorkers` function:

```python
import sense
import pickle
info = pickle.dumps(sense.networkInfo())
code = """
import distributedFramework
distributedFramework.contactMaster(%s)
"""%info
sense.launchWorkers(2, "medium", startupCode=code)
```

The parameters of launchWorkers are:

* `n`: The number of workers to launch.
* `size`: The size of the workers, for example "small", "medium" or "large".
* `engine` (optional): The name of the [npm](http://npmjs.org) module to use
  as the engine. Defaults to "sense-ipython-engine", but workers can run other
  engines too.
* `startupScript` (optional): A Python script file that the worker should
  execute on launch. 
* `startupCode` (optional): Python code that the worker should execute on 
  launch. `startupScript` and `startupCode` are mutually exclusive.
* `env` (optional): A map containing environment variables that should be
  set on the workers. 

The return value is a list of dicts. Each dict describes one of the workers
you just launched and contains keys such as `id`, `engine`, `status`, etc. 
The full format is documented [here.](http://help.senseplatform.com/api/rest#retrieve-dashboard)

If you want to get information about the current dashboard's cluster,
you can call `sense.getWorkers()`. This function returns a list of dicts
like those returned by `launchWorkers`. One dict is returned for each
dashboard that either shares a master with the current dashboard, or is
the master of the current dashboard.

To stop particular workers, you can call `sense.stopWorkers(id1, id2, ...)`.
To stop all workers that share a master with the current dashboard, and
reduce the cluster to a single interactive master dashboard, you can
simply call `sense.stopWorkers()`. The return value is the same kind of 
object as that returned by `getWorkers` and `launchWorkers`.

### Rich output

IPython provides its own [rich display system](http://nbviewer.ipython.org/urls/raw.github.com/ipython/ipython/1.x/examples/notebooks/Part%205%20-%20Rich%20Display%20System.ipynb), 
so unlike its [R](http://github.com/SensePlatform/sense-r-module) 
and [JavaScript](http://github.com/SensePlatform/sense-js-module) 
counterparts this package does not provide any rich output functions.

Just use IPython's rich display system to display HTML, images and more
in a dashboard.

### Using the REST API

The Sense REST API lets you take a wide range of actions that aren't
supported by this package. To use it, you'll first need to call
`getAuth()` to get basic authentication information in a dict with
keys 'user' and 'pass'. You can then  supply this information to the
Python package `requests` to make REST API calls. For example, to
find information about the current project, you could do

```python
import sense
sense.authInfo = getAuth()
url = "https://api.senseplatform.com/users/" + os.environ["SENSE_OWNER_ID"] + "/projects/" + os.environ["SENSE_PROJECT_ID"]
response = requests.get(url, auth=(auth["user"], auth["pass"])).json()
```

The environment variables used in that code are common to all dashboards,
across all engines, and are documented [here](https://docs.senseplatform.com/getting-started/#environment).

## Support

* Email: support@senseplatform.com
* Google Group: https://groups.google.com/forum/?fromgroups#!forum/sense-users
* IRC: `#senseplatform` on `irc.freenode.net`