from flask import Flask, Response, send_from_directory
import config

app = Flask(__name__)

# CORS
if config.ENABLE_CORS:
    @app.after_request
    def add_cors_headers(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        return response

# Register API blueprints
from backend.api.capture import bp as capture_bp
from backend.api.project import bp as project_bp
from backend.api.blocks import bp as blocks_bp

app.register_blueprint(capture_bp)
app.register_blueprint(project_bp)
app.register_blueprint(blocks_bp)

# MJPEG stream
if config.ENABLE_MJPEG_STREAM:
    @app.route('/stream')
    def stream():
        from backend.context import camera
        return Response(camera.mjpeg_generator(), mimetype='multipart/x-mixed-replace; boundary=frame')

# File serving (projects directory)
@app.route('/files/<path:filename>')
def serve_file(filename):
    return send_from_directory(config.PROJECTS_DIR, filename, as_attachment=False)
