from flask import Flask, jsonify


def create_app():
    app = Flask(__name__)

    # Register routes
    from .routes.main import main

    app.register_blueprint(main)

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal server error"}), 500

    return app
