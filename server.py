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
# CAMBIO CLAVE DE SEGURIDAD: Leer el correo y la contraseña de las variables de entorno de Render
SENDER_EMAIL = os.environ.get('proyectopersonaloxxo@gmail.com')  
SENDER_PASSWORD = os.environ.get('ekqrzjokpydqejrm')
# ----------------------------------------------

# --- CONFIGURACIÓN DEL ARCHIVO DE HISTORIAL (Opcional en la nube) ---
CSV_FILE = 'reportes.csv'
CSV_HEADERS = ['timestamp', 'tienda', 'quien_reporta', 'categoria', 'prioridad', 'resumen_ejecutivo', 'correo_proveedor', 'detalles']
# ---------------------------------------------------------------------

@app.route('/enviar_correo', methods=['POST'])
def enviar_correo():
    try:
        data = request.json
        
        # Obtener el resumen ejecutivo (nuevo campo)
        resumen_ejecutivo = data.get('resumen_ejecutivo', 'Resumen no generado.')
        
        # Validación de credenciales
        if not SENDER_EMAIL or not SENDER_PASSWORD:
            return jsonify({"error": "Error de configuración: Correo o Contraseña de Aplicación faltante. Configura las variables de entorno en tu servicio de hosting (Render)."}), 500

        # 1. PREPARAR EL CORREO ELECTRÓNICO
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = data['correo_proveedor']
        
        # Usamos el resumen en el asunto para que sea más informativo
        msg['Subject'] = f"CRÍTICO | {data['tienda']} - {data['categoria']} - {resumen_ejecutivo}"

        # Añadimos 'quien_reporta' y 'resumen_ejecutivo' al cuerpo del correo
        cuerpo_html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .container {{ max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
                .header {{ font-size: 24px; color: #D90000; }}
                .resumen {{ font-size: 16px; font-weight: bold; margin-bottom: 15px; color: #005691; border: 1px solid #e0f2fe; padding: 10px; background-color: #f0f8ff; border-radius: 4px;}}
                .priority-Alta {{ color: #D90000; font-weight: bold; }}
                .priority-Media {{ color: #F28C00; font-weight: bold; }}
                .priority-Baja {{ color: #34A853; font-weight: bold; }}
                .content {{ margin-top: 20px; }}
                .details {{ background-color: #f9f9f9; border: 1px solid #eee; padding: 15px; border-radius: 4px; white-space: pre-wrap; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">Nuevo Reporte de Incidencia OXXO</div>
                <div class="resumen">
                    Resumen Ejecutivo (IA): {resumen_ejecutivo}
                </div>
                <div class="content">
                    <p><strong>Tienda:</strong> {data['tienda']}</p>
                    <p><strong>Reportado por:</strong> {data['quien_reporta']}</p>
                    <p><strong>Prioridad:</strong> <span class="priority-{data['prioridad']}">{data['prioridad'].upper()}</span></p>
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
                    'timestamp': now,
                    'tienda': data['tienda'],
                    'quien_reporta': data['quien_reporta'],
                    'categoria': data['categoria'],
                    'prioridad': data['prioridad'], 
                    'resumen_ejecutivo': resumen_ejecutivo,
                    'correo_proveedor': data['correo_proveedor'],
                    'detalles': data['detalles']
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
