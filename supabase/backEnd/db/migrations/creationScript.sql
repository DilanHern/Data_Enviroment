-- schema: public (o ventas_pg)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE cliente (
 cliente_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
 nombre TEXT NOT NULL,
 email TEXT UNIQUE,
 genero CHAR(1) NOT NULL CHECK (genero IN ('M','F')),
 pais TEXT NOT NULL,
 fecha_registro DATE NOT NULL DEFAULT CURRENT_DATE
);

CREATE TABLE producto (
 producto_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
 sku TEXT UNIQUE, -- puede venir vacío en algunos
 nombre TEXT NOT NULL,
 categoria TEXT NOT NULL
);

CREATE TABLE orden (
 orden_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
 cliente_id UUID NOT NULL REFERENCES cliente(cliente_id),
 fecha TIMESTAMPTZ NOT NULL DEFAULT NOW(),
canal TEXT NOT NULL CHECK (canal IN ('WEB','APP','PARTNER')), -- PARTNER distinto
moneda CHAR(3) NOT NULL, -- USD/CRC
 total NUMERIC(18,2) NOT NULL
);

CREATE TABLE orden_detalle (
 orden_detalle_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
 orden_id UUID NOT NULL REFERENCES orden(orden_id),
 producto_id UUID NOT NULL REFERENCES producto(producto_id),
 cantidad INT NOT NULL CHECK (cantidad > 0),
 precio_unit NUMERIC(18,2) NOT NULL
);

CREATE INDEX ix_orden_fecha ON orden(fecha);
CREATE INDEX ix_detalle_producto ON orden_detalle(producto_id);