import logging
from flask import Flask
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import json
import paho.mqtt.client as mqtt
import os

app = Flask(__name__)

# Configuración básica del registro de log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configura el cliente MQTT, con las variables de entorno del sistema
app.config['mqtt_broker_host'] = os.environ.get('MQTTO_HOST', '')
app.config['mqtt_broker_port'] = int(os.environ.get('MQTTO_PORT',''))
app.config['mqtt_keep_alive']  = 60

# Configuración de conexión a InfluxDB, con las variables de entorno del sistema
app.config['influx_host']     = os.environ.get('INFLUXDB_HOST', '')
app.config['influx_port']     = int(os.environ.get('INFLUXDB_PORT', '0'))
app.config['influx_user']     = os.environ.get('DOCKER_INFLUXDB_INIT_USERNAME', '')
app.config['influx_password'] = os.environ.get('DOCKER_INFLUXDB_INIT_PASSWORD', '')
app.config['influx_org']      = os.environ.get('DOCKER_INFLUXDB_INIT_ORG', '')
app.config['influx_bucket']   = os.environ.get('DOCKER_INFLUXDB_INIT_BUCKET', '')

# Defino el canal de MQTT
app.config['mqtt_channel'] = 'challenge/dispositivo/rx'

# Defino el measurement de MQTT
app.config['influx_measurement'] = 'dispositivos' 

# Configuración del cliente MQTT
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

# Función para procesar los mensajes MQTT
def on_message(client, userdata, message):
    payload = json.loads(message.payload.decode('utf-8'))
    value   = payload['value']
    version = payload['version']
    time    = payload['time']
    
    # Crear un punto InfluxDB con los datos recibidos
    point = Point(app.config['influx_measurement']).tag('version', version).field('time', time).field('value', value)
    
    # Crear un cliente InfluxDB
    influx_client =  InfluxDBClient(
        url      = f"http://{app.config['influx_host']}:{app.config['influx_port']}",
        username = app.config['influx_user'],
        password = app.config['influx_password']
    )
    write_api = influx_client.write_api()

    # Insertar el punto en InfluxDB
    write_api.write(
        bucket = app.config['influx_bucket'],
        org    = app.config['influx_org'],
        record = point
    )

    logger.info(f"Insertando punto en InfluxDB - { datetime.now() }")

# Configurar el manejo de mensajes MQTT
mqtt_client.on_message = on_message
mqtt_client.connect(
    host      = app.config['mqtt_broker_host'], 
    port      = app.config['mqtt_broker_port'], 
    keepalive = app.config['mqtt_keep_alive']
)
mqtt_client.subscribe(app.config['mqtt_channel'])
mqtt_client.loop_start()

if __name__ == '__main__':
    app.run()