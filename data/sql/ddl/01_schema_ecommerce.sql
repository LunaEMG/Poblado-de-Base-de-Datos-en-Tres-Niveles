-- =============================================
-- EJERCICIO 1: DISEÑO DEL MODELO DE DATOS
-- Dominio: E-Commerce
-- Motor: PostgreSQL
-- =============================================
-- 1. Tabla de Usuarios (Clientes y Admins)
CREATE TABLE usuarios (
    usuario_id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    es_activo BOOLEAN DEFAULT TRUE,
    pais VARCHAR(50),
    -- Constraint CHECK: Validación de formato de email
    CONSTRAINT check_email_valido CHECK (
        email ~* '^[A-Za-z0-9._+%-]+@[A-Za-z0-9.-]+[.][A-Za-z]+$'
    )
);
-- 2. Tabla de Categorías
CREATE TABLE categorias (
    categoria_id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion TEXT,
    activo BOOLEAN DEFAULT TRUE
);
-- 3. Tabla de Productos
CREATE TABLE productos (
    producto_id SERIAL PRIMARY KEY,
    categoria_id INT REFERENCES categorias(categoria_id),
    nombre VARCHAR(150) NOT NULL,
    precio DECIMAL(10, 2) NOT NULL CHECK (precio > 0),
    stock INT NOT NULL DEFAULT 0 CHECK (stock >= 0),
    sku VARCHAR(20) UNIQUE NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- 4. Tabla de Órdenes (Cabecera)
CREATE TABLE ordenes (
    orden_id SERIAL PRIMARY KEY,
    usuario_id INT REFERENCES usuarios(usuario_id),
    fecha_orden TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado VARCHAR(20) DEFAULT 'PENDIENTE' CHECK (
        estado IN (
            'PENDIENTE',
            'PAGADO',
            'ENVIADO',
            'ENTREGADO',
            'CANCELADO'
        )
    ),
    total DECIMAL(12, 2) DEFAULT 0.00
);
-- 5. Tabla de Detalle de Órdenes (Relación Muchos a Muchos)
CREATE TABLE detalle_ordenes (
    detalle_id SERIAL PRIMARY KEY,
    orden_id INT REFERENCES ordenes(orden_id) ON DELETE CASCADE,
    producto_id INT REFERENCES productos(producto_id),
    cantidad INT NOT NULL CHECK (cantidad > 0),
    precio_unitario DECIMAL(10, 2) NOT NULL,
    -- Columna calculada automáticamente
    subtotal DECIMAL(12, 2) GENERATED ALWAYS AS (cantidad * precio_unitario) STORED
);
-- 6. Tabla de Pagos
CREATE TABLE pagos (
    pago_id SERIAL PRIMARY KEY,
    orden_id INT UNIQUE REFERENCES ordenes(orden_id),
    fecha_pago TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metodo_pago VARCHAR(50) CHECK (
        metodo_pago IN ('TARJETA', 'PAYPAL', 'TRANSFERENCIA')
    ),
    monto DECIMAL(12, 2) NOT NULL,
    transaccion_externa_id VARCHAR(100)
);
-- ÍNDICES PARA OPTIMIZACIÓN
CREATE INDEX idx_usuarios_email ON usuarios(email);
CREATE INDEX idx_productos_categoria ON productos(categoria_id);
CREATE INDEX idx_ordenes_usuario ON ordenes(usuario_id);
CREATE INDEX idx_ordenes_fecha ON ordenes(fecha_orden);
CREATE INDEX idx_detalle_producto ON detalle_ordenes(producto_id);