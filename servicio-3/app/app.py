import logging
from flask import Flask, request, jsonify,abort
from flask_cors import CORS
from influxdb_client import InfluxDBClient, Point,Query
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import mysql.connector
import random
import os
import re
import secrets

app = Flask(__name__)
CORS(app)

# Configuración básica del registro de log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de conexión a InfluxDB, con las variables de entorno del sistema
app.config['influx_host']        = os.environ.get('INFLUXDB_HOST', '')
app.config['influx_port']        = int(os.environ.get('INFLUXDB_PORT', '0'))
app.config['influx_user']        = os.environ.get('DOCKER_INFLUXDB_INIT_USERNAME', '')
app.config['influx_password']    = os.environ.get('DOCKER_INFLUXDB_INIT_PASSWORD', '')
app.config['influx_org']         = os.environ.get('DOCKER_INFLUXDB_INIT_ORG', '')
app.config['influx_bucket']      = os.environ.get('DOCKER_INFLUXDB_INIT_BUCKET', '')
app.config['influx_measurement'] = 'dispositivos'

# Configuración de conexión a MySQL, con las variables de entorno del sistema
app.config['mysql_host']     = os.environ.get('MYSQL_HOST', '')
app.config['mysql_port']     = int(os.environ.get('MYSQL_PORT', '0'))
app.config['mysql_username'] = os.environ.get('MYSQL_USER', '')
app.config['mysql_password'] = os.environ.get('MYSQL_PASSWORD', '')
app.config['mysql_database'] = os.environ.get('MYSQL_DATABASE', '')
app.config['timezone'] = os.environ.get('TZ', '')
db_config = {
    'host'    : app.config['mysql_host'],
    #'port'    : app.config['mysql_port'],
    'user'    : app.config['mysql_username'],
    'password': app.config['mysql_password'],
    'database': app.config['mysql_database']
}

# Defino las versiones soportadas por el dispositivo
app.config['device_versions'] = [1, 2]
app.config['alert_type'] = ['BAJA', 'MEDIA', 'ALTA']

# Defino la ventana maxima a procesar de manera sincronica, en días
app.config['max_days_sync_time_search'] = 30

# Crear un cliente InfluxDB
influx_client =  InfluxDBClient(
    url      = f"http://{app.config['influx_host']}:{app.config['influx_port']}",
    username = app.config['influx_user'],
    password = app.config['influx_password']
)
influx_client.default_to_local = True
query_api = influx_client.query_api()

@app.route('/challenge/process', methods=['POST'])
def process_measurements():
    try:
        # Obtengo los parámetros de entrada
        v_data        = request.get_json()
        logger.info(f'v_data: {v_data}')
        v_version     = v_data['version']
        v_time_search = v_data['timeSearch']

        # Validar los parámetros de entrada
        if not(validate_sync_time_search(v_time_search) and v_version in app.config['device_versions']):
            return jsonify({'status': 'No se pudo procesar los párametros'}), 422
        
        # Procesar los puntos de InfluxDB
        v_measurements = get_devices_measurements(v_version, v_time_search)
        logger.info(f'Mensajes obtenidos a procesar en MySQL: {v_measurements}')

        # Insertar registros en MySQL
        save_measurements_as_alerts(v_measurements)
        return jsonify({'status': 'ok'}), 200    
    except Exception as e:
        return jsonify({'status': f'Error: {str(e)}'}), 500

@app.route('/challenge/process_async', methods=['POST'])
def process_async_measurements():
    try:
        # Obtengo los parámetros de entrada
        v_data        = request.get_json()
        logger.info(f'v_data: {v_data}')
        v_version     = v_data['version']
        v_time_search = v_data['timeSearch']

        # Validar los parámetros de entrada
        if not(validate_async_time_search(v_time_search) and v_version in app.config['device_versions']):
            return jsonify({'status': 'No se pudo procesar los párametros'}), 422
        
        v_uid = secrets.token_hex(32)
        logger.info(f'v_uid: {v_uid}')
        # Obtener la fecha y hora actual
        v_schedule_time = datetime.now()

        # Sumar 1 minuto a la fecha y hora actual para ejecutar el procesamiento de forma desacoplada al request y evitar timeout
        v_schedule_time = v_schedule_time + timedelta(minutes=1)
        scheduler.add_job(
            id       = v_uid, 
            func     = process_async_alerts, 
            trigger  = 'date', 
            run_date = v_schedule_time,
            args     = [v_uid,v_version, v_time_search]
        )
        # Retornamos el contexto de ejecución con el que se agendó el job
        return jsonify({'status': 'ok','job_id':v_uid}), 200    
    except Exception as e:
        return jsonify({'status': f'Error: {str(e)}'}), 500
    
