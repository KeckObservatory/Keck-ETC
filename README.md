## W. M. Keck Observatory Exposure Time Calculator

### About

This project contains the source code for the server running the W.M.K.O. exposure time calculator.

The calculator GUI can be found at [www2.keck.hawaii.edu/software/keckETC](https://www2.keck.hawaii.edu/software/keckETC/), while the API can be found at [www2.keck.hawaii.edu/software/keckETC/getETC2.php](https://www2.keck.hawaii.edu/software/keckETC/getETC2.php). Usage instructions for the GUI and API can be found on their relevant web pages.

The remainder of this document contains instructions to download, install, and run the API server and GUI on your local machine.

### Installation

To install this program, clone this directory using `git clone https://github.com/KeckObservatory/Keck-ETC.git`.

Next, ensure that all requirments are met. To install the necessary python packages, use
```
pip install astropy
pip install scipy
```
if using `pip`, or
```
conda install astropy
conda install scipy
```
if using `conda`.

### Requirements

The following are minimum system requirements necessary to run the API server and view the GUI.

- Bash 4
- Python 3.7

- Python libraries:
    - astropy 4
    - scipy 1.6

- Browsers:
    - Chrome 51
    - Firefox 54
    - Safari 10
    - Edge 15

### Execution

To run the API server, run the executable file `etc-api` with argument `start`. To see usage, use `--help`. An example is shown below:

```
$   ./etc-api start

Succesfully started server on port 8080 with pid 52104

$   ./etc-api start -p 5000

Succesfully started server on port 5000 with pid 52106

$   ./etc-api status

Running 2 servers on ports 5000, 8080 with pids 52106, 52104

$   ./etc-api stop

Succesfully terminated server on port 8080

$   ./etc-api -h

Usage: etc-api {start,stop,status,restart,test} [-fhvw] [-p port_number] [-l log_file]
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
        
For more information, visit https://github.com/KeckObservatory/Keck-ETC
```

Once the API server is running on `localhost:8080`, open the file `index.html` in a browser to view the GUI.

### Modifications

The exposure time calculator is designed to be easily modified. For example, to add a new instrument to the calculator, create a new directory under `instruments` and add the appropriate files. An example of a new instrument directory tree is shown here:

```
calculator/
└── instruments/
    └── new_instrument/
        ├── instrument_config.yaml
        └── throughput_files
            ├── file_1.fits
            ├── ...
            └── file_n.fits
```

After making any changes, such as editing configuration files or source templates, run the shell script `etc-validate` to ensure that your changes will function as intended.

```
$   ./etc-validate

Inspecting calculator/instruments/new_instrument/instrument_config.yaml
Error: missing required value dark_current for spectroscopic mode in file calculator/instruments/new_instrument/instrument_config.yaml

$   nano calculator/instruments/new_instrument/instrument_config.yaml

$   ./etc-validate

Inspecting calculator/instruments/new_instrument/instrument_config.yaml
No configuration problems discovered
```

### Acknowledgements

Atmospheric transmission and emission data from Gemini Observatory, [gemini.edu/observing/telescopes-and-sites/sites](https://www.gemini.edu/observing/telescopes-and-sites/sites)

Sky background generated using ATRAN (Lord, S. D., 1992, NASA Technical Memorandum 103957)

Source SEDs from STScI `pysynphot` package, [pysynphot.readthedocs.io/en/latest/spectrum.html](https://pysynphot.readthedocs.io/en/latest/spectrum.html)

Instrument specs and throughput data from W. M. Keck Observatory, [www2.keck.hawaii.edu/inst](https://www2.keck.hawaii.edu/inst)

### Contact

This project was developed by Keaton Blair and Sherry Yeh at the W. M. Keck Observatory.

[To submit a bug report or feature request, click here.](https://github.com/KeckObservatory/Keck-ETC/issues/new/choose)

For other feedback or information, contact Sherry Yeh at [syeh@keck.hawaii.edu](mailto:syeh@keck.hawaii.edu).

### License

Copyright (c) 2022, W. M. Keck Observatory

All rights reserved.

This project is licensed under the BSD-style license found in the LICENSE file.