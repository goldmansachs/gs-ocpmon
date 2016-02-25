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

import os
import re
import time
import logging

from gs_ocpmon.utils import misc
from gs_ocpmon.utils import ExeWrapper
from gs_ocpmon.platform import Plat

logger = logging.getLogger("root")

class Ipmitool(ExeWrapper):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        super(Ipmitool, self).__init__("ipmitool")
        product_name = Plat().get_baseboard_product_name()
        self.product_map = misc.json_file_to_dict(self.rootdir +"/conf/products.json")

        product_name = re.sub("\s",'',product_name.strip())

        product_name_key = misc.get_key_for_nearest_match(product_name,self.product_map.keys())
        product_name_key_final = misc.get_equivalent_key_with_config(product_name,product_name_key,self.product_map)
        try:
            self.server_model = str(self.product_map[product_name_key_final]["server_model"])
            self.dimm_table = self.product_map[product_name_key_final]["ecc_dimm_location_map"]
            self.handles_post_errors = False
            self.fru_stash_cfg = self.product_map[product_name_key_final]["fru_stash_cfg"]
            self.get_last_seen = getattr(self,"get_last_seen_{0}".format(self.product_map[product_name_key_final]["last_seen_marker_method"]))
            self.set_last_seen = getattr(self,"set_last_seen_{0}".format(self.product_map[product_name_key_final]["last_seen_marker_method"]))
        except Exception as e:
            logger.info("Missing configurations  in the Products config file : {0}".format(e))

        self.sensor_map = misc.json_file_to_dict(self.rootdir  + "/conf/{0}_sensor_map.json".format(self.server_model))
        self.alert_map = misc.json_file_to_dict(self.rootdir + "/conf/{0}_alert_map.json".format(self.server_model))
        self.post_error_map = misc.json_file_to_dict(self.rootdir + "/conf/{0}_post_error_map.json".format(self.server_model))
        self.notify_map = misc.json_file_to_dict(self.rootdir  + "/conf/notify.json")


        # We use a magic record as a book mark in the event log,
        # All new events since the last magic record will be processed
        # Following is the various fields in the record
        # {EvM Revision} 0x02 is not a valid version in spec
        # {Sensor Type} 0x00 is a reserved sensor type code
        #    Rest of the data used really magic (0x55802397)
        # {Sensor Num} 0x55
        # {Event Dir/Type} 0x00
        # {Event  Data  0}
        # {Event Data 1}
        # {Event   Data 2}
        #
        self.magic_rec="0x02 0x00 0x55 0x00 0x80 0x23 0x97"

        # generate an sdr dump if one doesnt exist
        sdr_loc = self.get_sdr_location()
        if not os.path.isfile(sdr_loc):
            self.sdr_dump(sdr_loc)

    @staticmethod
    def str_to_date(timestr):
        return time.strptime(timestr, '%m/%d/%Y %H:%M:%S')

    def get_last_seen_fru(self):
        # get last seen message
        last_seen = self.read_fru_stash()

        logger.debug("Retreived last_seen of {0}".format(last_seen))

        # 44b 04/02/2014 14:39:15
        match = re.match(r"""^(\d+) (\d\d/\d\d/\d\d\d\d \d\d:\d\d:\d\d)$""", last_seen)

        if not match:
            raise ValueError("couldnt match a date in last_seen data (FRU)")

        (e_id, e_dt_str) = match.groups()
        e_id = int(e_id)

        e_dt = self.str_to_date(e_dt_str)

        return last_seen, e_id, e_dt, e_dt_str


    def set_last_seen_fru(self, cnt, ts):
        new_seen = "{0} {1}".format(cnt, ts)
        self.write_fru_stash(0, self.fru_stash_cfg["sect"], self.fru_stash_cfg["pos"], new_seen)

    def get_last_seen_sel(self):
        events = self.get_sel_list_csv()
        magic_rec_id = -1
        for event in reversed(events):
            curr_id = int(event["id"], 16)
            if event["sensor"] == "Reserved #0x55":  # magic
                magic_rec_id = curr_id
                logger.debug("found magic sel record with decimal id %d", curr_id)
            if curr_id == magic_rec_id:
                e_dt_str = "{0} {1}".format(event["date"], event["time"])
                e_dt = self.str_to_date(e_dt_str)
                last_seen = "%d %s" % (curr_id, e_dt_str)
                logger.debug("last_seen SEL record is #%d at %s", curr_id, e_dt_str)
                return last_seen, curr_id, e_dt, e_dt_str

        # magic_rec is first record??
        if magic_rec_id != -1:
            logger.critical("Magic SEL record was first record - should never get here")
            self.set_last_seen(None, None)
        else:
            #raise ValueError("couldnt find magic record in SEL")
            logger.critical("No magic SEL record")
            self.set_last_seen(None, None)

    def set_last_seen_sel(self, cnt, ts):
        import tempfile
        with(tempfile.NamedTemporaryFile(prefix="gs_ocpmon_tmp_sel")) as tmpfile:
            tmpfile.write(self.magic_rec)
            tmpfile.flush()
            tmp_filename = tmpfile.name
            result = self.runcmd("event_file", tmp_filename)
            return result


    event_data_enrichers = {

        3000: lambda x,dimm_tables : dimm_tables[x[-2:]]

    }

    def check_sel(self):

        trapped_ok = True
        sel_info = self.get_sel_info()
        logger.debug(sel_info)
        sel_last_add_time = sel_info["last_add_time"]
        sel_entries = int(sel_info["entries"])
        sel_last_del = sel_info["last_del_time"]

        if sel_last_del == "Not Available":
            sel_last_del = "01/01/1970 00:00:00"

        new_seen = "{0} {1}".format(sel_entries, sel_last_add_time)


        try:
            last_seen, e_id, e_dt, e_dt_str = self.get_last_seen()
        except ValueError as vex:

            # send a "new server/mainboard" alert?
            # should run sensor check
            # remember to write last seen
            logger.warn(vex.message + " - is this a new server/mainboard?")
            self.set_last_seen(sel_entries, sel_last_add_time)
            self.post_error_check()
            return

        new_e_dt = self.str_to_date(sel_last_add_time)
        last_del = self.str_to_date(sel_last_del)

        count = -1

        # check for log clear?
        if e_id > sel_entries:
            logger.info("We have less SEL events than before ({0} < {1}) - presuming log clear".format(e_id, sel_entries))
            count = 0

        if last_del > e_dt:
            logger.info("SEL last clear date is newer the last seen message ({0} > {1}) - presuming log clear".format(sel_last_del, e_dt_str))
            count = 0

        # check for last update + entries
        if e_id < sel_entries:
            logger.info("We have more SEL events than before: {0} > {1}".format(sel_entries, e_id))
            if count != 0:
                count = sel_entries - e_id

        if new_e_dt > e_dt:
            logger.info("Detected newer entry/s in SEL: {0} > {1}".format(sel_last_add_time, e_dt_str))
            if count != 0:
                count = sel_entries - e_id

        logger.debug("after all checks, count is %d" % count)


        if count >= 0:
            # get delta messages and do trap/s
            events = self.get_sel_list_csv_last(count)

            for event in events:

                # magic SEL record for last_seen
                if event["sensor"] == "Reserved #0x55":
                    continue

                ev_get = self.get_sel_get(event['id'])
                event["data"] = ev_get.get("event_data")

                if not event["data"]:
                    logger.critical("sel_get of 'Event Data' field did not return a value")

                #  {u'direction': 'Asserted', u'description': 'Lower Non-critical going low ', u'data': None,
                #  u'time': '12:11:13', u'date': '04/24/2014', u'sensor': 'Voltage #0xdd', u'id': '5'}
                # handle events with no direction (default to assert)
                if event["direction"] is None:
                    event["direction"] = 'Asserted'

                # handle empty events
                if event["description"] is "":
                    event["description"] = 'No description'

                # lookup "Unknown" sensors
                if event["sensor"].startswith("Unknown"):
                    match = re.match(r""".*? (#0x[0-9a-f]{2})""", event["sensor"])
                    if match:
                        sensor_hexid = match.groups(1)
                        for sensor in self.sensor_map.keys():
                            if sensor.endswith(sensor_hexid):
                                event["sensor"] = sensor
                                logger.debug("matched Unknown sensor as: " + sensor)
                                continue

                # lookup sensor
                if event["sensor"] in self.sensor_map:
                    sensor = self.sensor_map[event["sensor"]]
                    # lookup alert
                    akey = "%s %s #0x%02x %s %s" %(
                        sensor["entity_id"],
                        sensor["sensor_type"],
                        int(sensor["sensor_id_num"], 16),
                        event["description"],
                        event["direction"])
                    logger.debug("Looking up alert ID for key: " + akey)
                    if akey in self.alert_map:
                        alert = self.alert_map[akey]

                        message = "gs-ocpmon::ipmi::{0} {1} {2} {3}".format(
                            alert["camel"],
                            sensor["sensor_id"],
                            event["description"],
                            event["direction"]
                        )

                        if alert["id"] in Ipmitool.event_data_enrichers and event["data"]:
                            enricher = Ipmitool.event_data_enrichers[ alert["id"]]
                            richtext = enricher(event["data"], self.dimm_table)
			    logging.info("enriching {0} with {1}".format(message, richtext))
                            message += " " + richtext

                        # vars_list '1009,watchdog2TimerInterrupt,System Board,IPMI Watchdog'
                        vars_list = [str(v) for v in (alert["id"], alert["camel"], sensor["entity_id"], sensor["sensor_id"])]

                    else:
                        # we know the sensor but not the alert
                        message = "gs-ocpmon::ipmi::unknownEvent {0} {1} {2}".format(
                            event["sensor"],
                            event["description"],
                            event["direction"]
                        )
                        logger.debug("event description is '{0}'".format(event["description"]))
                        vars_list = [str(v) for v in (9999, event["sensor"])]
                else:
                    # ok - we dont even know about this sensor
                    message = "gs-ocpmon::ipmi::unknownSensor {0} {1} {2}".format(
                        event["sensor"],
                        event["description"],
                        event["direction"]
                    )
                    vars_list = [str(v) for v in (9999, event["sensor"])]

                if event["data"] is not None:
                    message += " [{0}]".format(event["data"])

                logger.info("new SEL event: {0}".format(message))
                # send a trap
                for endpoint in self.notify_map["notify"] :
                    endpoint = str (endpoint)
                    mod = __import__("gs_ocpmon.providers.notifiers."+endpoint.lower(), fromlist=[endpoint])
                    klass = getattr(mod,endpoint)
                    rc = klass.notify(message,5,vars_list=vars_list)
                    if rc != 0:
                        trapped_ok = False
                        logger.critical("Failed to execute "+ endpoint +" - all new events will be re-processed next execution")

        # store id for last seen message
        if trapped_ok and last_seen != new_seen:
            self.set_last_seen(sel_entries, sel_last_add_time)


    def post_error_check(self):

        if not self.handles_post_errors:
            return

        sel = self.get_sel_list_csv()

        last_seen_post_id = 0
        post_events = list()
        # scan SEL in reverse for reboots and post errors
        sel.reverse()


        for event in sel:
            # lookup sensor
            if event["sensor"] not in self.sensor_map:
                logger.warn("Failed to lookup sensor [{0}] in post_error_check".format(event["sensor"]))
                continue
            sensor = self.sensor_map[event["sensor"]]

            # lookup alert
            akey = "%s %s #0x%02x %s %s" % (
                sensor["entity_id"],
                sensor["sensor_type"],
                int(sensor["sensor_id_num"], 16),
                event["description"],
                event["direction"])

            if akey not in self.alert_map:
                logger.warn("Failed to lookup alert key [{0}] in post_error_check".format(akey))
                continue
            alert = self.alert_map[akey]

            event_id = int(event["id"], 16)

            if alert["camel"] == "systemFirmwareErrorUnknownError":
                last_seen_post_id = event_id
                logger.info("POST error detected at %d", last_seen_post_id)
                evt = {"event_id": event_id, "alert": alert}
                post_events.append(evt)
            elif alert["camel"] == "systemEventOemSystemBootEvent":
                event_id = event_id
                logger.debug("Boot event detected at %d", event_id)
                if event_id > last_seen_post_id:
                    logger.debug("No POST events since last reboot")
                    return
                else:
                    break

        for evt in post_events:
            # get post code
            logger.debug("Running 'sel get {0}' to get raw data field".format(evt["event_id"]))
            record = self.get_sel_get(evt["event_id"])
            alert = evt["alert"]
            if record and record["event_data"]:
                flipped = re.sub(r'[a-f0-9]{2}([a-f0-9]{2})([a-f0-9]{2})', r'\2\1', record["event_data"])
                flipped = flipped.upper()
                # post code lookup
                if flipped:
                    if flipped in self.post_error_map:
                        actual_post = self.post_error_map[flipped]
                        logger.debug("Actual POST error: {0}".format(actual_post))
                        logger.debug("POST alert is: {0}".format(alert))
                        message = "gs-ocpmon::ipmi::{0} {1} ({2})".format(
                            alert["camel"],
                            actual_post["message"],
                            actual_post["response"],
                        )
                        vars_list = [str(v) for v in (alert["id"], alert["camel"])]
                        for endpoint in self.notify_map["notify"] :
                            endpoint = str (endpoint)
                            mod = __import__("gs_ocpmon.providers.notifiers."+endpoint.lower(), fromlist=[endpoint])
                            klass = getattr(mod,endpoint)
                            rc = klass.notify(message,5,vars_list=vars_list)

                            if rc != 0:
                                logger.critical("Failed to execute notification")
                    else:
                        logger.warn("Couldnt find [{0}] in post error map".format(flipped))
                else:
                    logger.warn("failed to match post error regex in SEL raw data field [{0}]".format(record["event_data"]))
            else:
                logger.error("Failed to get raw data for alert {0}".format(evt))

    def get_sel_info(self):
        return self.cmd_colon_sep("sel_info")

    def get_sdr_location(self):  #
        return "{0}/{1}.sdr.dump".format(Plat.get_tempdir(), self.server_model)

    #  ipmitool sdr dump S2600GZ.sdr.dump
    def sdr_dump(self, filename):
        result = self.runcmd("sdr_dump", filename)
        return result

    def get_sel_elist_csv(self):
        retval = self.cmd_comma_sep("sel_elist_csv")
        return retval

    def get_sel_list_csv(self):
        retval = self.cmd_comma_sep("sel_list_csv")
        return retval

    def get_sel_list_csv_raw(self):
        result = self.runcmd("sel_list_csv")
        return result.stdout

    def get_sel_elist_csv_last(self, count):
        sdr_loc = self.get_sdr_location()
        args = (sdr_loc, count)
        retval = self.cmd_comma_sep("sel_elist_csv_last", args=args)
        return retval

    def get_sel_get(self, eid=1):
        if isinstance(eid, int):
            hex_eid = hex(eid)
        elif isinstance(eid, basestring):
            if eid.startswith('0x'):
                hex_eid = eid
            else:
                hex_eid = '0x' + eid
        else:
            raise RuntimeError

        sdr_loc = self.get_sdr_location()
        args = (sdr_loc, hex_eid)
        retval = self.cmd_colon_sep("sel_get", args=args)
        return retval

    def get_sel_list_csv_last(self, count):
        sdr_loc = self.get_sdr_location()
        args = (sdr_loc, count)
        retval = self.cmd_comma_sep("sel_list_csv_last", args=args)
        return retval

    def get_fru_print(self, fruid=0):
        retval = self.cmd_colon_sep("fru_print", args=fruid)
        return retval

    def read_fru_stash(self, fruid=0):
        fru = self.get_fru_print(fruid)
        return fru[self.fru_stash_cfg["field"]]

    def write_fru_stash(self, fruid, section, index, string):
        args = (fruid, section, index, string)
        result = self.runcmd("fru_edit", args=args)
        return result
