-- ====================================================================================
-- EJERCICIO 3: OPERACIONES DML AVANZADAS (COMPLETO Y CORREGIDO)
-- Materia: Bases de Datos - Práctica 5
-- Motor: PostgreSQL 15+
-- ====================================================================================

-- ------------------------------------------------------------------------------------
-- 3.1 CONSULTAS SELECT (Mínimo 10 tipos distintos)
-- ------------------------------------------------------------------------------------

-- 1. JOINs Múltiples (3+ tablas)
-- Obtener un reporte detallado de ventas con datos de usuario, producto y categoría.
SELECT 
    o.orden_id,
    u.nombre AS cliente,
    p.nombre AS producto,
    c.nombre AS categoria,
    det.subtotal
FROM ordenes o
JOIN usuarios u ON o.usuario_id = u.usuario_id
JOIN detalle_ordenes det ON o.orden_id = det.orden_id -- Alias 'det' (seguro) en lugar de 'do'
JOIN productos p ON det.producto_id = p.producto_id
JOIN categorias c ON p.categoria_id = c.categoria_id
WHERE o.estado = 'ENTREGADO'
LIMIT 10;

-- 2. Subconsultas Correlacionadas
-- Listar productos cuyo precio es mayor al precio promedio de su propia categoría.
SELECT p.nombre, p.precio, p.categoria_id
FROM productos p
WHERE p.precio > (
    SELECT AVG(p2.precio)
    FROM productos p2
    WHERE p2.categoria_id = p.categoria_id
);

-- 3. Funciones de Agregación con GROUP BY y HAVING
-- Encontrar categorías que han generado más de $5,000 en ventas totales.
SELECT c.nombre AS categoria, SUM(det.subtotal) AS total_ventas
FROM categorias c
JOIN productos p ON c.categoria_id = p.categoria_id
JOIN detalle_ordenes det ON p.producto_id = det.producto_id
GROUP BY c.nombre
HAVING SUM(det.subtotal) > 5000;

-- 4. Window Functions (ROW_NUMBER)
-- Obtener la orden más reciente de cada usuario.
SELECT * FROM (
    SELECT 
        usuario_id, 
        orden_id, 
        fecha_orden, 
        total,
        ROW_NUMBER() OVER (PARTITION BY usuario_id ORDER BY fecha_orden DESC) as rn
    FROM ordenes
) sub
WHERE rn = 1;

-- 5. Operaciones de Conjuntos (EXCEPT)
-- Encontrar usuarios registrados que NUNCA han realizado una orden (Usuarios inactivos).
SELECT usuario_id FROM usuarios
EXCEPT
SELECT usuario_id FROM ordenes;

-- 6. Common Table Expressions (CTEs)
-- Calcular el ticket promedio por usuario y filtrar a los "Compradores VIP".
WITH TicketPromedio AS (
    SELECT usuario_id, AVG(total) as promedio_compra
    FROM ordenes
    WHERE estado IN ('PAGADO', 'ENTREGADO')
    GROUP BY usuario_id
)
SELECT u.nombre, tp.promedio_compra
FROM TicketPromedio tp
JOIN usuarios u ON tp.usuario_id = u.usuario_id
WHERE tp.promedio_compra > 500;

-- 7. Consultas con CASE
-- Clasificar productos por rango de precio para análisis de inventario.
SELECT 
    nombre, 
    precio,
    CASE 
        WHEN precio < 50 THEN 'Económico'
        WHEN precio BETWEEN 50 AND 200 THEN 'Estándar'
        ELSE 'Premium'
    END as gama_producto
FROM productos;

-- 8. Análisis Temporal con Fechas
-- Cantidad de órdenes generadas por día de la semana.
SELECT 
    TO_CHAR(fecha_orden, 'Day') as dia_semana,
    COUNT(*) as total_ordenes
FROM ordenes
GROUP BY TO_CHAR(fecha_orden, 'Day'), EXTRACT(DOW FROM fecha_orden)
ORDER BY EXTRACT(DOW FROM fecha_orden);

-- 9. Expresiones Regulares (Regex)
-- Buscar usuarios con correos de dominios específicos (ej. gmail o hotmail).
SELECT nombre, email
FROM usuarios
WHERE email ~* '@(gmail|hotmail)\.com$';

-- 10. Ranking (RANK) - Extra
-- Top 3 productos más caros por categoría.
SELECT * FROM (
    SELECT 
        p.nombre, 
        c.nombre as categoria, 
        p.precio,
        RANK() OVER (PARTITION BY c.categoria_id ORDER BY p.precio DESC) as ranking
    FROM productos p
    JOIN categorias c ON p.categoria_id = c.categoria_id
) sub
WHERE ranking <= 3;


-- ------------------------------------------------------------------------------------
-- 3.2 OPERACIONES INSERT
-- ------------------------------------------------------------------------------------

-- 1. INSERT con Subconsultas
-- Crear tabla temporal de auditoría e insertar usuarios inactivos.
CREATE TABLE IF NOT EXISTS usuarios_inactivos_log (
    log_id SERIAL PRIMARY KEY,
    usuario_id INT,
    fecha_reporte TIMESTAMP DEFAULT NOW()
);

INSERT INTO usuarios_inactivos_log (usuario_id)
SELECT usuario_id 
FROM usuarios 
WHERE es_activo = FALSE;

-- 2. INSERT Múltiple
-- Insertar varias categorías de golpe.
INSERT INTO categorias (nombre, descripcion) VALUES 
('Gaming', 'Accesorios y consolas de videojuegos'),
('Oficina', 'Mobiliario y papelería')
ON CONFLICT (nombre) DO NOTHING;

