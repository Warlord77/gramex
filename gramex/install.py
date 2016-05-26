import os
import six
import yaml
import shutil
import logging
import datetime
import requests
from pathlib import Path
from orderedattrdict import AttrDict
from zipfile import ZipFile
import gramex
from gramex.config import ChainConfig, PathConfig, variables


def zip_prefix_filter(members, prefix):
    '''
    Return only ZIP file members starting with the directory prefix, with the
    prefix stripped out.
    '''
    if not prefix.endswith('/'):
        prefix += '/'
    offset = len(prefix)
    result = []
    for zipinfo in members:
        if zipinfo.filename.startswith(prefix):
            zipinfo.filename = zipinfo.filename[offset:]
            if len(zipinfo.filename) > 0:
                result.append(zipinfo)
    return result


def download_zip(url, target, contentdir=True, rootdir=None):
    '''
    Download url into path. url can be http, https, ftp. It will be unzipped
    based on its type.
    '''
    if os.path.exists(url):
        handle = url
    else:
        logging.info('Downloading: %s', url)
        response = requests.get(url)
        response.raise_for_status()
        handle = six.BytesIO(response.content)

    zipfile = ZipFile(handle)
    members = zipfile.infolist()
    if contentdir:
        members = zip_prefix_filter(members, os.path.commonprefix(zipfile.namelist()))
    if rootdir is not None:
        members = zip_prefix_filter(members, rootdir)

    if os.path.exists(target):
        shutil.rmtree(target)
    zipfile.extractall(target, members)

    logging.info('Extracted: %s', target)


app_dir = Path(variables.get('GRAMEXDATA')) / 'apps'
if not app_dir.exists():
    app_dir.mkdir(parents=True)

# Get app configuration by chaining apps.yaml in gramex + app_dir + command line
apps_config = ChainConfig()
apps_config['base'] = PathConfig(gramex.paths['source'] / 'apps.yaml')
user_config_file = app_dir / 'apps.yaml'
apps_config['user'] = PathConfig(user_config_file)


def save_user_config(appname, value):
    user_config = AttrDict()
    if user_config_file.exists():
        with user_config_file.open(encoding='utf-8') as handle:
            user_config = yaml.load(handle)
    if value is None:
        if appname in user_config:
            del user_config[appname]
    else:
        app_config = user_config.setdefault(appname, AttrDict())
        app_config.update(value)
        app_config['installed_time'] = datetime.datetime.utcnow()

    with user_config_file.open(mode='w', encoding='utf-8') as handle:
        yaml.dump(user_config, handle, indent=4, default_flow_style=False)


def get_app_config(appname, args):
    apps_config['cmd'] = {appname: args}
    app_config = (+apps_config).get(appname, {})
    app_config.target = str(app_dir / app_config.get('target', appname))
    return app_config

def install(cmd, args):
    if len(cmd) < 1:
        apps = (+apps_config).keys()
        logging.error('gramex install [%s]', '|'.join(apps))
        return

    appname = cmd.pop(0)
    logging.info('Installing: %s', appname)

    app_config = get_app_config(appname, args)
    # Download the app URL into target directory
    if 'url' in app_config:
        download_zip(
            url=app_config.url,
            target=app_config.target,
            contentdir=app_config.get('contentdir', True),
            rootdir=app_config.get('rootdir', None),
        )
        save_user_config(appname, app_config)
    else:
        logging.error('Cannot find URL to install %s. Use --url=...', appname)


def uninstall(cmd, args):
    if len(cmd) < 1:
        apps = (+apps_config['user']).keys()
        logging.error('gramex uninstall [%s]', '|'.join(apps))
        return

    appname = cmd.pop(0)
    logging.info('Uninstalling: %s', appname)

    # Delete the target directory if it exists
    app_config = get_app_config(appname, args)
    if os.path.exists(app_config.target):
        if app_config.target.startswith(variables['GRAMEXDATA']):
            shutil.rmtree(app_config.target)
        else:
            logging.warn('Not removing directory %s (outside $GRAMEXDATA)', app_config.target)
    else:
        logging.error('No directory %s to remove', app_config.target)
    save_user_config(appname, None)


def run(cmd, args):
    if len(cmd) < 1:
        apps = (+apps_config['user']).keys()
        logging.error('gramex run [%s]', '|'.join(apps))
        return

    appname = cmd.pop(0)
    logging.info('Initializing %s on Gramex %s', appname, gramex.__version__)

    app_config = get_app_config(appname, args)
    if os.path.exists(app_config.target):
        os.chdir(app_config.target)
        gramex.paths['base'] = Path('.')
        gramex.init(cmd=AttrDict(app=args))
    else:
        logging.error('No directory %s to run', app_config.target)