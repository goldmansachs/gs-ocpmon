# (C) Copyright 2016, Goldman Sachs. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging
import re
import socket

from ._platform import Base
from gs_ocpmon.utils import ExeWrapper

logger = logging.getLogger("root")


class DmiDecode(ExeWrapper):

    def __init__(self):
        super(DmiDecode, self).__init__("dmidecode", {
            "name": "dmidecode",
            "path": "",
            "ld_library_path": "",
            "cmdline": "/usr/sbin/dmidecode",
            "commands": {
                "by_keyword": {
                    "args": "--string %s",
                    "label": "Get DMI field by keyword",
                    "type": "exitcode"
                }
            }
        })

    def get_baseboard_manufacturer(self):
        return self.runcmd("by_keyword", "baseboard-manufacturer")

    def get_baseboard_product_name(self):
        return self.runcmd("by_keyword", "system-product-name")

    def get_baseboard_version(self):
        return self.runcmd("by_keyword", "baseboard-version")

    def get_chassis_asset_tag(self):
        return self.runcmd("by_keyword", "chassis-asset-tag")

    def get_chassis_serial_number(self):
        return self.runcmd("by_keyword", "chassis-serial-number")


class Linux(DmiDecode, Base):
    # requires root - should raise if not root

    default_snmptrap_port = socket.getservbyname('snmptrap')
    default_snmpd_conf_file = "/etc/snmp/snmpd.conf"

    def get_system_trapsinks(self, snmpd_conf_file=default_snmpd_conf_file, snmptrap_port=default_snmptrap_port):

        # trapsink trapsink.company.com privateComm 1234
        trapsink_re = re.compile(r"""^trapsink\s+(\S+)\s+([\S+]+)(?:\s+(\d+))?""")

        for line in open(snmpd_conf_file):
            match = trapsink_re.match(line)
            if match:
                if match.group(3):
                    snmptrap_port = int(match.group(3))

                return {
                    "hostname": match.group(1),
                    "community": match.group(2),
                    "port": snmptrap_port
                }

        raise RuntimeError("failed to find trapsink entry in {0}".format(snmpd_conf_file))