@app.route('/challenge/process_async/exec_status', methods=['POST'])
def process_async_measurements_status():
    ## FIXME: Esto deberia implementarse con una BD para poder persistir los jobs
    try:
        # Obtengo los parámetros de entrada
        v_data = request.get_json()
        logger.info(f'v_data: {v_data}')
        v_job_id = v_data['job_id']
        # Obtener información del trabajo con el ID específico
        v_job = scheduler.get_job(v_job_id)
        if v_job:
            v_status = "pending"
        else:
            v_status = "executed"
        # Retornamos el contexto de ejecución con el que se agendó el job
        return jsonify({'job_status': v_status}), 200    
    except Exception as e:
        return jsonify({'status': f'Error: {str(e)}'}), 500

@app.route('/challenge/search', methods=['POST'])
def search_alerts():
    try:
        v_data       = request.get_json()
        v_version    = v_data['version']
        v_alert_type = v_data['type']
        v_sended     = v_data['sended']

        # Validar los parámetros de entrada
        if not(
            (v_version in app.config['device_versions']) and
            (v_alert_type in app.config['alert_type'] or v_alert_type is None) and
            (isinstance(v_sended, bool) or v_sended is None)
        ):
            return jsonify({'status': 'No se pudo procesar los párametros'}), 422

        # Realizar busqueda de alertas
        v_alerts = alerts_search(v_version, v_alert_type, v_sended)

        return jsonify(v_alerts), 200
    except Exception as e:
        return jsonify({'status': f'Error: {str(e)}'}), 500

@app.route('/challenge/send', methods=['POST'])
def send_alerts():
    try:
        v_data       = request.get_json()
        v_version    = v_data['version']
        v_alert_type = v_data['type']

        # Validar los parámetros de entrada
        if not(
            v_version in app.config['device_versions'] and
            v_alert_type in app.config['alert_type'] 
        ):
            return jsonify({'status': 'No se pudo procesar los párametros'}), 422

        # Buscar y actualizar los datos dentro de MySQL
        process_send_alerts(v_version, v_alert_type)

        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        return jsonify({'status': f'Error: {str(e)}'}), 500

def process_async_alerts(p_uid,p_version,p_time_search):
    logger.info(f'Iniciando el proceso con el uid: {p_uid}')
    # Procesar los puntos de InfluxDB
    v_measurements = get_devices_measurements(p_version, p_time_search)
    logger.info(f'Mensajes obtenidos a procesar en MySQL: {v_measurements}')

    # Insertar registros en MySQL
    save_measurements_as_alerts(v_measurements)
    return None

def validate_sync_time_search(p_time_search):
    # Expresión regular para validar el formato (ej: 15m, 3h, 2d)
    v_pattern = r'^\d+[mhd]$'
    if re.match(v_pattern, p_time_search):
        # Obtener el valor numérico de la ventana (eliminando la última letra)
        v_value  = int(p_time_search[:-1])
        # Obtener la unidad de la ventana (m, h, d)
        v_unit    = p_time_search[-1]
        v_days    = app.config['max_days_sync_time_search']
        v_hours   = v_days * 24
        v_minutes = v_hours * 60
        if v_unit == 'm' and v_value <= v_minutes:
            return True
        elif v_unit == 'h' and v_value <= v_hours:
            return True
        elif v_unit == 'd' and v_value <= v_days:
            return True
        else:
            return False
    return False

def validate_async_time_search(p_time_search):
    # Expresión regular para validar el formato (ej: 15m, 3h, 2d)
    v_pattern = r'^\d+[mhd]$'
    if re.match(v_pattern, p_time_search):
        return True
    else:
        return False

def get_devices_measurements(p_version, p_time_search):
    # Aquí puedes agregar la lógica real para consultar y procesar los datos de InfluxDB
    # Ejecutar la consulta con los parámetros usando el parámetro params
    v_query_params = {
        "p_bucket" : app.config["influx_bucket"],
        "p_from" : '-'+p_time_search,
        "p_to" : 'now()',
        "p_measurement" : app.config["influx_measurement"],
        "p_version" : str(p_version)
    }
    v_result = query_api.query(
        query  = 'from(bucket: "'+ v_query_params["p_bucket"] +'") \
            |> range(start: '+ v_query_params["p_from"] +', stop: '+ v_query_params["p_to"] +') \
            |> filter(fn: (r) => r["_measurement"] == "'+ v_query_params["p_measurement"] +'") \
            |> filter(fn: (r) => r["version"] == "'+ v_query_params["p_version"] +'")', 
        org    = app.config['influx_org']
    )
    return v_result

