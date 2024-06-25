
import requests
import logging
from urllib.parse import urlparse, parse_qs

from utils import get_logging_level

logging.basicConfig(level=get_logging_level())
logger = logging.getLogger(__name__)

def get_access_token(username, password, proxies=None):
    """
    Obtains an chat API access token for the Reka AI chat platform by simulating a login sequence.
    Args:
        username (str): The username to use for login
        password (str): The password to use for login

    Returns:
        str: The obtained access token, or None if the request fails
    """
  
    s = requests.Session()
    if proxies:
        s.proxies = proxies

    try:
        pre_login_response = s.get("https://chat.reka.ai/bff/auth/login")
        pre_login_response.raise_for_status()
        logger.debug(f"Status Code: {pre_login_response.status_code}")
        logger.debug(f"URL: {pre_login_response.url}")

        pre_login_params = parse_qs(urlparse(pre_login_response.url).query)
        pre_login_state = pre_login_params.get('state')

        if not pre_login_state:
            raise ValueError("No 'state' parameter found in the login URL.")
        pre_login_state = pre_login_state[0]

        logger.debug(f"Login state: {pre_login_state}")

        login_url = "https://auth.reka.ai/u/login"
        login_query = {"state": pre_login_state}
        login_form_data = {
            "state": pre_login_state,
            "action": "default",
            "username": username,
            "password": password
        }

        login_response = s.post(login_url, params=login_query, data=login_form_data)
        login_response.raise_for_status()
        logger.debug(f"Login status: {login_response.status_code}")

        login_session = s.cookies.get("appSession")
        logger.debug(f"Login app session: {login_session}")

        create_token_url = "https://chat.reka.ai/bff/auth/access_token"
        create_token_response = s.get(create_token_url)
        create_token_response.raise_for_status()

        access_token = create_token_response.json().get('accessToken')
        logger.debug(f"Access token: {access_token}")

        if not access_token:
            raise ValueError("Failed to retrieve access token.")

    except requests.RequestException as e:
        logger.error(f"Unable to obtain new access token error: {e}")
        return None

    return access_token
