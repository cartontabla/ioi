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

# Simple camera view (no dashboard needed)
@app.route('/view')
def view():
    from flask import make_response
    html = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>IOI Camera</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { background: #111; color: #eee; font-family: sans-serif; padding: 20px; }
    h1 { font-size: 15px; color: #0eb8c0; margin-bottom: 16px; letter-spacing: 1px; }
    .panels { display: flex; gap: 16px; flex-wrap: wrap; }
    .panel { flex: 1; min-width: 280px; }
    .panel h2 { font-size: 12px; color: #666; text-transform: uppercase;
                letter-spacing: 1px; margin-bottom: 8px; }
    img { width: 100%; border-radius: 4px; display: block; background: #222; min-height: 180px; }
    button { background: #097479; color: #fff; border: none; padding: 10px 20px;
             border-radius: 4px; cursor: pointer; font-size: 13px; margin-top: 12px; }
    button:hover { background: #0eb8c0; }
    button:disabled { background: #333; color: #666; cursor: default; }
    #status { font-size: 11px; color: #666; margin-top: 8px; min-height: 16px; }
    #captured { min-height: 180px; object-fit: contain; }
  </style>
</head>
<body>
  <h1>IOI</h1>
  <div class="panels">
    <div class="panel">
      <h2>Live stream</h2>
      <img src="/stream" alt="live">
    </div>
    <div class="panel">
      <h2>Capture</h2>
      <img id="captured" alt="no capture yet">
      <button id="btn" onclick="capture()">Capture Frame</button>
      <div id="status"></div>
    </div>
  </div>
  <script>
    async function capture() {
      const btn = document.getElementById('btn');
      const status = document.getElementById('status');
      btn.disabled = true;
      status.textContent = 'Capturing...';
      try {
        const fr = await fetch('/api/capture/frame', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: '{}'
        }).then(r => r.json());
        if (!fr.ok) { status.textContent = 'Error: ' + fr.reason; return; }
        status.textContent = 'Generating preview...';
        const pr = await fetch('/api/blocks/preview', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({image_path: fr.frame.image_path})
        }).then(r => r.json());
        if (!pr.ok) { status.textContent = 'Preview error'; return; }
        document.getElementById('captured').src = pr.http_path + '?t=' + Date.now();
        status.textContent = fr.frame.frame_id;
      } catch(e) {
        status.textContent = 'Error: ' + e.message;
      } finally {
        btn.disabled = false;
      }
    }
  </script>
</body>
</html>"""
    r = make_response(html)
    r.headers['Content-Type'] = 'text/html; charset=utf-8'
    return r
