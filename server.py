from flask import Flask, request, jsonify
from flask_cors import CORS
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import csv
import os

app = Flask(__name__)
CORS(app)

# --- CONFIGURACIÓN DE TU CORREO (GMAIL) ---
# Leemos las variables. Si no existen, SENDER_EMAIL será None.
SENDER_EMAIL = os.environ.get('proyectopersonaloxxo@gmail.com')  
SENDER_PASSWORD = os.environ.get('ekqrzjokpydqejrm')
# ----------------------------------------------

# --- CONFIGURACIÓN DEL ARCHIVO DE HISTORIAL ---
CSV_FILE = 'reportes.csv'
CSV_HEADERS = ['timestamp', 'tienda', 'quien_reporta', 'categoria', 'prioridad', 'resumen_ejecutivo', 'correo_proveedor', 'detalles']
# ---------------------------------------------------------------------

# --- INICIO DE RUTA DE DIAGNÓSTICO ---
# Esta es una nueva ruta SÓLO para probar si las variables se leyeron.
@app.route('/debug-vars')
def debug_vars():
    print("--- INICIANDO PRUEBA DE DEBUG ---")
    
    email_leido = os.environ.get('SENDER_EMAIL')
    pass_leido = os.environ.get('SENDER_PASSWORD')

    print(f"DEBUG: Variable SENDER_EMAIL leída como: {email_leido}")
    
    if pass_leido:
        # Imprimimos solo el primer y último caracter por seguridad
        print(f"DEBUG: Variable SENDER_PASSWORD leída como: {pass_leido[0]}***{pass_leido[-1]} (¡Encontrada!)")
    else:
        print("DEBUG: Variable SENDER_PASSWORD leída como: None (¡NO ENCONTRADA!)")
        
    print("--- FIN DE PRUEBA DE DEBUG ---")
    
    if email_leido and pass_leido:
        return "VARIABLES ENCONTRADAS. Revisa los logs."
    else:
        return "ERROR: VARIABLES NO ENCONTRADAS. Revisa los logs."
# --- FIN DE RUTA DE DIAGNÓSTICO ---


@app.route('/enviar_correo', methods=['POST'])
def enviar_correo():
    
    # Añadimos un print aquí también para ver el flujo
    print("--- Se recibió una petición en /enviar_correo ---")

    try:
        data = request.json
        
        # Obtener el resumen ejecutivo
        resumen_ejecutivo = data.get('resumen_ejecutivo', 'Resumen no generado.')
        
        # Validación de credenciales
        if not SENDER_EMAIL or not SENDER_PASSWORD:
            # Si el código llega aquí, es 100% seguro que las variables son None
            print("ERROR DE VALIDACIÓN: 'if not SENDER_EMAIL' falló. Las variables están vacías o son None.")
            return jsonify({"error": "Error de configuración: Correo o Contraseña de Aplicación faltante. Configura las variables de entorno en tu servicio de hosting (Render)."}), 500

        # 1. PREPARAR EL CORREO ELECTRÓNICO
        # (El resto del código de envío sigue igual)
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = data['correo_proveedor']
        msg['Subject'] = f"CRÍTICO | {data['tienda']} - {data['categoria']} - {resumen_ejecutivo}"

        cuerpo_html = f"""
        <html>
        <body>
            <div class="container">
                <div class="header">Nuevo Reporte de Incidencia OXXO</div>
                <div class="resumen">
                    Resumen Ejecutivo (IA): {resumen_ejecutivo}
                </div>
                <div class="content">
                    <p><strong>Tienda:</strong> {data['tienda']}</p>
                    <p><strong>Reportado por:</strong> {data['quien_reporta']}</p>
                    <p><strong>Prioridad:</strong> {data['prioridad'].upper()}</p>
                    <p><strong>Categoría:</strong> {data['categoria']}</p>
                    <hr>
                    <p><strong>Detalles del Reporte Completo:</strong></p>
                    <div class="details">{data['detalles']}</div>
                </div>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(cuerpo_html, 'html'))

        # 2. ENVIAR EL CORREO
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        texto_del_mensaje = msg.as_string()
        server.sendmail(SENDER_EMAIL, data['correo_proveedor'], texto_del_mensaje)
        server.quit()

        # 3. GUARDAR EN EL HISTORIAL (CSV)
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            file_exists = os.path.isfile(CSV_FILE)
            with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
                if not file_exists:
                    writer.writeheader()
                writer.writerow({
                    'timestamp': now, 'tienda': data['tienda'], 'quien_reporta': data['quien_reporta'],
                    'categoria': data['categoria'], 'prioridad': data['prioridad'], 'resumen_ejecutivo': resumen_ejecutivo,
                    'correo_proveedor': data['correo_proveedor'], 'detalles': data['detalles']
                })
        except Exception as e_csv:
            print(f"ADVERTENCIA: Correo enviado, pero falló el guardado en CSV local: {e_csv}")
            
        return jsonify({"mensaje": "¡Reporte enviado y procesado por el servidor online!"}), 200

    except Exception as e:
        print(f"Error en /enviar_correo: {e}")
        return jsonify({"error": f"Error al enviar el correo: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 SERVIDOR PYTHON (FLASK) INICIADO (Modo Online) en puerto {port}")
    app.run(host='0.0.0.0', port=port)
