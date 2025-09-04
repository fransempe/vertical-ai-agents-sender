import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Configuración SMTP
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SENDER_EMAIL = os.getenv("SENDER_EMAIL")
    SENDER_NAME = os.getenv("SENDER_NAME", "Email Sender API")
    
    # Configuración API
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    
    @classmethod
    def validate_config(cls):
        """Valida que la configuración esencial esté presente"""
        required_vars = [
            ("SMTP_USERNAME", cls.SMTP_USERNAME),
            ("SMTP_PASSWORD", cls.SMTP_PASSWORD),
            ("SENDER_EMAIL", cls.SENDER_EMAIL)
        ]
        
        missing_vars = []
        for var_name, var_value in required_vars:
            if not var_value:
                missing_vars.append(var_name)
        
        if missing_vars:
            raise ValueError(f"Variables de entorno faltantes: {', '.join(missing_vars)}")
        
        return True