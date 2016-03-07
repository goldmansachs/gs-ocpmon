GS ocpmon Utility
=================

[![][license img]][license]

GS ocpmon is a Hardware Monitoring and Alerting agent for OCP
Platform. Designed to produce standardized Alerts on OCP platform with
System Event Log(SEL) being primary source. In addition to SEL log
handling, includes utilities to monitor Seagate Nytro WarpDrives.


# Key feature and Goals
- Define consistent event numbers and associated text payload information, this masks differences between different various OCP vendors.
- Multiple reporting mechanisms(SNMP trap, HTTP Post, Shell script Hooks).


# Supported OCP-Platforms
Has been tested on below platforms
- Intel Decathlete
- QuantaGrid D51B-1U (2S Intel Grantley Winterfell Motherboard)

# Runtime Requirements
- Red Hat Enterprise Linux 6.x
- Python : 2.x
- __ipmitool__ - Was tested on (Version 1.8.15), In RHEL environments available as [ipmitool](http://ipmitool.sourceforge.net/) package.
- __ddcli__ - Can be downloaded from Seagate.com or Platform Integrator.


# How to use it
- ```src``` directory will be the top level directory containing useful code.
- ```src``` can be renamed to any preferred top level directory name.
- Schedule execution of  ```${top_level_dir}/bin/ipmi_mon``` to report on SEL events and
```${top_level_dir}/bin/nytro_mon``` to report on Storage events.
- Modify ```${top_level_dir}/conf/notify.json``` as required to configure notification end
points.
- Modify ```${top_level_dir}/conf/products.json``` as required to configure platform specific details.
- Additional details on how to customize ```ipmi_mon``` and ```nytro_mon```  using above mentioned configs is available
in [Documentation](src/Documentation/).

# Licensing
GS ocpmon is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE-2.0.txt) for the full license text.


# Getting Help
Issues can be reported via issue tracker.

# Contributing to GS ocpmon
We currently do all development in an internal Subversion repository and are not prepared to take external contributions. However, we watch the issue tracker for bug reports and feature requests.

# Known Issues
For every platform we have tested, we provide an alert map(in ```src/conf/${platform}_alert_map.json```) which provides an unique identifier and text description for SEL events. Alert maps provided may not cover entire possible set, in those cases alerts are sent with identifier 9999.



[license]:LICENSE-2.0.txt
[license img]:https://img.shields.io/badge/License-Apache%202-blue.svg
