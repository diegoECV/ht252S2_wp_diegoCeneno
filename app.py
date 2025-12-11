from flask import Flask, render_template, request, jsonify
import pymysql
import os


pymysql.install_as_MySQLdb()

app = Flask(__name__)

DB_CONFIG = {
    'host': 'aws.czmy26ksgtca.us-east-1.rds.amazonaws.com',
    'user': 'root',
    'password': 'diego1416',
    'database': 'hackaton',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'

def get_db_connection():
    """Crea y retorna una nueva conexión a la base de datos"""
    return pymysql.connect(**DB_CONFIG)

def ejecutar_query(query, params=None, uno=False):
    """Función auxiliar para ejecutar consultas SQL de forma segura"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params or ())
            resultado = cursor.fetchone() if uno else cursor.fetchall()
        return resultado
    finally:
        connection.close()

# ============================================
# RUTAS DE VISTAS (TEMPLATES)
# ============================================

@app.route('/')
def index():
    """Renderiza el formulario de registro de equipos"""
    return render_template("index.html")

@app.route('/equipos')
def equipos():
    """Renderiza la lista de equipos registrados"""
    return render_template("equipos.html")

# ============================================
# ENDPOINTS REST API
# ============================================

@app.route('/api/modelos/<marca>', methods=['GET'])
def obtener_modelos(marca):
    """
    GET /api/modelos/<marca> - Obtiene los modelos disponibles para una marca
    Params: marca - nombre de la marca (hp, dell, lenovo, asus, apple)
    Returns: JSON con lista de modelos y sus especificaciones
    """
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT nombre, ram, almacenamiento, procesador FROM modelos WHERE LOWER(marca) = LOWER(%s) ORDER BY nombre",
                (marca,)
            )
            modelos = cursor.fetchall()
        return jsonify({'ok': True, 'modelos': modelos}), 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'ok': False, 'error': str(e)}), 500
    finally:
        connection.close()

@app.route('/api/equipos', methods=['GET'])
def listar_equipos():
    """
    GET /api/equipos - Obtiene todos los equipos registrados
    Returns: JSON con lista de equipos ordenados por fecha de registro
    """
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM equipos ORDER BY fecha_registro DESC")
            equipos = cursor.fetchall()
        return jsonify({'ok': True, 'equipos': equipos}), 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'ok': False, 'error': str(e)}), 500
    finally:
        connection.close()

@app.route('/api/equipos', methods=['POST'])
def crear_equipo():
    """
    POST /api/equipos - Registra un nuevo equipo
    Body: JSON con datos del equipo (codigo, tipo, marcas, modelo, so, almacenamiento, ram, estado, mantenimiento)
    Returns: JSON con confirmación de registro exitoso
    """
    connection = get_db_connection()
    try:
        datos = request.get_json()
        if not datos:
            return jsonify({'ok': False, 'error': 'No hay datos'}), 400
        
        # Insertar nuevo equipo usando consulta parametrizada (seguridad SQL injection)
        sql = """INSERT INTO equipos 
                 (codigo, tipo, marcas, modelo, so, almacenamiento, ram, estado, mantenimiento) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        
        valores = (
            datos.get('codigo'),
            datos.get('tipo'),
            datos.get('marcas'),
            datos.get('modelo'),
            datos.get('so'),
            datos.get('almacenamiento'),
            datos.get('ram'),
            datos.get('estado'),
            datos.get('mantenimiento')
        )
        
        with connection.cursor() as cursor:
            cursor.execute(sql, valores)
        connection.commit()
        
        return jsonify({'ok': True, 'mensaje': 'Equipo registrado exitosamente'}), 200
        
    except Exception as e:
        import traceback
        print(f"Error: {str(e)}")
        print(traceback.format_exc())
        connection.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500
    finally:
        connection.close()

@app.route('/api/equipos/<int:id>', methods=['PUT'])
def actualizar_equipo(id):
    """
    PUT /api/equipos/<id> - Actualiza un equipo existente
    Params: id del equipo a actualizar
    Body: JSON con datos actualizados del equipo
    Returns: JSON con confirmación de actualización exitosa
    """
    connection = get_db_connection()
    try:
        datos = request.get_json()
        if not datos:
            return jsonify({'ok': False, 'error': 'No hay datos'}), 400
        
        # Actualizar equipo usando consulta parametrizada
        sql = """UPDATE equipos SET 
                 codigo=%s, tipo=%s, marcas=%s, modelo=%s, so=%s, 
                 almacenamiento=%s, ram=%s, estado=%s, mantenimiento=%s 
                 WHERE id=%s"""
        
        valores = (
            datos.get('codigo'),
            datos.get('tipo'),
            datos.get('marcas'),
            datos.get('modelo'),
            datos.get('so'),
            datos.get('almacenamiento'),
            datos.get('ram'),
            datos.get('estado'),
            datos.get('mantenimiento'),
            id
        )
        
        with connection.cursor() as cursor:
            cursor.execute(sql, valores)
        connection.commit()
        
        return jsonify({'ok': True, 'mensaje': 'Equipo actualizado exitosamente'}), 200
        
    except pymysql.Error as e:
        import traceback
        print(f"Error MySQL: {str(e)}")
        print(traceback.format_exc())
        connection.rollback()
        return jsonify({'ok': False, 'error': 'Error en la base de datos'}), 500
    except Exception as e:
        print(f"Error inesperado: {str(e)}")
        return jsonify({'ok': False, 'error': 'Error del servidor'}), 500
    finally:
        connection.close()

@app.route('/api/equipos/<int:id>', methods=['DELETE'])
def eliminar_equipo(id):
    """
    DELETE /api/equipos/<id> - Elimina un equipo
    Params: id del equipo a eliminar
    Returns: JSON con confirmación de eliminación exitosa
    """
    connection = get_db_connection()
    try:
        # Eliminar equipo de la base de datos
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM equipos WHERE id=%s", (id,))
        connection.commit()
        
        return jsonify({'ok': True, 'mensaje': 'Equipo eliminado exitosamente'}), 200
        
    except pymysql.Error as e:
        import traceback
        print(f"Error MySQL: {str(e)}")
        print(traceback.format_exc())
        connection.rollback()
        return jsonify({'ok': False, 'error': 'Error en la base de datos'}), 500
    except Exception as e:
        print(f"Error inesperado: {str(e)}")
        return jsonify({'ok': False, 'error': 'Error del servidor'}), 500
    finally:
        connection.close()

if __name__ == '__main__':
    puerto = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=puerto, debug=True)