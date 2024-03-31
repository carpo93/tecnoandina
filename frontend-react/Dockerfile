# Utilizar la imagen base de Node para construir la aplicación
FROM node:alpine AS builder

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar el archivo package.json y package-lock.json para instalar dependencias
COPY ./app/ .

# Instalar las dependencias
RUN npm install

# Construir la aplicación React
RUN npm run build

# Segunda etapa para servir la aplicación React construida
FROM nginx:alpine

# Copiar los archivos de la aplicación construida desde el builder
COPY --from=builder /app/build /usr/share/nginx/html

# Exponer el puerto 80 para la aplicación
EXPOSE 80

# Comando para iniciar el servidor de nginx y servir la aplicación
CMD ["nginx", "-g", "daemon off;"]