from ommat import create_app
from ommat.config import Config
from ommat.crawler.utils import Analyser
from ommat.crawler import crawler_run

app = create_app(Config)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
