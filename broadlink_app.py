"""AppDaemon App For use with Broadlink. With this app, all Broadlinks on the same network  can be used to control device
requirements:
- AD 4.0
- python 3.6 minimum
- pip3 install broadlink

apps.yaml parameters:
| - local_ip (optional, default None): The local IP of the system running AD. Only important in a docker container
| - broadlinks: (not optional): A dictionay definition of the name and mac address of each broadlink device
| - mac: (not optional) the mac address from the broadlink device
| - friendly_name (optional, default broadlink name)
| - entity_domain (optional, default sensor): The domain to be used when defining the entities to be created
| - service_domain (optional, default broadlink): The domain from the services
| - namespace (optional, default default): The namespace in which the entities and services are created
| - learn_time (optional, default 5): the time that AD listens for a data packet to return
| - use_sensor_for_temperature: (optional, default False): A dictionay definition of the name and update frequency for a temperature sensor
| - update_frequence (optional, default 60): the frequency with which the temperature attribute or sensor will be updated
| - name: (optional, default sensor.broadlink_name_temperature) the name for the temperature sensor
| - friendly_name (optional, default broadlink_name_temperature) friendly name for the temperature sensor
| - Unit_of_measurement (optional, default C) unit of measurement for the temperature sensor
| - use_temp_as_attribute: (optional, default True) set the temperature as attribute from the broadlink device
| - base64 (optional): A dictionay definition of names and ir codes to be used, encoded as base64
| - lirc (optional): A dictionay definition of names and ir codes to be used, encoded as lirc
| - pronto (optional): A diction aydefinition of names and ir codes to be used, encoded as pronto
| - hex (optional): A dictionay definition of names and ir codes to be used, encoded as hex
| - example config can be seen below:
| - 
| - broadlink_app:
| -     class: BroadlinkApp
| -     module: broadlink_app
| -     broadlinks:
| -         living_room:
| -             mac: xx:xx:xx:xx:xx:xx
| -             namespace: hass
| -             learn_time: 20
| -             entity_domain: sensor
| -             service_domain: living_room
| -             friendly_name: Broadlink living room
| -             use_temp_as_sensor: 
| -                 name: sensor.living_room_temperature
| -                 friendly_name: Living room temp
| -                 Unit_of_measurement: C 
| -                 update_frequency: 60 
| -             use_temp_as_attribute:
| -                 update_frequency: 60 
| -     base64:
| -         lg_tv_input: JgBQAAABKpQTEhITEjgSExITEhMSExITEzcSOBITEjgTNxI4EjgSOBI4EjgTEhI4EhMSExITEhMTEhITEjgSExI4EjgSOBI4EgAFLgABKkkSAA0FAAAAAAAAAAA=
| -     pronto:
| -         lg_tv_hdmi_1: 0000 006C 0022 0002 015B 00AD 0016 0016 0016 0016 0016 0041 0016 0016 0016 0016 0016 0016 0016 0016 0016 0016 0016 0041 0016 0041 0016 0016 0016 0041 0016 0041 0016 0041 0016 0041 0016 0041 0016 0016 0016 0041 0016 0041 0016 0041 0016 0016 0016 0016 0016 0041 0016 0041 0016 0041 0016 0016 0016 0016 0016 0016 0016 0041 0016 0041 0016 0016 0016 0016 0016 05F7 015B 0057 0016 0E6C
| -     hex:
| -         lg_tv_mute: 2600580000012a94121312131238121312131213121312131238133712131238133713371238123813371312121312381213121312131213121312381238121313371238123813371200052e00012a4a13000c670001294a12000d05
| -     lirc:
| -         philips_sb_audio_in: 2663 860 472 832 472 416 472 416 1332 1304 472 416 472 416 916 860 472 416 472 416 472 416 916 860 472 416 472 416 472 416 916 416 472 832 361

available services:
| - setup_broadlink, returns True or False
| - learn (expects entity_id="broadlink_entity_id") returns True or False
| - sweep_frequency (expects entity_id="broadlink_entity_id") returns True or False
| - cancel_sweep_frequency (expects entity_id="broadlink_entity_id") returns True or False
| - check_frequency (expects entity_id="broadlink_entity_id") returns frequency or False
| - find_rf_packet (expects entity_id="broadlink_entity_id") returns rf packet or False
| - check_data (expects entity_id="broadlink_entity_id") returns True or False
| - send_data (expects entity_id="broadlink_entity_id", data_packet="", protocol = "") returns True or False, data_packet can be a name you have set in the yaml or an actual data packet. protocol is optional
| - check_temperature (expects entity_id="broadlink_entity_id") returns temperature or False
| - check_sensors (expects entity_id="broadlink_entity_id") returns sensor data or False
"""

