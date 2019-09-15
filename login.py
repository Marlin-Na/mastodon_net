
import base64
import os
from mastodon import Mastodon

APP_NAME = "mastodon_net_crawler"

## Register the app and save the credentials
def mastodon_instance(baseurl, email, password):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    credential_path = os.path.join(
        script_dir, "app_credentials", base64.b64encode(baseurl.encode("ascii")).decode())

    if not os.path.exists(credential_path):
        Mastodon.create_app(
            APP_NAME, scopes=["read"], api_base_url=baseurl, to_file=credential_path
        )
        print("Created application credential file at {}".format(credential_path))
    instance = Mastodon(
        client_id=credential_path,
        api_base_url=baseurl
    )
    instance.log_in(username=email, password=password, scopes=["read"])
    return instance

def conf_instances():
    from config import mastodon_credentials
    return [ mastodon_instance(*ins) for ins in mastodon_credentials ]
 
