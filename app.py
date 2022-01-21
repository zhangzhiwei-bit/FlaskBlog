from flask_migrate import Migrate
from exts import db
from apps import create_app
from apps.user.models import *
from apps.article.models import *

app = create_app()
migerate = Migrate(app=app, db=db)
# app.register_blueprint(user_bp)


if __name__ == '__main__':
    app.run()