import adbase as ad
import broadlink
import re
import traceback
import base64
import binascii
import struct
import datetime

 
class Broadlink_App(ad.ADBase):
  
    def initialize(self): 
        self.adbase = self.get_ad_api()
        self.adbase.log("initialising started") 
        if "broadlinks" in self.args:
            self.broadlinks = self.args["broadlinks"]
        else:
            raise ValueError("No Devices given, please provide Broadlink Devices")
        
        self.entities = {} #to assist with HASS entities
        self.broadlinkObjects = {}#to store broadlink objects

        self.avail_services = ["setup_broadlink", "learn", "sweep_frequency", "cancel_sweep_frequency", "check_frequency",
                                "find_rf_packet", "check_data", "send_data", "check_temperature", "check_sensors"]

        # run in used here instead of direct call, so it doesn't
        # hold up AD from executing other apps due to delay
        self.adbase.run_in(self.setup_broadlink_cb, 0)

    def learn(self, entity_id):
        self._check_broadlink(entity_id)
        self.adbase.log(f"Broadlink device with Entity_ID {entity_id} Learning...")
        try:
            self.broadlinkObjects[entity_id].enter_learning()
            domain, name = entity_id.split(".")
            learn_time = self.get(self.args["broadlinks"][name]["learn_time"], 5)
            self.adbase.run_in(self.check_data_cb, learn_time, entity_id=entity_id)
            return True
        except:
            self.adbase.log("Logged an error in errorlog")
            self.adbase.error(traceback.format_exc())
            return False
    
    def sweep_frequency(self, entity_id):
        self._check_broadlink(entity_id)
        try:
            self.adbase.log(f"Broadlink device with Entity_ID {entity_id} Sweeping Frequency...")
            self.broadlinkObjects[entity_id].sweep_frequency()
            return True
        except:
            self.adbase.log("Logged an error in errorlog")
            self.adbase.error(traceback.format_exc())
            return False


    def cancel_sweep_frequency(self, entity_id):
        self._check_broadlink(entity_id)
        try:
            self.adbase.log(f"Cancelling Sweeping Frequency for Broadlink device with Entity_ID {entity_id}")
            self.broadlinkObjects[entity_id].cancel_sweep_frequency()
            return True
        except:
            self.adbase.log("Logged an error in errorlog")
            self.adbase.error(traceback.format_exc())
            return False
    
    def check_frequency(self, entity_id):
        self._check_broadlink(entity_id)
        try:
            return self.broadlinkObjects[entity_id].check_frequency()
        except:
            self.adbase.log("Logged an error in errorlog")
            self.adbase.error(traceback.format_exc())
            return False

    def find_rf_packet(self, entity_id):
        self._check_broadlink(entity_id)
        self.adbase.log(f"Broadlink device with Entity_ID {entity_id} searching for RF packet...")
        try:
            self.broadlinkObjects[entity_id].find_rf_packet()
            learn_time = self.get(self.args["broadlinks"][name]["learn_time"], 5)
            self.adbase.run_in(self.check_data_cb, learn_time, entity_id=entity_id)
            return True
        except:
            self.adbase.log("Logged an error in errorlog")
            self.adbase.error(traceback.format_exc())
            return False

    def check_data_cb(self, kwargs):
        self.check_data(kwargs["entity_id"])

    def check_data(self, entity_id):
        self._check_broadlink(entity_id)
        try:
            data_packet = self.broadlinkObjects[entity_id].check_data()

            if data_packet != None:
                data_packet = base64.b64encode(data_packet)
                #data_packet = data_packet.hex()
                
            self.adbase.log(f"data_packet = {data_packet}")
            
            return data_packet
        except:
            self.adbase.log("Logged an error in errorlog")
            self.adbase.error(traceback.format_exc())
            return False

    def send_data(self, entity_id, data_packet, protocol = None):
        self._check_broadlink(entity_id)

        if data_packet in self.args.get("base64", {}):
            data_packet = self.args["base64"][data_packet]
            protocol = "base64"
        
        elif data_packet in self.args.get("pronto", {}):
            data_packet = self.args["pronto"][data_packet]
            protocol = "pronto"
        
        elif data_packet in self.args.get("hex", {}):
            data_packet = self.args["hex"][data_packet]
            protocol = "hex"
        
        elif data_packet in self.args.get("lirc", {}):
            data_packet = self.args["lirc"][data_packet]
            protocol = "lirc"
        
        else: # at this point, auto check what codec is used
            if protocol == None:
                if " " in data_packet: # its either pronto/lirc
                    if all(list(map(lambda x: len(x) == 4, data_packet.split()))): # pronto
                        protocol = "pronto"
                    elif all(list(map(lambda x: len(x) == 2, data_packet.split()))): # hex
                        protocol = "hex"
                        data_packet = data_packet.replace(" ", "")
                    else:
                        protocol = "lirc"

                else:
                    try:
                        int(data_packet)
                        protocol = "hex" # hex
                    except ValueError:
                        protocol = "base64" # base64
        
        if protocol == "pronto":
            code = data_packet.replace(" ", "")
            pronto = bytearray.fromhex(code)
            pulses = self.pronto2lirc(pronto)
            data_packet = self.lirc2broadlink(pulses)
        
        elif protocol == "lirc":
            data_packet = self.lirc2broadlink((data_packet).split())

        elif protocol == "hex":
            data_packet = bytearray.fromhex(data_packet)

        elif protocol == "base64":
            data_packet = base64.b64decode(data_packet)

        try:
            self.broadlinkObjects[entity_id].auth()
            self.broadlinkObjects[entity_id].send_data(data_packet)
            return True
        except:
            self.adbase.log("Logged an error in errorlog")
            self.adbase.error(traceback.format_exc())
            return False

    def update_temperature(self, kwargs):
        dev_entity_id = kwargs["device_entity_id"]
        entity_id = kwargs["entity_id"]
        new_temp = self.check_temperature(dev_entity_id)
        if dev_entity_id == entity_id:
            self.entities[dev_entity_id]["attributes"]["temperature"] = new_temp
            self.adbase.set_state(dev_entity_id, state = "on", attributes = self.entities[dev_entity_id]["attributes"])
        else:
            self.adbase.set_state(entity_id, state = new_temp, attributes = self.entities[dev_entity_id]["temp_sensor_attributes"])

    def check_temperature(self, entity_id):
        temperature = "unavailable"
        self._check_broadlink(entity_id)
        try:
            temperature = self.broadlinkObjects[entity_id].check_temperature()
            if self.entities[entity_id]["use_temp_as_attribute"]:
                self.entities[entity_id]["attributes"]["temperature"] = temperature
        except:
            self.adbase.log("Logged an error in errorlog")
            self.adbase.error(traceback.format_exc())
        return temperature 

    def check_sensors(self, entity_id):
        self._check_broadlink(entity_id)
        try:
            data = self.broadlinkObjects[entity_id].check_sensors()
            return data
        except:
            self.adbase.log("Logged an error in errorlog")
            self.adbase.error(traceback.format_exc())
            return False
    
    def _check_broadlink(self, entity_id):
        if not entity_id in self.broadlinkObjects:
            raise ValueError (f"Broadlink with Entity_ID {entity_id}, doesn't exist")

    def setup_broadlink_cb(self, kwargs):
        self.setup_broadlink()

    def setup_broadlink(self):
        self.adbase.log("Setting up Broadlink Devices")
        try:
            devices = broadlink.discover(5, self.args.get("local_ip"))
        except:
            self.adbase.log("Logged an error in errorlog")
            self.adbase.error(traceback.format_exc())
            return False

        num = len(devices)
        if num > 0: # if it found more than 1 device on the network
            self.adbase.log(f"Found {num} Broadlink Devices on the Network")
        else:
            self.adbase.log(f"Coundn't find any Broadlink Device on the Network")
            return False

        try:
            for device in devices:
                device.auth() #first get device authentication
                device_mac = re.findall('..?', device.mac.hex())
                device_mac.reverse()
                device_mac = ":".join(device_mac)

                for bl, bl_settings in self.broadlinks.items():
                    b_mac = bl_settings.get("mac").lower()
                    if b_mac == None:
                        raise ValueError("No Device MAC Address given, please provide MAC Address")

                    if b_mac != device_mac:
                        continue
 
                    b_friendly_name = bl_settings.get("friendly_name", bl.replace("_", " ")) #get device friendly name
                    b_namespace = bl_settings.get("namespace", "default") #get device namespace

                    self.adbase.set_namespace(b_namespace)

                    b_service_domain = bl_settings.get("service_domain") #get app service domain

                    if b_service_domain != None:
                        b_service_domain = f"broadlink_{b_service_domain}"
                    else:
                        b_service_domain = "broadlink"

                    b_device_name = b_friendly_name.lower().replace(" ", "_")
                    b_device_domain =  bl_settings.get("entity_domain", "sensor")

                    (b_ip, b_port) = device.host
                    b_type = device.devtype

                    entity_id = f"{b_device_domain}.{b_device_name}"

                    self.broadlinkObjects[entity_id] = device #store broadlink object

                    self.entities[entity_id] = {}
                    self.entities[entity_id]["attributes"] = {"friendly_name" : b_friendly_name, "mac" : b_mac,
                                            "ip_address" : b_ip, "port" : b_port, "device_type" : b_type}
                    
                    self.entities[entity_id]["use_temp_as_attribute"] = False

                    if bl_settings.get("use_temp_as_attribute", False) is True:
                        self.entities[entity_id]["attributes"]["temperature"] = "unavailable"
                        self.entities[entity_id]["use_temp_attribute"] = True
                        attr_delay = bl_settings["use_temp_as_attribute"].get("update_frequency",60)
                        runtime = datetime.datetime.now() + datetime.timedelta(seconds=2)
                        self.adbase.run_every(self.update_temperature, runtime, attr_delay, device_entity_id = entity_id, entity_id = entity_id)

                    self.adbase.set_state(entity_id, state="on", attributes=self.entities[entity_id]["attributes"])

                    if "use_sensor_for_temperature" in bl_settings:
                        sensor_delay = bl_settings["use_sensor_for_temperature"].get("update_frequency",60)
                        friendly_name = bl_settings["use_sensor_for_temperature"].get("friendly_name",b_friendly_name)
                        unit_of_measurement = bl_settings["use_sensor_for_temperature"].get("unit_of_measurement","C")
                        runtime = datetime.datetime.now() + datetime.timedelta(seconds=2)
                        sensor_entity_id = bl_settings["use_sensor_for_temperature"].get("name",f"sensor.{b_friendly_name}_temperature")
                        self.entities[entity_id]["temp_sensor"] = sensor_entity_id
                        self.entities[entity_id]["temp_sensor_attributes"] = {}
                        self.entities[entity_id]["temp_sensor_attributes"]["friendly_name"] = friendly_name
                        self.entities[entity_id]["temp_sensor_attributes"]["unit_of_measurement"] = unit_of_measurement
                        self.adbase.run_every(self.update_temperature, runtime, sensor_delay, device_entity_id = entity_id, entity_id = sensor_entity_id)

                    # register services
                    for service in self.avail_services:
                        self.adbase.register_service(f"{b_service_domain}/{service}", self.broadlink_services)
        except:
            self.adbase.log("Logged an error in errorlog")
            self.adbase.error(traceback.format_exc())
            return False
        
        if self.entities != {}:
            self.adbase.fire_event("Broadlink_Setup", entities=self.entities)
            self.adbase.log("Completed Broadlink Device setup")
            return True
        

    def broadlink_services(self, namespace, domain, service, kwargs):
        self.adbase.log(f"{namespace} {domain} {service} {kwargs}", level="DEBUG")

        func = getattr(self, service) #get the function first
        entity_id = kwargs.get("entity_id")
        if service != "setup_broadlink" and entity_id == None:
            raise ValueError("No Entity_ID given, please provide the Entity_ID of the Broadlink device to use")

        data = {"entity_id" : entity_id}
        if service == "send_data":
            data_packet = kwargs.get("data_packet")
            if data_packet == None:
                raise ValueError("No data_packet given to send to Device, please provide the data_packet to use")

            data["data_packet"] = data_packet
            data["protocol"] = kwargs.get("protocol")

        elif service == "update_temperature":
            data["device_entity_id"] = kwargs.get("device_entity_id")

        value = func(**data)
        if value is False: #an error occured while trying to access broadlink. Mostlikely offline
            self.adbase.set_state(entity_id, state="off", attributes=self.entities[entity_id]["attributes"])
        else:
            self.adbase.set_state(entity_id, state="on", attributes=self.entities[entity_id]["attributes"])
        return value

    #def terminate(self): # when app terminates, remove broadlink entities
    #    for entity_id in self.broadlinkObjects:
    #        self.adbase.remove_entity(entity_id)

    #
    # Utility modified from https://github.com/emilsoman/pronto_broadlink/blob/master/pronto2broadlink.py
    #

    def pronto2lirc(self, pronto):
        codes = [int(binascii.hexlify(pronto[i:i+2]), 16) for i in range(0, len(pronto), 2)]

        if codes[0]:
            raise ValueError('Pronto code should start with 0000')
        if len(codes) != 4 + 2 * (codes[2] + codes[3]):
            raise ValueError('Number of pulse widths does not match the preamble')

        frequency = 1 / (codes[1] * 0.241246)

        lirc_code = [int(round(code / frequency)) for code in codes[4:]]

        self.adbase.log(lirc_code, level="DEBUG")
        return lirc_code

    def lirc2broadlink(self, pulses):
        array = bytearray()

        for pulse in pulses:
            if not isinstance(pulse, int):
                pulse = int(pulse)

            pulse = int(pulse * 269 / 8192)  # 32.84ms units

            if pulse < 256:
                array += bytearray(struct.pack('>B', pulse))  # big endian (1-byte)
            else:
                array += bytearray([0x00])  # indicate next number is 2-bytes
                array += bytearray(struct.pack('>H', pulse))  # big endian (2-bytes)

        packet = bytearray([0x26, 0x00])  # 0x26 = IR, 0x00 = no repeats
        packet += bytearray(struct.pack('<H', len(array)))  # little endian byte count
        packet += array
        packet += bytearray([0x0d, 0x05])  # IR terminator

        # Add 0s to make ultimate packet size a multiple of 16 for 128-bit AES encryption.
        remainder = (len(packet) + 4) % 16  # rm.send_data() adds 4-byte header (02 00 00 00)
        if remainder:
            packet += bytearray(16 - remainder)

        return packet
