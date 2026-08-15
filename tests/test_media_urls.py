import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app, build_media_url, get_upload_folder


def test_build_media_url_uses_configured_public_base_url():
    app.config['PUBLIC_BASE_URL'] = 'https://onyangosfamily.onrender.com'
    assert build_media_url('avatar.png') == 'https://onyangosfamily.onrender.com/uploads/avatar.png'


def test_build_media_url_keeps_external_urls():
    assert build_media_url('https://example.com/photo.jpg') == 'https://example.com/photo.jpg'


def test_get_upload_folder_uses_env_override():
    previous = os.environ.get('UPLOAD_FOLDER')
    os.environ['UPLOAD_FOLDER'] = '/tmp/family_uploads'
    try:
        assert get_upload_folder() == '/tmp/family_uploads'
    finally:
        if previous is None:
            os.environ.pop('UPLOAD_FOLDER', None)
        else:
            os.environ['UPLOAD_FOLDER'] = previous


def test_get_upload_folder_uses_render_disk_path():
    previous_upload = os.environ.get('UPLOAD_FOLDER')
    previous_render = os.environ.get('RENDER_DISK_PATH')
    os.environ.pop('UPLOAD_FOLDER', None)
    os.environ['RENDER_DISK_PATH'] = '/var/lib/render/projectdata'
    try:
        assert get_upload_folder() == '/var/lib/render/projectdata/uploads'
    finally:
        if previous_upload is None:
            os.environ.pop('UPLOAD_FOLDER', None)
        else:
            os.environ['UPLOAD_FOLDER'] = previous_upload
        if previous_render is None:
            os.environ.pop('RENDER_DISK_PATH', None)
        else:
            os.environ['RENDER_DISK_PATH'] = previous_render
