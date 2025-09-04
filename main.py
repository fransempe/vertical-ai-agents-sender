from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import os
from dotenv import load_dotenv
from email_service import EmailService
import tempfile
import uuid

# Cargar variables de entorno
load_dotenv()

app = FastAPI(
    title="Email Sender API",
    description="API sencilla para envío de emails",
    version="1.0.0"
)

# Modelos Pydantic
class EmailRequest(BaseModel):
    to_emails: List[EmailStr]
    subject: str
    body: str
    cc_emails: Optional[List[EmailStr]] = None
    bcc_emails: Optional[List[EmailStr]] = None
    is_html: Optional[bool] = False

class SimpleEmailRequest(BaseModel):
    to_email: EmailStr
    subject: str
    body: str

class EmailResponse(BaseModel):
    status: str
    message: str
    recipients: Optional[int] = None

# Configuración del servicio de email
def get_email_service():
    return EmailService(
        smtp_server=os.getenv("SMTP_SERVER", "smtp.gmail.com"),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        username=os.getenv("SMTP_USERNAME"),
        password=os.getenv("SMTP_PASSWORD"),
        sender_email=os.getenv("SENDER_EMAIL"),
        sender_name=os.getenv("SENDER_NAME", "Email Sender API")
    )

@app.get("/")
async def root():
    return {
        "message": "Email Sender API",
        "version": "1.0.0",
        "endpoints": [
            "/send-email - POST: Envía emails con opciones avanzadas",
            "/send-simple-email - POST: Envía un email simple",
            "/health - GET: Verificar estado de la API"
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API funcionando correctamente"}

@app.post("/send-email", response_model=EmailResponse)
async def send_email(email_request: EmailRequest):
    """
    Envía un email con opciones avanzadas (CC, BCC, HTML)
    """
    try:
        email_service = get_email_service()
        
        if not email_service.username or not email_service.password:
            raise HTTPException(
                status_code=500, 
                detail="Configuración SMTP incompleta. Verifica las variables de entorno."
            )
        
        result = email_service.send_email(
            to_emails=email_request.to_emails,
            subject=email_request.subject,
            body=email_request.body,
            cc_emails=email_request.cc_emails,
            bcc_emails=email_request.bcc_emails,
            is_html=email_request.is_html
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        
        return EmailResponse(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.post("/send-simple-email", response_model=EmailResponse)
async def send_simple_email(email_request: SimpleEmailRequest):
    """
    Envía un email simple a un solo destinatario
    """
    try:
        email_service = get_email_service()
        
        if not email_service.username or not email_service.password:
            raise HTTPException(
                status_code=500, 
                detail="Configuración SMTP incompleta. Verifica las variables de entorno."
            )
        
        result = email_service.send_simple_email(
            to_email=email_request.to_email,
            subject=email_request.subject,
            body=email_request.body
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        
        return EmailResponse(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.post("/send-email-with-attachment")
async def send_email_with_attachment(
    to_emails: str,
    subject: str,
    body: str,
    file: UploadFile = File(...),
    cc_emails: Optional[str] = None,
    is_html: Optional[bool] = False
):
    """
    Envía un email con archivo adjunto
    """
    try:
        email_service = get_email_service()
        
        if not email_service.username or not email_service.password:
            raise HTTPException(
                status_code=500, 
                detail="Configuración SMTP incompleta. Verifica las variables de entorno."
            )
        
        # Guardar archivo temporal
        temp_dir = tempfile.gettempdir()
        temp_filename = f"{uuid.uuid4()}_{file.filename}"
        temp_filepath = os.path.join(temp_dir, temp_filename)
        
        with open(temp_filepath, "wb") as temp_file:
            content = await file.read()
            temp_file.write(content)
        
        try:
            # Convertir strings a listas
            to_emails_list = [email.strip() for email in to_emails.split(",")]
            cc_emails_list = [email.strip() for email in cc_emails.split(",")] if cc_emails else None
            
            result = email_service.send_email(
                to_emails=to_emails_list,
                subject=subject,
                body=body,
                cc_emails=cc_emails_list,
                attachments=[temp_filepath],
                is_html=is_html
            )
            
            if result["status"] == "error":
                raise HTTPException(status_code=500, detail=result["message"])
            
            return EmailResponse(**result)
        
        finally:
            # Limpiar archivo temporal
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    uvicorn.run(app, host="0.0.0.0", port=8004)
    print(f"Iniciando servidor en http://{host}:{port}")
    print("Documentación disponible en: http://localhost:8000/docs")

    uvicorn.run(app, host="0.0.0.0", port=8004)