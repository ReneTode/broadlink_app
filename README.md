# broadlink_app

AppDaemon App For use with Broadlink. With this app, all Broadlink devices on the same network can be controlled

## installation
- This app requires appdaemon 4.0 pre installed
- Copy this python file to your apps directory
- Configure a yaml file (apps.yaml or any other yaml file in the apps directory) as shown below

apps.yaml parameters:
### toplevel:
- local_ip (optional, default None): The local IP of the system running AD. Only important in a docker container
- broadlinks: (not optional): A dictionay definition of the name and mac address of each broadlink device
- base64 (optional): A dictionay definition of names and ir codes to be used, encoded as base64
- lirc (optional): A dictionay definition of names and ir codes to be used, encoded as lirc
- pronto (optional): A diction aydefinition of names and ir codes to be used, encoded as pronto
- hex (optional): A dictionay definition of names and ir codes to be used, encoded as hex

inside broadlinks:
- specify a name for every broadlink

inside the specified name:
- mac: (not optional) the mac address from the broadlink device
- friendly_name (optional, default broadlink name)
- entity_domain (optional, default sensor): The domain to be used when defining the entities to be created
- service_domain (optional, default broadlink): The domain from the services
- namespace (optional, default default): The namespace in which the entities and services are created
- use_sensor_for_temperature: (optional): A dictionay definition of the name and update frequency for a temperature sensor
- use_temp_as_attribute: (optional, False or empty) set the temperature as attribute from the broadlink device

inside use_sensor_for_temperature:
- update_frequence (optional, default 60): the frequency with which the temperature sensor will be updated
- name: (optional, default sensor.broadlink_name_temperature) the name for the temperature sensor
- friendly_name (optional, default broadlink_name_temperature) friendly name for the temperature sensor
- Unit_of_measurement (optional, default C) unit of measurement for the temperature sensor

inside use_temp_as_attribute:
- update_frequence (optional, default 60): the frequency with which the temperature attribute will be updated

example config can be seen below:
```
broadlink_app:
    class: BroadlinkApp
    module: broadlink_app
    broadlinks:
        living_room:
            mac: xx:xx:xx:xx:xx:xx
            namespace: hass
            entity_domain: sensor
            service_domain: living_room
            friendly_name: Broadlink living room
            mac: xx:xx:xx:xx:xx:xx 
            use_temp_as_sensor: 
                name: sensor.living_room_temperature
                friendly_name: Living room temp
                Unit_of_measurement: C 
                update_frequency: 60 
            use_temp_as_attribute:
                update_frequency: 60 
    base64:
        lg_tv_input: JgBQAAABKpQTEhITEjgSExITEhMSExITEzcSOBITEjgTNxI4EjgSOBI4EjgTEhI4EhMSExITEhMTEhITEjgSExI4EjgSOBI4EgAFLgABKkkSAA0FAAAAAAAAAAA=
    pronto:
        lg_tv_hdmi_1: 0000 006C 0022 0002 015B 00AD 0016 0016 0016 0016 0016 0041 0016 0016 0016 0016 0016 0016 0016 0016 0016 0016 0016 0041 0016 0041 0016 0016 0016 0041 0016 0041 0016 0041 0016 0041 0016 0041 0016 0016 0016 0041 0016 0041 0016 0041 0016 0016 0016 0016 0016 0041 0016 0041 0016 0041 0016 0016 0016 0016 0016 0016 0016 0041 0016 0041 0016 0016 0016 0016 0016 05F7 015B 0057 0016 0E6C
    hex:
        lg_tv_mute: 2600580000012a94121312131238121312131213121312131238133712131238133713371238123813371312121312381213121312131213121312381238121313371238123813371200052e00012a4a13000c670001294a12000d05
    lirc:
        philips_sb_audio_in: 2663 860 472 832 472 416 472 416 1332 1304 472 416 472 416 916 860 472 416 472 416 472 416 916 860 472 416 472 416 472 416 916 416 472 832 361
```

available services:
- setup_broadlink                                                 ,returns True or False
- learn                  (expects entity_id="broadlink_entity_id") returns True or False
- sweep_frequency        (expects entity_id="broadlink_entity_id") returns True or False
- cancel_sweep_frequency (expects entity_id="broadlink_entity_id") returns True or False
- check_frequency        (expects entity_id="broadlink_entity_id") returns frequency or False
- find_rf_packet         (expects entity_id="broadlink_entity_id") returns rf packet or False
- check_data             (expects entity_id="broadlink_entity_id") returns True or False
- send_data              (expects entity_id="broadlink_entity_id", data_packet="", protocol = "") returns True or False, data_packet can be a name you have set in the yaml or an actual data packet. protocol is optional
- check_temperature      (expects entity_id="broadlink_entity_id") returns temperature or False
- check_sensors          (expects entity_id="broadlink_entity_id") returns sensor data or False

example use:
```
controle_value = self.call_service("broadlink_living_room/learn", entity_id = "sensor.living_room")
controle_value = self.call_service("broadlink_living_room/send_data", entity_id = "sensor.living_room", data_packet = lg_tv_hdmi_1)
controle_value = self.call_service("broadlink_living_room/send_data", entity_id = "sensor.living_room", protocol = lirc, data_packet = "2663 860 472 832 472 416 472 416 1332 1304 472 416 472 416 916 860 472 416 472 416 472 416 916 860 472 416 472 416 472 416 916 416 472 832 361"
```
