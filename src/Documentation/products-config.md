Product Configuration
=====================

Configures set of properties such as
- Where to store last seen SEL event marker.
- What will be mapping from SEL Event Data 3 to ECC dimm location.

DMI system-product-name, or baseboard-product-name will used as the
key (i.e ```dmidecode -s system-product-name```)

# JSON Key
system-product-name is used as key to look up config detail, regex lookup like "DCS12*" is also possible, if two different products are equivalent one can use another product name as the value.

For example
```
"R1000*" : "DCS12*"
```

## JSON Subkeys

### ```server_model```
The value of this key is shorthand notation of the server model.

### ```last_seen_marker_method```
ipmitool uses either fru inventory data field or a magic sel
record to keep track of last seen SEL entry. Value of this key
should be either "sel" or "fru".

### ```fru_stash_cfg```
if the last section was configured as fru, additional details
about where to stash ```last_seen marker```(ref: ```ipmitool fru edit```)
Possible valid values:
```
	"fru_stash_cfg" :{
	"field": "board_extra_1",
    "sec" :     "b",
	"pos":      4
    }

	"fru_stash_cfg" :{
    	"field":    "chassis_extra_1",
    "sect":     "c",
    "pos":      3
  }
```

### ```ecc_dimm_location_map```
Simple map of event data 3 (8bits) to DIMM Location.
Refer to [System Event Log Troublshooting Guide](http://download.intel.com/support/motherboards/server/sb/s1400_s4600_systemeventlog_troubleshootingguide_r1.pdf) page 76,77 for additional details. Quanta  Hardware differs slightly from intel boards.

```
SEL Event Data 3 individual bits map as
Quanta:    CPU [7:6]  Channel [5:3] DIMM [2:0]
Intel derived:   CPU [7:5]  Channel [4:3] DIMM [2:0]
Dimm numbering starts with 0 on Quanta and 1 on intel derived boards.
```
