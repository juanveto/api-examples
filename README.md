# CANedge API Examples - Process Log File Data (Local, S3)

This project includes Python examples of how to process data from your [CANedge](https://www.csselectronics.com/) CAN/LIN data loggers.

---
## Features
```
For most use cases we recommend to start with the below examples:
- data-processing: List specific log files, load them and DBC decode the data (local, S3)

For some use cases the below examples may be useful:
- asammdf-basics: Examples of using the asammdf API for processing MDF4 data
- s3-basics: Examples of how to download, upload or list specific objects on your server
- s3-events: Using AWS Lambda (for event based data processing)
- s3-events: Using MinIO notifications (for event based data processing)
- misc: Example of automating the use of the MDF4 converters
- misc: Basic e-mail sender function

```

---

## Installation
We recommend to install Python 3.7 for Windows ([32 bit](https://www.python.org/ftp/python/3.7.9/python-3.7.9.exe)/[64 bit](https://www.python.org/ftp/python/3.7.9/python-3.7.9-amd64.exe)) or [Linux](https://www.python.org/downloads/release/python-379/).

Next, intall script dependencies via the `requirements.txt` in each folder:  
  ``pip install -r requirements.txt``

### Platforms supported
The below platforms are currently supported for the `mdf_iter`, `canedge_browser` and `can_decoder` modules:

- Linux: x86-64 (Python 3.5, 3.6, 3.7, 3.8)
- Windows: x86-64 (Python 3.7, 3.8), x86 (Python 3.7, 3.8)

---

## Sample data (MDF4 & DBC)
You can download J1939 MDF4 & DBC samples from the [CANedge Intro docs](https://canlogger.csselectronics.com/canedge-getting-started/log-file-tools/). 

The `data-processing/` folder also includes ready-to-test J1939 log files and a demo DBC.

---

## Usage info
- Some example folders contain their own `README.md` files for extra information
- These example scripts are designed to be minimal and to help you get started - not for production
- Some S3 scripts use hardcoded credentials to ease testing - for production see e.g. [this guide](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html)

---

## Which API modules to use?
There are many ways that you can work with the data from your CANedge devices. Most automation use cases involve fetching data from a specific device and time period - and DBC decoding this into a dataframe for further processing. Here, we recommend to look at the examples from the `data-processing/` folder. These examples use our custom modules designed for use with the CANedge: The [mdf_iter](https://pypi.org/project/mdf-iter/) (for loading MDF4 data), the [canedge_browser](https://github.com/CSS-Electronics/canedge_browser) (for fetching specific data locally or from S3) and the [can_decoder](https://github.com/CSS-Electronics/can_decoder) (for DBC decoding the data). In combination, these modules serve to support most use cases.

If you have needs that are not covered by these modules, you can check out the other examples using the asammdf API, the AWS/MinIO S3 API and our MDF4 converters.

If in doubt, [contact us](https://www.csselectronics.com/screen/page/can-bus-logger-contact) for sparring.

---
## About the CANedge

For details on installation and how to get started, see the documentation:
- [CANedge Docs](https://www.csselectronics.com/screen/page/can-logger-resources)  
- [CANedge1 Product Page](https://www.csselectronics.com/screen/product/can-logger-sd-canedge1/language/en)  
- [CANedge2 Product Page](https://www.csselectronics.com/screen/product/can-lin-logger-wifi-canedge2/language/en)  

---
## Contribution & support
Feature suggestions, pull requests or questions are welcome!

You can contact us at CSS Electronics below:  
- [www.csselectronics.com](https://www.csselectronics.com)  
- [Contact form](https://www.csselectronics.com/screen/page/can-bus-logger-contact)  
