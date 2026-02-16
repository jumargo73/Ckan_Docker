from alembic.config import Config
from alembic import command
import os

migration_path = "/srv/app/src/ckan/ckanext/csvgeojson/migration/csvgeojson"

cfg = Config(os.path.join(migration_path, "alembic.ini"))

# PON TU URL REAL AQUÍ
cfg.set_main_option("sqlalchemy.url", "postgresql://ckan_default:car2986@db/ckan_default")

command.upgrade(cfg, "head")