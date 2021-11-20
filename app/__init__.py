from flask import Flask
from config import Config
from scrapinghub import ScrapinghubClient
import logging
from logging.handlers import RotatingFileHandler


app = Flask(__name__)
app.config.from_object(Config)

client = ScrapinghubClient(app.config['SCRAPYHUB_APIKEY'])

from app.main import bp as main_bp
app.register_blueprint(main_bp)

from app.sitemap import bp as sitemap_bp
app.register_blueprint(sitemap_bp)

from app.auth import bp as auth_bp
app.register_blueprint(auth_bp)

folder = app.config['BASEDIR'] / 'logs'
if not folder.is_dir():
    folder.mkdir()
file_handler = RotatingFileHandler(folder / 'rent_prop.log', maxBytes=102400,
    backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s'))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)

app.logger.setLevel(logging.INFO)
app.logger.info('Rental Property startup')
