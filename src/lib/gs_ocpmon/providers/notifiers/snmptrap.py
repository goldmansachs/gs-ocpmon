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
import shlex
import socket
import os
import sys
import time
import subprocess as sub


from gs_ocpmon.platform import Plat
from gs_ocpmon.utils import misc

logger = logging.getLogger("root")


class SnmpTrap(object):
    @staticmethod
    def load_config(configFile):
        try:
            return misc.json_file_to_dict(configFile)
        except IOError as e:
            logger.info("IOError loading Config file : {0}".format(e))
            print "IOError loading Config File"

    @classmethod
    def notify(cls, message, severity, alertgroup='', alerttype='snmp', installer='',
                 category='', platform='UNIX', division='', bu='', vars_list=None):
        '''
        -s severity (0=test/temp,1=auto, 2=ops(warn), 3=ops(minor), 4=ops(major),5=ops(critical)
        '''
        _plat = Plat()
        root_module = sys.modules[cls.__module__.split('.')[0]].__file__
        rootdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(root_module))))
        config_file = rootdir+"/conf/notify.json"

        if os.path.exists(config_file):
            config_dict = cls.load_config(config_file)
            try:
                traphost = config_dict['notification_endpoints'][cls.__name__]['traphost']
            except:
                traphost = _plat.get_system_trapsinks()["hostname"]
	    finally:
            	logger.error("Traphost not specified in notify.json OR Host-Snmp Configuration File , Agent cannot send Snmptrap Messages")
            try:
                community = config_dict['notification_endpoints'][cls.__name__]['community']
            except KeyError:
                community = "public"
            try:
                generic_trap = config_dict['notification_endpoints'][cls.__name__]['genericTrap']
            except KeyError:
                generic_trap = "6"
            try:
                enterprise_oid = config_dict['notification_endpoints'][cls.__name__]['enterpriseOid']
                specific_trap = config_dict['notification_endpoints'][cls.__name__]['specificTrap']
            except KeyError:
                logger.info("There is no \"enterpriseOid\" or \"specificTrap\"  key in the config file",)
        else:
            raise RuntimeError( "No configured SNMP-Trap")
        uptime= time.time() / 60
        host = socket.gethostname()
        host_ip = socket.gethostbyname(socket.gethostname())
        #oid = "sysDescr.0"
        oid = "1.3.6.1.2.1.1.1.0"
        if vars_list:
            vars_str = ','.join(str(x) for x in vars_list)

        alert_message = "Severity:{severity},Alerttype:{alerttype},Host:{host},Platform:{platform},Message:{message} %{vars_str}".format(**locals())
        print("alert_message : " + alert_message)
        logger.debug(locals())
        command = """snmptrap -v 1 -c {community} {traphost} {enterprise_oid} {host_ip} {generic_trap} {specific_trap} {uptime} {oid} s '{alert_message}'""".format(**locals())
        logger.info("running {0}".format(command))

        shlex_cmd = shlex.split(command.encode('utf-8'))
        proc = sub.Popen(shlex_cmd, stdout=sub.PIPE, stderr=sub.PIPE, env=os.environ.copy())
        (cmd_out, cmd_err) = proc.communicate()
        rc = proc.returncode
        logger.info("sendtrap returncode = {0}".format(rc))
        if rc != 0:
            logger.critical("sendtrap failed:\n\tcommand: {0}\n\treturn code:{1}\n\tstderr: {2}".format(command, rc, cmd_err))

        return rc
