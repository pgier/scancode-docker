
from flask import Flask, request, Response, json
from urlparse import urlparse
import os
import subprocess
import tempfile

CACHE_DIR = '/app/cache'

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
    source_url = request_data["source_url"]
    commit_id = request_data["commit_id"]
    if source_url == '' or commit_id == '':
        return display_help()
    git_repo_dir, result = git_clone(source_url, commit_id)
    if result != 0:
        return "Error cloning git repo"
    result = git_checkout(git_repo_dir, commit_id)
    if result != 0:
        return "Error checking out commit"
    output_filename = get_project_name(source_url) + "-" + commit_id + ".json"
    run_scancode(git_repo_dir, output_filename)

    with open(output_filename) as scancode_output:
        scancode_result = json.load(scancode_output)
    return Response(json.dumps(scancode_result), mimetype='application/json')


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
    return project_name


def git_checkout(repo_dir, commit):
    return subprocess.call(['git', 'checkout', commit], cwd=repo_dir)


def run_scancode(source_dir, output_file):
    return subprocess.call(["scancode", "--format", "json", source_dir, output_file])


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
