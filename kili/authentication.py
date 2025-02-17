"""API authentication module"""
import warnings
from datetime import datetime, timedelta

import requests

from . import __version__
from .graphql_client import GraphQLClient
from .helpers import format_result
from .queries.api_key import QueriesApiKey
from .queries.user.queries import GQL_ME

MAX_RETRIES = 20

warnings.filterwarnings("default", module='kili', category=DeprecationWarning)


def get_version_without_patch(version):
    """Return the version of Kili API removing the patch version.

    Args:
        version
    """
    return '.'.join(version.split('.')[:-1])


class KiliAuth:
    """
    from kili.client import Kili
    kili = Kili(api_key=api_key)
    assets = kili.assets(project_id=project_id)
    """

    def __init__(self,
                 api_key,
                 api_endpoint,
                 verify=True):
        self.session = requests.Session()

        self.verify = verify

        if api_endpoint and 'v1/graphql' in api_endpoint:
            # pylint: disable=line-too-long
            message = 'We are migrating the API to enhance our service,' \
                ' please use the new endpoint https://cloud.kili-technology.com/api/label/v2/graphql' \
                ' (or None), the former endpoint call will be deprecated on February 15th 2021'
            warnings.warn(message, DeprecationWarning)
        try:
            self.check_versions_match(api_endpoint)
        except:  # pylint: disable=bare-except
            message = 'We could not check the version, there might be a version' \
                'mismatch or the app might be in deployment'
            warnings.warn(message, UserWarning)

        adapter = requests.adapters.HTTPAdapter(max_retries=MAX_RETRIES)
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)
        self.client = GraphQLClient(
            api_endpoint, self.session, verify=self.verify)
        self.client.inject_token('X-API-Key: ' + api_key)

        user = self.get_user()

        if (user is None or user['id'] is None or user['email'] is None):
            raise Exception('No user attached to the API key was found')

        self.user_id = user['id']
        self.user_email = user['email']
        self.check_expiry_of_key_is_close(api_key)

    def __del__(self):
        self.session.close()

    def check_versions_match(self, api_endpoint):
        """Check that the versions of Kili Python SDK and Kili API are the same

        Args:
            api_endpoint: url of the Kili API
        """
        url = api_endpoint.replace('/graphql', '/version')
        response = requests.get(url, verify=self.verify).json()
        version = response['version']
        if get_version_without_patch(version) != get_version_without_patch(__version__):
            message = 'Kili Python SDK version should match with Kili API version.\n' + \
                      f'Please install version: "pip install kili=={version}"'
            warnings.warn(message, UserWarning)

    def check_expiry_of_key_is_close(self, api_key):
        """Check that the expiration date of the api_key is not too close.

        Args:
            api_key: key used to connect to the Kili API
        """
        duration_days = 365
        warn_days = 30
        queries = QueriesApiKey(self)
        key_object = queries.api_keys(api_key=api_key, fields=[
                                      'createdAt'], disable_tqdm=True)
        key_creation = datetime.strptime(
            key_object[0]['createdAt'], '%Y-%m-%dT%H:%M:%S.%fZ')
        key_expiry = key_creation + timedelta(days=duration_days)
        key_remaining_time = key_expiry - datetime.now()
        key_soon_deprecated = key_remaining_time < timedelta(days=warn_days)
        if key_soon_deprecated:
            message = f"""
Your api key will be deprecated on {key_expiry:%Y-%m-%d}.
You should generate a new one on My account > API KEY."""
            warnings.warn(message, UserWarning)

    def get_user(self):
        """Get the current user from the api_key provided"""
        result = self.client.execute(GQL_ME)
        return format_result('data', result)
