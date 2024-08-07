from pathlib import Path
import sys
service_path = Path(__file__).parent.parent
sys.path.append(str(service_path))
import src.migration_models
from flask_mail import Mail
from src.config import Config
from flask import Flask
from src.orm import db





app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)


mail = Mail(app)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG == "1")
