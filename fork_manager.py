import os
import requests
import logging
import argparse
from configparser import SafeConfigParser

logging.basicConfig(format='[%(asctime)s][%(name)s:%(lineno)s][%(levelname)s] %(message)s',
                    datefmt='%Y/%b/%d %H:%M:%S',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class RepoForker():

    DEFAULT_CONFIG_FILE = './configs/fork_config.cfg'

    def __init__(self, config=None, *args, **kwargs):
        config = config or self.DEFAULT_CONFIG_FILE
        if not os.path.isfile(config):
            raise OSError('Config file not found!')
        self.parser = SafeConfigParser()
        self.parser.optionxform = str
        self.parser.read(config)
        self._validate_config()
        self.user_username = self.parser.get('USER', 'USERNAME')
        self.user_app_pwd = self.parser.get('USER', 'APP_PW')
        self.owner = self.parser.get('OWNER', 'USERNAME')
        self.repo_url = 'https://api.bitbucket.org/2.0/repositories'

    def _validate_config(self):
        sections_options = {'USER': ['USERNAME', 'APP_PW'],
                            'OWNER': ['USERNAME']}
        repo_config = ['ORIGIN_REPO_SLUG',
                       'ORIGIN_PROJECT_KEY',
                       'FORK_REPO_NAME',
                       'FORK_PROJECT_KEY',
                       'LANGUAGE']
        # credentials
        req_sections = sections_options.keys()
        missing_sections = list(set(req_sections) - set(self.parser.sections()))
        if missing_sections:
            raise OSError(f'Missing required sections: {missing_sections}')
        for section, options in sections_options.items():
            opts = dict(self.parser.items(section)).keys()
            missing_options = list(set(options) - set(opts))
            if missing_options:
                raise OSError(f'Missing required options in {section}: {missing_options}')
        # repositories
        repos = list(set(self.parser.sections()) - set(req_sections))
        self.repo_list = []
        for repo in repos:
            if 'REPO' not in repo:
                continue
            self.repo_list.append(repo)
            opts = dict(self.parser.items(repo)).keys()
            missing_options = list(set(repo_config) - set(opts))
            if missing_options:
                raise OSError(f'Missing required options in {repo}: {missing_options}')

    def fork(self):
        forked_repo = 0
        for repo in self.repo_list:
            logger.info(f'Forking {repo}...')
            _is_forked = self._fork_repository(repo)
            if _is_forked:
                logger.info(f'Forking {repo} SUCCESS!')
                forked_repo += 1
            else:
                logger.info(f'Forking {repo} FAILED!')
        logger.info(f'{forked_repo}/{len(self.repo_list)} HAS BEEN FORKED.')

    def _fork_repository(self, repo):
        data = {
            'name': self.parser.get(repo, 'FORK_REPO_NAME')
            'language': self.parser.get(repo, 'LANGUAGE'),
            'owner': {
                'username': self.owner
            },
            'project': {
                'key': self.parser.get(repo, 'FORK_PROJECT_KEY')
            }
        }
        origin_repo_slug = self.parser.get(repo, 'ORIGIN_REPO_SLUG')
        repo_url = f'{self.repo_url}/{self.owner}/{origin_repo_slug}/forks'

        try:
            response = requests.post(repo_url,
                                     json=data,
                                     auth=(self.user_username,
                                           self.user_app_pwd))
            status = response.status_code
            if status == 201:
                return True
        except Exception as e:
            logger.error(e)
        return False


if __name__ == '__main__':

    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config',
                        help='Path to file or directory to be config file',
                        required=False)
    args = parser.parse_args()

    config = args.config or None
    forker = RepoForker(config=config)
    forker.fork()
