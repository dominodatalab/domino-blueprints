"""Study Publisher - Domino Flask App entrypoint."""
import os
from flask_app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('APP_PORT', 8888))
    app.run(host='0.0.0.0', port=port, debug=False)