-- 3. INSERT con Valores Calculados
-- Insertar un pago calculando un ID de transacción aleatorio.
INSERT INTO pagos (orden_id, metodo_pago, monto, transaccion_externa_id)
SELECT 
    o.orden_id, 
    'TARJETA', 
    o.total, 
    'TXN-' || MD5(RANDOM()::TEXT)
FROM ordenes o
WHERE o.estado = 'PENDIENTE' AND o.total > 0
LIMIT 1;

-- 4. INSERT con Manejo de Duplicados (UPSERT)
-- Intentar insertar producto; si existe SKU, actualizar stock.
INSERT INTO productos (categoria_id, nombre, precio, stock, sku)
VALUES (1, 'Laptop Gamer Pro', 25000.00, 10, 'LAP-001')
ON CONFLICT (sku) 
DO UPDATE SET 
    stock = productos.stock + EXCLUDED.stock,
    fecha_creacion = NOW();


-- ------------------------------------------------------------------------------------
-- 3.3 OPERACIONES UPDATE
-- ------------------------------------------------------------------------------------

-- 1. UPDATE con JOIN (Sintaxis PostgreSQL: FROM)
-- Aumentar 10% el precio de productos cuya categoría sea 'Premium' (simulada por descripción).
UPDATE productos
SET precio = precio * 1.10
FROM categorias
WHERE productos.categoria_id = categorias.categoria_id
AND categorias.descripcion ILIKE '%lujo%';

-- 2. UPDATE Condicional con CASE
-- Ajustar stock: si es bajo (<5) reponer 50 unidades.
UPDATE productos
SET stock = stock + CASE 
    WHEN stock < 5 THEN 50
    ELSE 0 
END;

-- 3. UPDATE Masivo
-- Cancelar órdenes pendientes de más de 1 año.
UPDATE ordenes
SET estado = 'CANCELADO'
WHERE estado = 'PENDIENTE' 
AND fecha_orden < NOW() - INTERVAL '1 year';

-- 4. UPDATE con Subconsultas
-- Desactivar usuarios que no han comprado nada.
UPDATE usuarios
SET es_activo = FALSE
WHERE usuario_id NOT IN (SELECT DISTINCT usuario_id FROM ordenes);


-- ------------------------------------------------------------------------------------
-- 3.4 OPERACIONES DELETE
-- ------------------------------------------------------------------------------------

-- 1. DELETE con Subconsultas
-- Eliminar categorías que no tienen productos.
DELETE FROM categorias
WHERE categoria_id NOT IN (SELECT DISTINCT categoria_id FROM productos);

-- 2. DELETE con JOIN (Sintaxis PostgreSQL: USING)
-- Eliminar detalles de órdenes canceladas.
DELETE FROM detalle_ordenes
USING ordenes
WHERE detalle_ordenes.orden_id = ordenes.orden_id
AND ordenes.estado = 'CANCELADO';

-- 3. Soft Delete (Marcado Lógico)
-- En lugar de borrar la orden, cambiamos su estado (si el constraint lo permite).
-- Nota: Asegurarse de que 'ELIMINADO' esté en el CHECK constraint o usar 'CANCELADO'.
UPDATE ordenes SET estado = 'CANCELADO' WHERE orden_id = 100;

-- 4. Archivado antes de eliminación
-- Mover productos descontinuados a histórico antes de borrarlos.
CREATE TABLE IF NOT EXISTS productos_archivados AS SELECT * FROM productos WITH NO DATA;

WITH movidos AS (
    DELETE FROM productos
    WHERE stock = 0 AND fecha_creacion < NOW() - INTERVAL '2 years'
    RETURNING *
)
INSERT INTO productos_archivados SELECT * FROM movidos;


-- ------------------------------------------------------------------------------------
-- 3.5 TRANSACCIONES (ACID)
-- ------------------------------------------------------------------------------------

-- Escenario 1: Proceso de Compra Completo (Commit Exitoso)
BEGIN;
    -- Bloquear el producto (FOR UPDATE)
    SELECT stock FROM productos WHERE producto_id = 5 FOR UPDATE;

    -- Actualizar inventario
    UPDATE productos SET stock = stock - 1 WHERE producto_id = 5;

    -- Crear orden (Usar un usuario existente, ej: 1)
    INSERT INTO ordenes (usuario_id, estado, total) 
    VALUES (1, 'PAGADO', 1500.00);
COMMIT;

-- Escenario 2: Control de Errores y Rollback
BEGIN;
    -- Intentar poner stock negativo (fallará por el CHECK constraint)
    UPDATE productos SET stock = -10 WHERE producto_id = 1;
ROLLBACK; -- Se deshacen los cambios (aunque el error ya lo hubiera abortado)

-- Escenario 3: Savepoints
BEGIN;
    INSERT INTO categorias (nombre) VALUES ('Categoria Temp');
    SAVEPOINT punto_seguro;
    
    -- Operación fallida (duplicado)
    INSERT INTO categorias (nombre) VALUES ('Categoria Temp'); 
    
    -- Regresamos al punto seguro, salvando la primera inserción
    ROLLBACK TO SAVEPOINT punto_seguro;
    
    INSERT INTO categorias (nombre) VALUES ('Categoria Final');
COMMIT;

-- Escenario 4: Niveles de Aislamiento
BEGIN;
    SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
    SELECT COUNT(*) FROM ordenes;
    -- ... operaciones críticas ...
COMMIT;