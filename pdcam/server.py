from flask import Flask, Response, render_template, request
import json
import os

from .video import Video


def create_app(grid_reference, grid_layout):
    camera = Video(grid_reference, grid_layout)
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    @app.route('/')
    def index():
        return render_template("index.html")

    @app.route('/video/')
    def video():
        markup = bool(request.args.get('markup', False))
        return Response(
            camera.mjpeg_frame_generator(markup), 
            mimetype = "multipart/x-mixed-replace; boundary=frame")
    
    @app.route('/latest')
    def latest():
        markup = bool(request.args.get('markup', False))
        min_frame = request.headers.get('X-Min-Frame-Number', None)
        if min_frame is None:
            min_frame = request.args.get('min_frame', None)
        if min_frame is not None:
            min_frame = int(min_frame)
        jpeg, frame_num = camera.latest_jpeg(min_frame_num=min_frame, markup=markup)
        return Response(
            jpeg,
            mimetype="image/jpeg",
            headers={'X-Frame-Number': str(frame_num)})

    @app.route('/transform')
    def transform():
        transform = camera.latest_transform()
        if transform is not None:
            transform = transform.tolist()
        return Response(json.dumps(transform), content_type="application/json")
    return app


def main():
    app = create_app()
    app.run()

# Consider running me with: `FLASK_APP=pd-stream flask run --host 0.0.0.0`
if __name__ == '__main__':
    main()