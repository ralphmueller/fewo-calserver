from flaskr import create_app
from config import Config

application = create_app()

if __name__ == "__main__":
    application.run()
