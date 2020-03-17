from flask import Flask
from config import Config
from scrapinghub import ScrapinghubClient


app = Flask(__name__)
app.config.from_object(Config)

client = ScrapinghubClient(app.config['SCRAPYHUB_APIKEY'])

from app.main import bp as main_bp
app.register_blueprint(main_bp)

from app.sitemap import bp as sitemap_bp
app.register_blueprint(sitemap_bp)
