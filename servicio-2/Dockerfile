# Usa la imagen oficial de Python 3.9 como base
FROM python:3.9

# Establece el directorio de trabajo en /app
WORKDIR /app

# Copia el archivo requirements.txt al directorio de trabajo
COPY requirements.txt .

# Instala las dependencias de la aplicación
RUN pip install -r requirements.txt

# Define el comando por defecto para ejecutar la aplicación cuando el contenedor se inicia
CMD ["flask", "run"]