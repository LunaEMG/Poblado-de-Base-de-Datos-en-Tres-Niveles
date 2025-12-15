Este proyecto contiene la solución dockerizada para la Práctica 5 de la materia **"Bases de Datos"**. Implementa un entorno completo con una base de datos **PostgreSQL**, scripts de poblado automático en **Python** y una interfaz de administración web (**Adminer**).

## 📋 Requisitos Previos

* Tener instalado **Docker Desktop** y **Docker Compose**.
* ⚠️ **Importante:** Asegurarse de que el puerto `5432` no esté ocupado por una instalación local de PostgreSQL (debes detener el servicio local antes de ejecutar este proyecto).

## 📂 Estructura del Proyecto

```text
practica5/
├── docker-compose.yml      # Orquestación de servicios (BD, App, Adminer)
├── Dockerfile              # Definición de la imagen de la aplicación Python
├── entrypoint.sh           # Script de control de flujo
├── requirements.txt        # Dependencias de Python
├── .env                    # Variables de entorno locales (opcional)
├── scripts/                # Scripts de poblado
│   ├── poblar_leve.py
│   ├── poblar_moderado.py
│   └── poblar_masivo.py
└── data/sql/ddl/
    └── 01_schema_ecommerce.sql  # Esquema inicial de la BD
🚀 Instrucciones de EjecuciónPara ejecutar los diferentes niveles de carga, abre tu terminal en la carpeta del proyecto y utiliza los comandos correspondientes a tu sistema operativo.1. Nivel Leve (Desarrollo)Carga ~300 registros verificando integridad transaccional fila por fila.Cualquier sistema:Bashdocker-compose up --build
2. Nivel Moderado (Pre-producción)Carga ~60,000 registros utilizando inserción por lotes (Batch Insert).Windows (PowerShell):PowerShell$env:NIVEL_POBLADO="moderado"; docker-compose up --build
Windows (CMD):DOSset NIVEL_POBLADO=moderado && docker-compose up --build
Linux / Mac:BashNIVEL_POBLADO=moderado docker-compose up --build
3. Nivel Masivo (Producción)Carga ~1,100,000 registros utilizando el protocolo COPY (Bulk Load).Windows (PowerShell):PowerShell$env:NIVEL_POBLADO="masivo"; docker-compose up --build
Windows (CMD):DOSset NIVEL_POBLADO=masivo && docker-compose up --build
Linux / Mac:BashNIVEL_POBLADO=masivo docker-compose up --build
📊 Acceso y VerificaciónUna vez que los contenedores estén corriendo, puedes administrar la base de datos visualmente.Abre tu navegador en: http://localhost:8080Ingresa las siguientes credenciales:CampoValorSistemaPostgreSQLServidordbUsuariopostgresContraseñapostgresBase de datosecommerce_db🧹 LimpiezaPara detener los contenedores y borrar los volúmenes de datos (reiniciar la base de datos desde cero para probar otro nivel de carga), ejecuta:Bashdocker-compose down -v
