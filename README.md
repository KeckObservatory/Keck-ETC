## W.M. Keck Observatory Exposure Time Calculator

*Developed by Keaton Blair and Sherry Yeh, 2021*

*Liscensing info. goes here*

### About Program

This project contains the source code for the server running the W.M.K.O. exposure time calculator.

The calculator GUI can be found at <https://www2.keck.hawaii.edu/not-yet-released>, while the API can be found at <https://www2.keck.hawaii.edu/not-yet-released-again>. Usage instructions for the GUI and API can be found on their relevant pages.

The remainder of this document contains instructions to download, install, and run the server on your own local machine.

*Acknowledgments to gemini & others go here*

### Installation

To install this program, clone this directory using `git clone https://github.com/Keaton-WMKO/etc-prototype.git`.

Next, ensure that all requirments are met. To install requirements, use
```
pip install astropy
pip install scipy
```
if using `pip`, or
```
conda install astropy
```
if using `conda`.

### Requirements

- Bash v?
- Python 3.8?

- Python Libraries:
    - numpy v?
    - astropy v?
    - scipy v?s

### Running 

To run the server, run the executable file `wmko-etc` with argument `start`. To see usage, use `--help`. An example is shown below:

```
$   ./wmko-etc start gui

Starting gui server on port 5006

$   ./wmko-etc start api -p 8080

Starting api server on port 8080

$   ./wmko-etc status

Checking status of server * on port *
Running 1 API server on port 8080
Running 1 GUI server on port 5006

$   ./wmko-etc -h

Usage: ./etc {start,stop,status,restart} [-f] [-p port_number] [-h]
    Positional arguments: {start,stop,status,restart}
        start           Begin running a server, requires additional argument 'gui' or 'api'
        stop            Stop running a server, requires additional argument 'gui' or 'api'
        status          Print server status, accepts optional argument 'gui' or 'api'
        restart         Restart a server, requires additional argument 'gui' or 'api'
    Optional arguments:
        -p, --port      Specifies port for server
        -f, --force     Force kill running server, use with 'stop' or 'restart'
        -h, --help      Displays this message
```
