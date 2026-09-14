import time
import os

from flask import Flask, jsonify, request, render_template
from werkzeug.exceptions import HTTPException

from solver_api import InvalidScenarioError, solve_scenario, solve_views
import solver_api

app = Flask(__name__, static_folder='../static/dist',
            template_folder='../static')
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

# Configuration
IsDebugEnv = os.environ.get('FLASK_DEBUG') == "1"
solver_api.set_debug_env(IsDebugEnv)

title = 'Gloomhaven Monster Mover'
version_major = 3
version_minor = 0
version_build = 0
version = f'{version_major}.{version_minor}.{version_build}'
client_local_storage_version_major = 2
client_local_storage_version_minor = 0
client_local_storage_version_build = 0
client_local_storage_version = (
    f'{client_local_storage_version_major}.'
    f'{client_local_storage_version_minor}.'
    f'{client_local_storage_version_build}'
)

# Routes


@app.errorhandler(Exception)
def handle_unexpected_error(exc: Exception):
    """Ensure API clients always get a JSON error body, even for unexpected bugs.

    HTTP exceptions (404, 405, ...) are left to Flask's normal handling.
    """
    if isinstance(exc, HTTPException):
        return exc
    if IsDebugEnv:
        raise exc
    app.logger.exception('Unhandled exception while processing request')
    return jsonify({'error': 'internal server error'}), 500


@app.route('/isAlive')
def isAlive():
    return jsonify("ok")


@app.route('/')
def root():
    return templates('index.html')


@app.route('/los')
def los() -> str:
    return templates('index.html', params={
        'los_mode': True,
    })


def templates(filename: str, params: dict[str, bool] | None = None) -> str:
    template_version = version
    if IsDebugEnv:
        template_version += '.' + str(time.time())

    return render_template(
        filename,
        debug_server=IsDebugEnv,
        title=title,
        version=template_version,
        client_local_storage_version=client_local_storage_version,
        client_local_storage_version_major=client_local_storage_version_major,
        client_local_storage_version_minor=client_local_storage_version_minor,
        client_local_storage_version_build=client_local_storage_version_build,
        **(params or {})
    )


@app.route('/solve', methods=['PUT'])
def solve():
    try:
        solution = solve_scenario(request.data)
    except InvalidScenarioError as exc:
        return jsonify({'error': str(exc)}), 400

    return jsonify(solution)


@app.route('/views', methods=['PUT'])
def views():
    try:
        solution = solve_views(request.data)
    except InvalidScenarioError as exc:
        return jsonify({'error': str(exc)}), 400

    return jsonify(solution)
