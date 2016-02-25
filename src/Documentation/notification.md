Notification configuration
==========================
Monitoring utilities such as ```ipmi_mon``` or ```storage_mon``` notifies the endpoint configured in notify.json when there is an reportable event.


# JSON Keys

## ```notify```
- Array of the endpoints where alerts needs to be sent.
- Current supported endpoints are "SnmpTrap", "HTTPPost", "ExecHandler".
- At least one supported endpoint needs to be present in "notify" array.

## ```notification_endpoints```
 - Contains configuration details of  possible notification endpoints.
 - Config information is looked up by code as ```notification_endpoints.${endpoint}```, For example HTTPPost configuration details would be looked up as ```notification_endpoints.HTTPPost```.
 - All methods in ```notify``` array needs to have valid config object in ```notification_endpoints```.
 - A valid configuration would be similar to [```notify.json```](../conf/notify.json).


# Extending current implementation
   Each notification mode has  implementation in ```lib/gs_ocpmon```. ```ipmi_mon```, ```storage_mon``` just calls class method "notify" from those implementations.
   You can refer any of the other implementations for method signature..etc.
