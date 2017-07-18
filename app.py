
from flask import Flask, request, Response
from urlparse import urlparse
import os
import shutil
import subprocess
import tempfile

CACHE_DIR = '/app/cache'
DEFAULT_RESULT_FORMAT = 'json'

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

app = Flask(__name__)


@app.route('/')
def handle_get():
    return display_help()


@app.route('/', methods=['POST'])
def scan_project():
    if not request.is_json:
        return "Post data must be json format"

    request_data = request.get_json()

    if 'source_url' not in request_data:
        return display_help()
    source_url = request_data['source_url']

    if 'commit_id' not in request_data:
        return display_help()
    commit_id = request_data['commit_id']

    format_param = DEFAULT_RESULT_FORMAT
    if 'format' in request_data:
        format_param = request_data['format']

    license_info_filename = CACHE_DIR + '/' + get_project_name(source_url) + "-" + commit_id \
                            + "." + format_param
    if not os.path.exists(license_info_filename):
        git_repo_temp_dir, result = git_clone(source_url, commit_id)
        if result != 0:
            return "Error cloning git repo"
        result = git_checkout(git_repo_temp_dir, commit_id)
        if result != 0:
            return "Error checking out commit"
        run_scancode(git_repo_temp_dir, license_info_filename, format_param)
        shutil.rmtree(git_repo_temp_dir, ignore_errors=True)

    with open(license_info_filename, "r") as license_info_file:
        license_info = license_info_file.readlines()

    mimetype = 'text/plain'
    if format_param == 'json' or format_param == 'json-pp':
        mimetype = 'application/json'
    elif format_param == 'html':
        mimetype = 'text/html'

    return Response(license_info, mimetype=mimetype)


def display_help():
    return 'Please submit a POST request with json content.  {"source_url":"<url>", "commit_id":"<commit>"}'


def git_clone(source_url, commit):
    project_name = get_project_name(source_url)
    git_repo_dir = tempfile.mkdtemp(prefix=project_name, suffix="-" + commit)
    result = subprocess.call(['git', 'clone', source_url, git_repo_dir])
    return git_repo_dir, result


def get_project_name(source_url):
    parsed_url = urlparse(source_url)
    _, project_name = os.path.split(parsed_url.path)
    project_name = os.path.splitext(project_name)[0]
    return project_name


def git_checkout(repo_dir, commit):
    return subprocess.call(['git', 'checkout', commit], cwd=repo_dir)


def run_scancode(source_dir, output_file, format_param):
    return subprocess.call(["scancode", "--format", format_param, source_dir, output_file])


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
