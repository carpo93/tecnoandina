USE tecnoandina;

-- Se decide dejar los campos de fecha como timestamp para poder manejar mejor los cambios de zona horaria (verano/invierno)
-- Se crea además un indice unico sobre los campos version y datetime, para evitar repetir la inserción de los mismos registros
CREATE TABLE IF NOT EXISTS alertas (
    id_alerta INT AUTO_INCREMENT PRIMARY KEY,
    datetime TIMESTAMP NOT NULL,
    value FLOAT NOT NULL,
    version INT NOT NULL,
    type ENUM('BAJA', 'MEDIA', 'ALTA'),
    sended BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY alertas_unique (version, datetime)
);
