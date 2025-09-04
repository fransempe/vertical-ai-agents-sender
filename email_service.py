import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from typing import List, Optional
import logging

class EmailService:
    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str, sender_email: str, sender_name: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.sender_email = sender_email
        self.sender_name = sender_name
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
        is_html: bool = False
    ) -> dict:
        try:
            msg = MIMEMultipart()
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = ", ".join(to_emails)
            msg['Subject'] = subject
            
            if cc_emails:
                msg['Cc'] = ", ".join(cc_emails)
            
            # Agregar el cuerpo del mensaje
            mime_type = 'html' if is_html else 'plain'
            msg.attach(MIMEText(body, mime_type, 'utf-8'))
            
            # Agregar archivos adjuntos si los hay
            if attachments:
                for file_path in attachments:
                    if os.path.isfile(file_path):
                        with open(file_path, "rb") as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                        
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {os.path.basename(file_path)}'
                        )
                        msg.attach(part)
            
            # Configurar conexión SMTP
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            
            # Preparar lista de destinatarios
            all_recipients = to_emails.copy()
            if cc_emails:
                all_recipients.extend(cc_emails)
            if bcc_emails:
                all_recipients.extend(bcc_emails)
            
            # Enviar email
            text = msg.as_string()
            server.sendmail(self.sender_email, all_recipients, text)
            server.quit()
            
            self.logger.info(f"Email enviado exitosamente a {len(all_recipients)} destinatarios")
            
            return {
                "status": "success",
                "message": f"Email enviado exitosamente a {len(all_recipients)} destinatarios",
                "recipients": len(all_recipients)
            }
            
        except Exception as e:
            self.logger.error(f"Error al enviar email: {str(e)}")
            return {
                "status": "error",
                "message": f"Error al enviar email: {str(e)}"
            }
    
    def send_simple_email(self, to_email: str, subject: str, body: str) -> dict:
        """Método simplificado para envío básico de emails"""
        return self.send_email([to_email], subject, body)