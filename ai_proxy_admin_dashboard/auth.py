from werkzeug.security import check_password_hash, generate_password_hash
from sqlite_logger import init_db

ADMIN_HASH = generate_password_hash("adminpassword123")

init_db()

def check_admin_password(password):
    return check_password_hash(ADMIN_HASH, password) 