def save_measurements_as_alerts(p_measurements):
    logger.info('Guardando en MySQL')
    # Establecer la conexión a la base de datos
    connection = mysql.connector.connect(**db_config)
    # Crear un cursor para ejecutar consultas
    cursor = connection.cursor()
    # Lista para almacenar los puntos de datos
    points = []
    # Iterar sobre las tablas de resultados
    for table in p_measurements:
        # Iterar sobre las filas de la tabla
        for row in table.records:
            # Agregar cada punto de datos a la lista
            points.append(row.values)
            v_version    = row.values["version"]
            v_value      = row.values["_value"]
            v_time       = row.values["_time"]
            v_alert_type = get_alert_type(int(v_version),int(v_value))
            sql = "INSERT INTO alertas (datetime,value,version,type) VALUES (CONVERT_TZ(%s,'+00:00','America/Santiago'), %s,%s,%s) ON DUPLICATE KEY UPDATE updated_at = now()"
            values = (v_time,v_value,v_version,v_alert_type)
            # Ejecutar la consulta de inserción
            cursor.execute(sql, values)
    # Confirmar la transacción
    connection.commit()
    # Cerrar el cursor y la conexión
    cursor.close()
    connection.close()
    return None

def get_alert_type(p_version,p_value):
    # Se calculan los tipos de alertas, se decide poner nulo para aquellos casos que no cumplan las parametrizaciones definidas
    if p_version == 1:
        if p_value > 200 and p_value <= 500:
            return 'BAJA'
        elif p_value > 500 and p_value <= 800:
            return 'MEDIA'
        elif p_value > 800 and p_value < 1000:
            return 'ALTA'
        else:
            return None
    elif p_version == 2:
        if p_value < 200 and p_value >= 0 :
            return 'ALTA'
        elif p_value < 500 and p_value >= 200:
            return 'MEDIA'
        elif p_value < 800 and p_value >= 500:
            return 'BAJA'
        else:
            return None
    else:
        return None

def alerts_search(p_version, p_alert_type, p_sended):
    # Buscar las alertas en MySQL
    # Establecer la conexión a la base de datos
    connection = mysql.connector.connect(**db_config)
    # Crear un cursor para ejecutar consultas
    cursor = connection.cursor()
    sql = "SELECT datetime,value,version,type,sended FROM alertas WHERE version=%s AND (type = %s OR %s IS NULL) AND (sended = %s OR %s IS NULL) ORDER BY datetime"
    values = (p_version,p_alert_type,p_alert_type,p_sended,p_sended)
    # Ejecutar la consulta de inserción
    cursor.execute(sql, values)
    v_data = cursor.fetchall()
    cursor.close()
    connection.close()
    # Convertir los resultados a un formato JSON y devolverlos
    v_alerts = []
    for v_row in v_data:
        v_alerts.append(
            {
                'datetime': v_row[0].strftime('%Y-%m-%d %H:%M:%S'),
                'value': v_row[1],
                'version': v_row[2],
                'type': v_row[3],
                'sended': bool(v_row[4])
            }
        )
    return v_alerts

def process_send_alerts(p_version, p_alert_type):
    # Buscar las alertas en MySQL
    # Establecer la conexión a la base de datos
    connection = mysql.connector.connect(**db_config)
    # Crear un cursor para ejecutar consultas
    cursor = connection.cursor()
    logger.info(f'p_version: {p_version}')
    logger.info(f'p_alert_type: {p_alert_type}')
    sql = "UPDATE alertas SET sended = TRUE WHERE version="+str(p_version)+" AND type = '"+p_alert_type+"' AND NOT(sended)"
    logger.info(f'sql: {sql}')
    # Ejecutar la consulta de actualización
    cursor.execute(sql)
    # Confirmar la transacción
    connection.commit()
    # Cerrar el cursor y la conexión
    cursor.close()
    connection.close()
    return None

# Agregar una tarea periódica al planificador con un intervalo de tiempo
scheduler = BackgroundScheduler()

# Iniciar el planificador cuando se inicia la aplicación
scheduler.start()  

if __name__ == '__main__':
    app.run(debug=True)