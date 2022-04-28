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

The exposure time calculator is designed to be easily modified. For example, to add a new instrument to the calculator, create a new directory under `calculator/instruments` and add the appropriate files. An example of a new instrument directory tree is shown here:

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

All of the configurable paramaters for the ETC are explicitly stated in `yaml` files in the `/calculator/` directory tree. To change any one of these parameters, edit the appropriate files in a text editor, then run `./etc-validate`. Finally, run `./etc-api restart` to run the API server using your new changes.

The GUI is designed to recieve all important parameters from the API. However, it may be helpful to modify the tooltips and instructions displayed by the GUI and API. These are stored in the folder `src/static`.
```
src/
└── static/
    ├── api_instructions.txt
    ├── gui_instructions.txt
    └── mouseover_text.json
```
To change the tooltip associated with any input, edit `mouseover_text.json` and add a key-value pair, following the format
```
    "INPUT ELEMENT ID": "Message to be displayed on mouseover of information icon"
```

### Troubleshooting

#### Front End

If you're experiencing errors using the GUI, open the console to view the error messages. Double check that the API is running and the GUI is making API calls to the correct web address. If necessary, you may need to edit file `/src/script.js`, changing
```
318    // Send fetch request and return data
319    const request = await fetch('http://localhost:8080', {
320        method: 'POST',
321        headers: {'Content-Type': 'text/plain'},
322        body: query
323    });
```
to match the location of the API server in your implementation.
```
319    const request = await fetch('API_ADDRESS_HERE', {
```

To determine whether a bug is being caused by the front end or back end, you can access the API directly by visiting [www2.keck.hawaii.edu/inst/etc/getETC2.php](https://www2.keck.hawaii.edu/inst/etc/getETC2.php), or [localhost:8080](http://localhost:8080) if running the API locally. If the unexpected behavior is present when making API calls, the bug you're experiencing is being caused by the back end.

[To report a bug you've discovered or request a feature, click here.](https://github.com/KeckObservatory/Keck-ETC/issues/new/choose)

#### Back End

If you're experiencing errors using the API, first run the shell script
```
$ ./etc-api status
```
then try restarting the API with `./etc-api restart`.

Run the command `./etc-api test` to verify that your installation matches [github](https://github.com/KeckObservatory/Keck-ETC) and that you have installed the required dependencies.

If you have made any changes to the ETC, run the shell script
```
$ ./etc-validate
```
to test the format and contents of all configuration and source files.

For more detailed information, view the log file, positioned by default at `/log/etc.log`. To log warnings as well as errors, use the `--warn` flag.
```
$ ./etc-api start -w
```
*Important: The script `etc-api` reads the contents of the log file to determine the API status. If you edit or delete the log file, stop the API first or you will have to manually kill the process later. If you use a non-standard location for your log file, you must always use the `--log` flag.*
```
$ ./etc-api status -l PATH_TO_LOG_FILE
```

[If you've discovered a bug, click here to report it.](https://github.com/KeckObservatory/Keck-ETC/issues/new/choose)

[If you've made changes to the ETC and wish to contribute, submit a pull request here](https://github.com/KeckObservatory/Keck-ETC/pulls) or [contact us.](https://github.com/KeckObservatory/Keck-ETC#contact)

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