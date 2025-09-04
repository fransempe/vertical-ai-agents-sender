# Email Sender API

API sencilla para envío de emails con Python, FastAPI y SMTP.

## Características

- ✉️ Envío de emails simples y avanzados
- 📎 Soporte para archivos adjuntos
- 🎨 Soporte para HTML y texto plano
- 📬 CC y BCC
- 🚀 API REST con FastAPI
- 🔧 Fácil configuración con variables de entorno
- 📚 Documentación automática con Swagger

## Instalación

1. Clona o descarga el proyecto
2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Copia el archivo de configuración:
```bash
copy .env.example .env
```

4. Configura tus credenciales SMTP en el archivo `.env`:
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=tu_email@gmail.com
SMTP_PASSWORD=tu_password_de_app
SENDER_EMAIL=tu_email@gmail.com
SENDER_NAME=Tu Nombre
```

## Configuración Gmail

Para usar Gmail:
1. Activa la verificación en 2 pasos
2. Genera una contraseña de aplicación
3. Usa esa contraseña en `SMTP_PASSWORD`

## Uso

### Iniciar el servidor
```bash
python main.py
```

La API estará disponible en: http://localhost:8000
Documentación: http://localhost:8000/docs

### Endpoints disponibles

#### 1. Email simple
```bash
POST /send-simple-email
Content-Type: application/json

{
    "to_email": "destinatario@example.com",
    "subject": "Asunto del email",
    "body": "Contenido del mensaje"
}
```

#### 2. Email avanzado
```bash
POST /send-email
Content-Type: application/json

{
    "to_emails": ["dest1@example.com", "dest2@example.com"],
    "subject": "Asunto del email",
    "body": "<h1>Contenido HTML</h1>",
    "cc_emails": ["cc@example.com"],
    "bcc_emails": ["bcc@example.com"],
    "is_html": true
}
```

#### 3. Email con archivo adjunto
```bash
POST /send-email-with-attachment
Content-Type: multipart/form-data

to_emails: destinatario@example.com
subject: Email con adjunto
body: Mensaje con archivo
file: [archivo]
```

### Usar desde Python

```python
import requests

# Email simple
response = requests.post("http://localhost:8000/send-simple-email", json={
    "to_email": "test@example.com",
    "subject": "Test",
    "body": "Mensaje de prueba"
})

print(response.json())
```

### Usar desde cURL

```bash
curl -X POST "http://localhost:8000/send-simple-email" \
     -H "Content-Type: application/json" \
     -d '{
         "to_email": "test@example.com",
         "subject": "Test desde cURL",
         "body": "Este es un mensaje de prueba"
     }'
```

## Estructura del proyecto

```
sender-function/
├── main.py              # API FastAPI
├── email_service.py     # Servicio de envío de emails
├── config.py           # Configuración
├── requirements.txt    # Dependencias
├── .env.example       # Ejemplo de configuración
└── README.md         # Documentación
```

## Personalización

El proyecto está diseñado para ser fácilmente adaptable:

- **Cambiar proveedor SMTP**: Modifica las variables en `.env`
- **Agregar validaciones**: Extiende los modelos Pydantic
- **Personalizar respuestas**: Modifica los endpoints en `main.py`
- **Agregar autenticación**: Implementa middleware de seguridad

## Ejemplo de integración

```python
# ejemplo_uso.py
import requests

class EmailClient:
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
    
    def send_email(self, to, subject, body):
        response = requests.post(
            f"{self.api_url}/send-simple-email",
            json={"to_email": to, "subject": subject, "body": body}
        )
        return response.json()

# Uso
client = EmailClient()
result = client.send_email(
    "usuario@example.com", 
    "Notificación", 
    "Tu proceso ha terminado correctamente"
)
print(result)
```

## Notas de seguridad

- No hardcodees credenciales en el código
- Usa variables de entorno para configuración sensible
- Considera implementar rate limiting para producción
- Valida siempre las direcciones de email
- Usa HTTPS en producción