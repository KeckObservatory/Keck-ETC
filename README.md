## W. M. Keck Observatory Exposure Time Calculator

Copyright (c) 2022, W. M. Keck Observatory

All rights reserved.

This project is licensed under the BSD-style license found in the LICENSE file in the root directory of this source tree.

### About Program

This project contains the source code for the server running the W.M.K.O. exposure time calculator.

The calculator GUI can be found at <https://www2.keck.hawaii.edu/software/keckETC/>, while the API can be found at <https://www2.keck.hawaii.edu/software/keckETC/getETC2.php>. Usage instructions for the GUI and API can be found on their relevant pages.

The remainder of this document contains instructions to download, install, and run the API server and GUI on your own local machine.

*Acknowledgments to gemini & others go here*

### Installation

To install this program, clone this directory using `git clone https://github.com/KeckObservatory/Keck-ETC.git`.

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

To run the server, run the executable file `etc-api` with argument `start`. To see usage, use `--help`. An example is shown below:

```
$   ./etc-api start

Starting server on port 8080
Succesfully started server on port 8080 with pid 52104

$   ./etc-api start -p 5000

Starting server on port 5000
Succesfully started server on port 5000 with pid 52106

$   ./etc-api status

Checking status of server on port *
Running 2 servers on ports 5000, 8080

$   ./etc-api stop

Succesfully terminated server on port 8080

$   ./etc-api -h

Usage: $PROGRAM_DIR/etc-api {start,stop,status,restart,test} [-f] [-h] [-v] [-w] [-p port_number] [-l log_file]
    Positional arguments: {start,stop,status,restart,test}
        start           Begin running the server
        stop            Stop running the server
        status          Print server status
        restart         Restart the server
        test            Verify successful program installation
    Optional arguments:
        -p, --port      Specifies port for server, defaults to 8080
        -f, --force     Force kill running server, use with 'stop' or 'restart'
        -l, --log       Path to logfile, defaults to ./log/etc.log
        -w, --warn      Log python warnings, ignored by default
        -v, --version   Display program version
        -h, --help      Displays this message
```

### Contact Us

This project was developed by Keaton Blair and Sherry Yeh at the W. M. Keck Observatory.

[To submit a bug report or feature request, click here.](https://github.com/KeckObservatory/Keck-ETC/issues/new/choose)

For other feedback or information, contact Sherry Yeh at [syeh@keck.hawaii.edu](mailto:syeh@keck.hawaii.edu).