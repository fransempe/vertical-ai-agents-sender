import smtplib
import ssl
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from typing import List, Optional
import logging
import requests

class EmailService:
    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str, sender_email: str, sender_name: str, sendgrid_api_key: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.sender_email = sender_email
        self.sender_name = sender_name
        self.sendgrid_api_key = sendgrid_api_key
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Alternativas de configuración para Railway
        self.fallback_configs = [
            {'server': 'smtp.gmail.com', 'port': 587, 'ssl': False},
            {'server': 'smtp.gmail.com', 'port': 465, 'ssl': True},
            {'server': 'smtp-mail.outlook.com', 'port': 587, 'ssl': False},
            {'server': 'smtp.sendgrid.net', 'port': 587, 'ssl': False},
        ]
    
    def test_connectivity(self) -> dict:
        """Probar conectividad a diferentes servidores SMTP"""
        results = {}
        
        # Probar configuración actual
        current_config = f"{self.smtp_server}:{self.smtp_port}"
        results[current_config] = self._test_smtp_connection(self.smtp_server, self.smtp_port)
        
        # Probar configuraciones alternativas
        for config in self.fallback_configs:
            config_name = f"{config['server']}:{config['port']}"
            if config_name != current_config:
                results[config_name] = self._test_smtp_connection(config['server'], config['port'])
        
        return results
    
    def _test_smtp_connection(self, server: str, port: int, timeout: int = 10) -> dict:
        """Probar conexión a un servidor SMTP específico"""
        try:
            self.logger.info(f"Probando conexión a {server}:{port}")
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((server, port))
            sock.close()
            
            if result == 0:
                return {"status": "reachable", "message": "Conexión exitosa"}
            else:
                return {"status": "unreachable", "message": f"Error de conexión: {result}"}
                
        except socket.gaierror as e:
            return {"status": "dns_error", "message": f"Error DNS: {str(e)}"}
        except Exception as e:
            return {"status": "error", "message": f"Error: {str(e)}"}
    
    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
        is_html: bool = False,
        use_fallback: bool = True
    ) -> dict:
        """Enviar email con fallback automático si la conexión principal falla"""
        
        # Intentar con configuración principal
        result = self._attempt_send_email(
            self.smtp_server, self.smtp_port, False,
            to_emails, subject, body, cc_emails, bcc_emails, attachments, is_html
        )
        
        if result["status"] == "success":
            return result
        
        if not use_fallback:
            return result
        
        # Si falla, intentar con configuraciones alternativas
        self.logger.warning(f"Fallo principal: {result['message']}. Intentando configuraciones alternativas...")
        
        for config in self.fallback_configs:
            if config['server'] == self.smtp_server and config['port'] == self.smtp_port:
                continue  # Ya intentamos esta configuración
            
            self.logger.info(f"Intentando con {config['server']}:{config['port']}")
            
            result = self._attempt_send_email(
                config['server'], config['port'], config['ssl'],
                to_emails, subject, body, cc_emails, bcc_emails, attachments, is_html
            )
            
            if result["status"] == "success":
                result["fallback_used"] = f"{config['server']}:{config['port']}"
                return result
        
        # Si todos fallan, sugerir usar API
        return {
            "status": "error",
            "message": "Todos los servidores SMTP fallaron. Considera usar SendGrid API.",
            "suggestion": "use_sendgrid_api",
            "connectivity_test": self.test_connectivity()
        }
    
    def _attempt_send_email(
        self,
        smtp_server: str,
        smtp_port: int,
        use_ssl: bool,
        to_emails: List[str],
        subject: str,
        body: str,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
        is_html: bool = False
    ) -> dict:
        """Intentar enviar email con una configuración específica"""
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
            
            # Preparar lista de destinatarios
            all_recipients = to_emails.copy()
            if cc_emails:
                all_recipients.extend(cc_emails)
            if bcc_emails:
                all_recipients.extend(bcc_emails)
            
            # Configurar conexión SMTP
            context = ssl.create_default_context()
            
            if use_ssl:
                # Conexión SSL directa (puerto 465)
                server = smtplib.SMTP_SSL(smtp_server, smtp_port, context=context)
            else:
                # Conexión STARTTLS (puerto 587)
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls(context=context)
            
            # Autenticación
            server.login(self.username, self.password)
            
            # Enviar email
            text = msg.as_string()
            server.sendmail(self.sender_email, all_recipients, text)
            server.quit()
            
            self.logger.info(f"Email enviado exitosamente via {smtp_server}:{smtp_port} a {len(all_recipients)} destinatarios")
            
            return {
                "status": "success",
                "message": f"Email enviado exitosamente a {len(all_recipients)} destinatarios",
                "recipients": len(all_recipients),
                "server_used": f"{smtp_server}:{smtp_port}"
            }
            
        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"Error de autenticación SMTP: {str(e)}"
            self.logger.error(error_msg)
            return {"status": "auth_error", "message": error_msg}
            
        except smtplib.SMTPConnectError as e:
            error_msg = f"Error de conexión SMTP a {smtp_server}:{smtp_port}: {str(e)}"
            self.logger.error(error_msg)
            return {"status": "connection_error", "message": error_msg}
            
        except OSError as e:
            if "Network is unreachable" in str(e):
                error_msg = f"Red no alcanzable para {smtp_server}:{smtp_port}. Railway podría estar bloqueando este puerto."
                self.logger.error(error_msg)
                return {"status": "network_unreachable", "message": error_msg}
            else:
                error_msg = f"Error de red: {str(e)}"
                self.logger.error(error_msg)
                return {"status": "network_error", "message": error_msg}
            
        except Exception as e:
            error_msg = f"Error inesperado enviando email via {smtp_server}:{smtp_port}: {str(e)}"
            self.logger.error(error_msg)
            return {"status": "error", "message": error_msg}
    
    def send_simple_email(self, to_email: str, subject: str, body: str) -> dict:
        """Método simplificado para envío básico de emails"""
        return self.send_email([to_email], subject, body)
    
    def send_via_sendgrid_api(
        self,
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = False
    ) -> dict:
        """Alternativa usando SendGrid API cuando SMTP falla"""
        api_key = self.sendgrid_api_key
        
        if not api_key:
            return {
                "status": "error",
                "error_type": "config_missing",
                "message": "SENDGRID_API_KEY no configurado. Configúralo en Railway para usar esta alternativa.",
                "solution": "Agrega SENDGRID_API_KEY en Railway → Settings → Variables"
            }
        
        # Verificar que el email remitente esté configurado
        if not self.sender_email:
            return {
                "status": "error",
                "error_type": "sender_missing",
                "message": "EMAIL_FROM no configurado",
                "solution": "Configura EMAIL_FROM en las variables de entorno"
            }
        
        try:
            url = "https://api.sendgrid.com/v3/mail/send"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            content_type = "text/html" if is_html else "text/plain"
            
            data = {
                "personalizations": [{
                    "to": [{"email": to_email}]
                }],
                "from": {
                    "email": self.sender_email,
                    "name": self.sender_name
                },
                "subject": subject,
                "content": [{
                    "type": content_type,
                    "value": body
                }]
            }
            
            self.logger.info(f"Enviando email via SendGrid API de {self.sender_email} a {to_email}")
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 202:
                self.logger.info(f"Email enviado exitosamente via SendGrid API a {to_email}")
                return {
                    "status": "success",
                    "message": f"Email enviado via SendGrid API a {to_email}",
                    "method": "sendgrid_api",
                    "recipient": to_email
                }
            elif response.status_code == 401:
                return {
                    "status": "error",
                    "error_type": "authentication",
                    "message": "API Key de SendGrid inválida",
                    "solution": "Verifica que SENDGRID_API_KEY sea correcta en Railway"
                }
            elif response.status_code == 403:
                try:
                    error_data = response.json()
                    errors = error_data.get('errors', [])
                    
                    # Verificar si es problema de identidad del remitente
                    sender_identity_error = any(
                        'sender identity' in error.get('message', '').lower() or
                        'from address' in error.get('message', '').lower()
                        for error in errors
                    )
                    
                    if sender_identity_error:
                        return {
                            "status": "error",
                            "error_type": "sender_not_verified",
                            "message": f"El email {self.sender_email} no está verificado en SendGrid",
                            "sendgrid_errors": errors,
                            "solution": {
                                "step_1": "Ve a https://app.sendgrid.com/settings/sender_auth",
                                "step_2": "Click en 'Verify a Single Sender'",
                                "step_3": f"Verifica el email: {self.sender_email}",
                                "step_4": "Revisa tu email y confirma la verificación",
                                "step_5": "Asegúrate de que EMAIL_FROM coincida exactamente con el email verificado"
                            }
                        }
                    else:
                        return {
                            "status": "error",
                            "error_type": "forbidden",
                            "message": "Acceso denegado por SendGrid",
                            "sendgrid_errors": errors,
                            "response_code": response.status_code
                        }
                except:
                    return {
                        "status": "error",
                        "error_type": "forbidden",
                        "message": f"SendGrid API error 403: {response.text}",
                        "solution": "Verifica la configuración de SendGrid Sender Authentication"
                    }
            elif response.status_code == 400:
                try:
                    error_data = response.json()
                    return {
                        "status": "error",
                        "error_type": "bad_request",
                        "message": "Error en los datos enviados a SendGrid",
                        "sendgrid_errors": error_data.get('errors', []),
                        "sent_data": {
                            "from": self.sender_email,
                            "to": to_email,
                            "subject": subject
                        }
                    }
                except:
                    return {
                        "status": "error",
                        "error_type": "bad_request",
                        "message": f"SendGrid API error 400: {response.text}"
                    }
            else:
                return {
                    "status": "error",
                    "error_type": f"api_error_{response.status_code}",
                    "message": f"SendGrid API error: {response.status_code}",
                    "response": response.text[:500] if len(response.text) > 500 else response.text
                }
            
        except requests.exceptions.ConnectionError as e:
            return {
                "status": "error",
                "error_type": "connection_error",
                "message": "No se pudo conectar a SendGrid API",
                "details": str(e),
                "solution": "Verifica la conexión a internet desde Railway"
            }
        except requests.exceptions.Timeout as e:
            return {
                "status": "error",
                "error_type": "timeout",
                "message": "Timeout conectando a SendGrid API",
                "details": str(e)
            }
        except Exception as e:
            self.logger.error(f"Error inesperado con SendGrid API: {str(e)}")
            return {
                "status": "error",
                "error_type": "unexpected_error",
                "message": f"Error inesperado con SendGrid API: {str(e)}"
            }
    
    def send_email_with_api_fallback(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
        is_html: bool = False
    ) -> dict:
        """Enviar email intentando SMTP primero, luego API como fallback"""
        
        # Intentar SMTP primero
        result = self.send_email(to_emails, subject, body, cc_emails, bcc_emails, attachments, is_html)
        
        if result["status"] == "success":
            return result
        
        # Si SMTP falla y no hay adjuntos, intentar con SendGrid API
        if not attachments and not cc_emails and not bcc_emails:
            self.logger.warning("SMTP falló, intentando con SendGrid API...")
            return self.send_via_sendgrid_api(to_emails, subject, body, is_html)
        
        return result