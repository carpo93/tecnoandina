# Usa la imagen oficial de Python 3.9 como base
FROM python:3.9

# Establece el directorio de trabajo en /app
WORKDIR /app

# Copia el archivo requirements.txt al directorio de trabajo
COPY requirements.txt .

# Expone el puerto en el que Flask está escuchando
EXPOSE ${IMAGE_PORT_3}

# Instala las dependencias de la aplicación
RUN pip install -r requirements.txt

# Define el comando por defecto para ejecutar la aplicación cuando el contenedor se inicia
CMD ["sh", "-c", "flask run --host=0.0.0.0 --port=${IMAGE_PORT_3}"]