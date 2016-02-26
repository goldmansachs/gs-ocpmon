GS ocpmon Utility
=================

[![][license img]][license]

GS ocpmon is a Hardware Monitoring and Alerting agent for OCP
Platform. Designed to produce standardized Alerts on OCP platform with
System Event Log(SEL) being primary source. In addition to SEL log
handling, includes utilities to monitor Seagate Nytro WarpDrives.



# Key feature and Goals
- Define consistent event numbers and associated text payload
information, this masks differences between different various OCP vendors.
- Multiple reporting mechanisms(SNMP trap, HTTP Post, Shell script Hooks).



# Supported OCP-Platforms
Has been tested on below platforms
- Intel Decathlete
- QuantaGrid D51B-1U (2S Intel Grantley Winterfell Motherboard)

# Runtime Requirments
- Red Hat Enterprise Linux 6.x
- Python : 2.x
- __ipmitool__ - Was tested on (Version 1.8.15), In RHEL environments available as ipmitool package(Also available at http://ipmitool.sourceforge.net/).
- __ddcli__ - Can be downloaded from Seagate.com or Platform Integrator.


# How to use it.
- If ```src``` present in distribution, it will be the top level directory containing useful code.
- Schedule execution of  ```bin/ipmi_mon``` to report on SEL events and
```bin/storage_mon``` to report on Storage events.
- Modify ```conf/notify.json``` as required to configure notification end
points.
- Modify ```conf/products.json``` as required to configure platform specific details.
- Additional details on how to customize ```ipmi_mon``` and ```storage_mon```  using above mentioned configs is available
in [Documentation](Documentation/).

# Licensing
GS ocpmon is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE-2.0.txt) for the full license text.


# Getting Help (issues ,link,dev-mailing list)

# Contributing to GS ocpmon
We currently do all development in an internal Subversion repository and are not prepared to take external contributions. However, we watch the issue tracker for bug reports and feature requests.

# Known Issues
For every platform we have tested, we provide an alert map(in ```conf/${platform}_alert_map.json```) which provides an unique identifier and text description for SEL events. Alert maps provided may not cover entire possible set, in those cases alerts are sent with identifier 9999.
