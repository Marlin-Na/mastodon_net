
from mastodon import Mastodon
from config import mastodon_credentials
from login import conf_instances
from itertools import chain
import re
import os
import shelve
import time
from collections import OrderedDict 

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crawlerdata.db")
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crawlerjob.log")

def get_instance_name_from_baseurl(url):
    return url.replace("http://", "").replace("https://", "")
def get_user_and_instance_name_from_acct(acct, from_which_instance):
    if re.search("@", acct):
        spl = acct.split("@")
        return spl[0], spl[1] 
    else:
        return acct, from_which_instance

instance_set = {
    get_instance_name_from_baseurl(ins.api_base_url):ins for ins in conf_instances()
}

class RelationPerUser:
    base_instance = None # From which instance the data is fetched
    user_id = None
    user_name = None
    instance_name = None
    followers = None
    following = None
    def __init__(self, base_instance, user_id, user_name, instance_name, followers, following):
        self.base_instance = base_instance
        self.user_id       = user_id
        self.user_name     = user_name
        self.instance_name = instance_name
        self.followers     = followers
        self.following     = following
    @classmethod
    def create_from_id(cls, user_id, acct, base_instance_name):
        #base_instance = get_instance_name_from_baseurl(instance.api_base_url)
        user_name, instance_name = get_user_and_instance_name_from_acct(acct, base_instance_name)
        return cls(base_instance_name, user_id, user_name, instance_name, None, None)
    def fetch_relation(self):
        ins = instance_set[self.base_instance]
        try:
            following = ins.account_following(self.user_id)
            followers = ins.account_followers(self.user_id)
        except Exception as err:
            print("Error fetching user {} on instance {}: {}".format(
                self.user_id, self.instance_name, err))
            return
        ## Strip some fields
        self.following = [
            dict((k, the_one[k]) for k in ["id", "acct"]) for the_one in following
        ]
        self.followers = [
            dict((k, the_one[k]) for k in ["id", "acct"]) for the_one in followers
        ]
        return
    def get_key(self):
        return self.base_instance, self.user_id
    def get_db_key(self):
        return self.base_instance + "!!" + str(self.user_id)
    def persistent(self):
        with shelve.open(DB_PATH) as db:
            db[self.get_db_key()] = {
                "base_instance" : self.base_instance,
                "user_id"       : self.user_id,
                "user_name"     : self.user_name,
                "instance_name" : self.instance_name,
                "followers"     : self.followers,
                "following"     : self.following,
            }
        return None
    @classmethod
    def from_persistent(cls, db_key):
        with shelve.open(DB_PATH, "r") as db:
            data = db[db_key]
        return cls(
            data["base_instance"],
            data["user_id"      ],
            data["user_name"    ],
            data["instance_name"],
            data["followers"    ],
            data["following"    ],
        )

class FriendshipCrawler:
    known_users = set()
    wait_queue = OrderedDict()
    failed_users = dict()
    def __init__(self):
        return
    def update_schedule(self, peruser, do_persistent=True):
        """
        The function will end up adding the entry to either known_users
        or failed_users. And add followers/following to wait_queue.
        """
        ## The data is not available, add to the failed_users list
        if peruser.followers is None or peruser.following is None:
            self.failed_users[peruser.get_key()] = peruser
            if peruser.get_key() in self.known_users:
                print("Something unexpected happened !!!")
                self.known_users.remove(peruser.get_key())
            if peruser.get_key() in self.wait_queue:
                del self.wait_queue[peruser.get_key()]
            return
        ## The data is available, remove it from failed_users and wait queue
        if peruser.get_key() in self.failed_users:
            del self.failed_users[peruser.get_key()]
        if peruser.get_key() in self.wait_queue:
            del self.wait_queue[peruser.get_key()]
        ## Add the following and followers to wait_queue.
        base_instance = peruser.base_instance
        for friend_info in chain(peruser.following, peruser.followers):
            user_id = friend_info['id']
            acct    = friend_info['acct']
            the_person = RelationPerUser.create_from_id(user_id, acct, base_instance)
            if the_person.instance_name not in instance_set:
                continue # external ones, do not even persistent
            if the_person.get_key() in self.known_users:
                continue # Already fetched
            if the_person.get_key() in self.failed_users:
                continue # Already failed
            if the_person.get_key() in self.wait_queue:
                continue
            if do_persistent:
                the_person.persistent() # So that we can restore wait_queue from db
            self.wait_queue[the_person.get_key()] = the_person
        ## Add to known_users (save to disk and free the memory)
        if do_persistent:
            peruser.persistent()
        self.known_users.add(peruser.get_key())
    def fetch(self):
        if len(self.wait_queue):
            key, the_person = self.wait_queue.popitem()
            self.update_schedule(the_person) ## Temporarily add to failed_users
            the_person.fetch_relation()
            self.update_schedule(the_person) ## Move to known_users if successful
        else:
            print("==== wait_queue is empty ====")
            time.sleep(1)
    def reschedule_failed_users(self):
        for key, value in self.failed_users.items():
            self.wait_queue[key] = value
        for key in self.failed_users:
            del self.failed_users[key]
    @classmethod
    def restore_from_persistent(cls):
        ans = cls()
        with shelve.open(DB_PATH, "r") as db:
            for key in db.keys():
                person = RelationPerUser.from_persistent(key)
                ans.update_schedule(person, do_persistent=False)
        ans.reschedule_failed_users()
        return ans
    @classmethod
    def init_from_seed(cls):
        ans = cls()
        seed_instance = list(instance_set.values())[0]
        seed_account = seed_instance.account(1)
        seed_instance_name = get_instance_name_from_baseurl(seed_instance.api_base_url)
        seed = RelationPerUser(
            seed_instance_name,
            seed_account['id'],
            seed_account['username'],
            get_user_and_instance_name_from_acct(seed_account['acct'], seed_instance_name)[1],
            None, None
        )
        ans.wait_queue[seed.get_key()] = seed
        return ans
    def log_stat(self):
        with open(LOG_FILE, "a") as log_file:
            log = "{}\t{}\t{}\t{}\n".format(
                len(self.known_users), len(self.wait_queue), len(self.failed_users), time.time()
            )
            log_file.write(log)

if __name__ == "__main__":
    if os.path.exists(DB_PATH):
        crawler = FriendshipCrawler.restore_from_persistent()
    else:
        crawler = FriendshipCrawler.init_from_seed()
    while True:
        crawler.fetch()
        crawler.log_stat()
        if len(crawler.wait_queue) == 0:
            print("======== Job finished ======")
            break
