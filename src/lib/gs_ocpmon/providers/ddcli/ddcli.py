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


from gs_ocpmon.platform import Plat
from gs_ocpmon.utils import misc, ExeWrapper



'''
The -health command shows the overall health status of a selected Nytro WarpDrive card and its components. If
any alert exists, this command shows the component causing the alert along with further information. The -health
command Overall Health output possiblities include the following:
 - GOOD. The Nytro WarpDrive card is operating correctly. All operations are supported.
 - WARNING. The Nytro WarpDrive card is approaching failure. This output appears because of a decreased Life
Left value or an increased Temperature value outside the set threshold.
 - ERROR. The Nytro WarpDrive card is not operating. No operations can be performed.
The -health command Life Left output possibilities include percentages between 0 percent and 100 percent.
Zero percent indicates an expired Nytro WarpDrive card warranty.
'''

logger = logging.getLogger("root")


class Ddcli(ExeWrapper):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        super(Ddcli, self).__init__("ddcli")

        self.alert_map = misc.json_file_to_dict(self.rootdir + "/conf/ddcli_alert_map.json")
        self.notify_map = misc.json_file_to_dict(self.rootdir  + "/conf/notify.json")

        self.stash_file = Plat.get_tempdir() + "/ocpmon_ddcli-stash.json"
        # baseid for ddcli alert, no real significance other than should cont conflict other alert ids
        # Also recieving end might have rules(or workflows) to process these ids.

        self.base_alert_id=5900

    return_codes = misc.enum(
        NO_CHANGE_IN_HEALTH = 0,
        DIDNT_PASS_THRESHOLD= 1,
        NOT_LOWER_LOW       = 2,
        INFORMATIONAL       = 3,
        WARNING             = 4,
        CRITICAL            = 5,
        UNKNOWN_VALUE       = 6,)

    def get_health(self):

        #cmd_def = self.exe["commands"]["health"]
        result = self.runcmd("health")

        output = dict()

        # SSD Life Left (PE Cycles)             100        (%)
        lifeleft_re = re.compile(r"""SSD Life Left \(PE Cycles\)\s+(\d+)\s+\(%\)$""", re.M)
        output["lifeleft"] = []
        for i, pctlife in enumerate(re.findall(lifeleft_re, result)):
            logger.debug("pct life left [%d]: %s" % (i, pctlife))
            output["lifeleft"].append(pctlife)

        # Backup Rail Monitor          : GOOD
        brm_re = re.compile(r"""Backup Rail Monitor\s+:\s+(\w+)$""", re.M)
        for brm_status in re.findall(brm_re, result):
            logger.debug("backup rail monitor: {0}".format(brm_status))
            output["backup_rail_monitor"] = brm_status

        #Warranty Remaining       : 100 %
        warr_re = re.compile(r"""Warranty Remaining\s+:\s+(\w+) %$""", re.M)
        for warr_status in re.findall(warr_re, result):
            logger.debug("warranty remaining: {0}".format(warr_status))
            output["warranty_remaining"] = warr_status

        #Overall Health           : GOOD
        health_re = re.compile(r"""Overall Health\s+:\s+(\w+)$""", re.M)
        for health_status in re.findall(health_re, result):
            logger.info("overall health: {0}".format(health_status))
            output["overall_health"] = health_status

        return output
    def load_stash(self):
        try:
            return misc.json_file_to_dict(self.stash_file)
        except IOError as e:
            logger.info("IOError loading stash file (server was probably rebooted): {0}".format(e))
            # return 100% healthy report as baseline
            logger.info("Defaulting stash to 100% healthy report")
            return self.exe["commands"]["health"]["default_stash"]

    def store_stash(self, stash):
        try:
            misc.dict_to_json_file(stash, self.stash_file)
        except IOError as e:
            logger.critical("IOError saving stash file: {0}".format(e))


    def check_health(self):
        stash = self.load_stash()
        health = self.get_health()
        self.store_stash(health)

        if health == stash:
            logger.debug("No change in health output detected - exiting")
            return self.return_codes.NO_CHANGE_IN_HEALTH

        for m_name, m_def in self.exe["commands"]["health"]["monitors"].items():
            camel = misc.to_camel_text(m_def["label"])
            direction = "Asserted"  # TODO add deassert functionality?
            message = ""
            # check if we have changes since last stash
            m_was = stash[m_name]
            m_now = health[m_name]
            if m_now == m_was:
                continue

            if m_def["type"] == "threshold" and isinstance(m_now, list):
                m_was = [int(x) for x in m_was]
                m_now = [int(x) for x in m_now]

            logger.debug("Change in health output detected. {0} was {1} but is now {2}".format(m_def["label"], m_was, m_now))

            if m_def["type"] == "status":
                if m_now in self.exe["status_value_map"]:
                    sev = self.exe["status_value_map"][m_now]
                    message = "{0} changed state from {1} to {2}".format(m_def["label"], m_was, m_now)
                else:
                    logger.critical("Unknown value for {0}: {1}".format(m_name, m_now))
                    message = "unknownStatusCritical Unknown status value for {0}: {1}".format(m_name, m_now)
                    vars_list = [9999, "unknownStatusCritical", "Asserted"]
                    self.send_alert(message, 5, vars_list)
                    return self.return_codes.UNKNOWN_VALUE

            elif m_def["type"] == "threshold":
                # lookup up sev in threshold tables
                if isinstance(m_now, list):
                    min_m_now = min(m_now)
                    min_m_was = min(m_was)
                    if min_m_now == min_m_was:
                        logger.debug("New minumum for {0} is not lower than previous minimum - exiting".format(m_def["label"]))
                        return self.return_codes.NOT_LOWER_LOW
                    else:
                        thresh = min_m_now
                else:
                    thresh = int(m_now)
                    min_m_was = int(m_was)

                thresholds = self.exe["thresholds"].items()
                rev_thresh_map = dict((v, lvl) for (lvl, lst) in thresholds for v in lst)

                all_t = sorted(rev_thresh_map.keys(), reverse=True)
                crossed = False
                for t in all_t:
                    #logger.debug("testing %s <= %s < %s -> %s" % (thresh, t, min_m_was, thresh <= t < min_m_was))
                    if thresh <= t < min_m_was:
                        sev = rev_thresh_map[t]
                        crossed = True
                        continue
                    elif crossed:
                        logger.debug("Crossed threshold of {0} for {1} from {2} to {3}".format(t, sev, min_m_was, thresh))
                        message = "{0} crossed {1} alert threshold of {2} from {3} to {4}".format(m_def["label"], sev, t, min_m_was, thresh)
                        break

                if not crossed:
                    logger.debug("New value for {0} didnt cross a new threshold - exiting".format(m_def["label"]))
                    return self.return_codes.DIDNT_PASS_THRESHOLD

            alert_key = "{0}{1} {2}".format(camel, sev, direction)
            logger.debug("looking up alert id map for {0}".format(alert_key))
            if alert_key in self.alert_map:
                alert = self.alert_map[alert_key]
                message = "{0} {1}".format(camel, message)
                vars_list = [alert["id"], camel, direction]
                self.send_alert(message, 5, vars_list)
                if sev == 'Informational':
                    return self.return_codes.INFORMATIONAL
                elif sev == 'Warning':
                    return self.return_codes.WARNING
                elif sev == 'Critical':
                    return self.return_codes.CRITICAL
            else:
                logger.critical("failed to find alert_id for [{0}]".format(alert_key))
                message = "missingAlertIdCritical failed to find alert_id for key {0}".format(alert_key)
                vars_list = [9999, "missingAlertIdCritical", "Asserted"]
                self.send_alert(message, 5, vars_list)

    def send_alert(self, message, severity, vars_list=None):
        message = "gs-ocpmon::nytro::" + message
        alert_id = vars_list[0]
        logger.warning("sending alert %d: %s" % (alert_id, message))
        for endpoint in self.notify_map["notify"] :
            endpoint = str (endpoint)
            mod = __import__("gs_ocpmon.providers.notifiers."+endpoint.lower(), fromlist=[endpoint])
            klass = getattr(mod,endpoint)
            rc = klass.notify(message, severity,vars_list=vars_list)

            if rc != 0:
                logger.critical("Bad return code from "+ endpoint)

    def get_health_raw(self):
        result = self.runcmd("health")
        return result

    def warranty_log(self):
        log = ""
        for cmd_name in ["listall", "list", "health", "showvpd", "paniclog"]:
            result = self.runcmd(cmd_name)
            log += result

        return log

    def gen_alert_table(self):
        alert_id = self.base_alert_id
        outdict = dict()
        outtsv = ""
        for m_name, m_def in self.exe["commands"]["health"]["monitors"].items():
            camel = misc.to_camel_text(m_def["label"])

            if m_def["type"] == "threshold":
                things = self.exe["ddcli"]["thresholds"].keys()
            else:
                things = self.exe["ddcli"]["status_value_map"].values()

            for key in things:
                key = camel + key
                key_a = key + ' Asserted'
                key_d = key + ' Deasserted'
                outdict[key_a] = {"camel": key, "id": alert_id}
                outdict[key_d] = {"camel": key, "id": alert_id + 1}
                outtsv += "{0}\t{1}\t{2}\n".format(alert_id, key, 'assert')
                outtsv += "{0}\t{1}\t{2}\n".format(alert_id+1, key, 'deassert')
                alert_id += 2

        return outdict, outtsv
