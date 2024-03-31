import logging
import random
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import json
import paho.mqtt.client as mqtt
import os

app = Flask(__name__)

# Configuración básica del registro de log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setear la configuración global de la aplicación con las variables de entorno del sistema
app.config['mqtt_broker_host'] = os.environ.get('MQTTO_HOST', '')
app.config['mqtt_broker_port'] = int(os.environ.get('MQTTO_PORT',''))
app.config['mqtt_keep_alive']  = 60

# Defino el canal a donde se enviarán las mediciones en mqtt
app.config['mqtt_channel'] = 'challenge/dispositivo/rx'

# Define la periodicidad con la que se ejecutara el envío de mensajes, en segundos
app.config['seconds_interval'] = 60

# Define el intervalo entre el que se obtendrán aleatoriamente las mediciones
app.config['from_measurement_value'] = 0
app.config['to_measurement_value']   = 1000

# Defino las versiones soportadas por el dispositivo
app.config['device_versions'] = [1, 2]

# Función para publicar un mensaje en el tópico MQTT
def device_publish_measurement_message(p_date_time,p_value,p_version):
    #Armado del mensaje para enviar a MQTT
    current_time = p_date_time.strftime('%Y-%m-%d %H:%M:%S')
    message = {
        'time': current_time,
        'value': p_value,
        'version': p_version
    }
    #Envio del mensaje
    mqtt_topic = app.config['mqtt_channel']
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.connect(
        host      = app.config['mqtt_broker_host'], 
        port      = app.config['mqtt_broker_port'], 
        keepalive = app.config['mqtt_keep_alive']
    )
    mqtt_client.publish(mqtt_topic, json.dumps(message))
    logger.info(f'Mensaje publicado: {message}')

# Definir la función que se ejecutará periódicamente
def device_send_current_measurement():
    v_date_time = datetime.now()
    v_value = round(
        number = random.uniform(
            app.config['from_measurement_value'],
            app.config['to_measurement_value']
        ),
        ndigits = 2
    )
    v_version = random.choice(app.config['device_versions'])
    logger.info(f"Ejecutando tarea periódica a las {v_date_time}")
    device_publish_measurement_message(v_date_time,v_value,v_version)

# Agregar una tarea periódica al planificador con un intervalo de tiempo
scheduler = BackgroundScheduler()
scheduler.add_job(
    id      = 'send_measurement', 
    func    = device_send_current_measurement, 
    trigger = 'interval', 
    seconds = app.config['seconds_interval']
)

# Iniciar el planificador cuando se inicia la aplicación
scheduler.start()  

if __name__ == '__main__':
    app.run(debug=True)