
Mastodon is a free software for distributed social networking. Unlike Twitter
which has a central server, it allows anyone to host their own server node in the network,
and these servers are connected as a federated social network.

This is an exercise to write a crawler fetching the friendship network
of mastodon users on different instances with mastodon api.

## Source code

The source code can be found at https://github.com/Marlin-Na/mastodon_net.

To run the program, first edit `config.py` with the instance names, user names
and passwords. Then run the program with

```
python3 crawler.py
```

The data and log will be saved to `crawlerdata.db` and `crawlerjob.log`.

After finishing or interrupting the job, run `plot.py` will generate the
a plot of count of successfully fetched users and users in the queue with
regards to time.

## Results

I runned a job for three days with two large instances
(pawoo.net and mastodon.social). The following plot shows the count of
successfully fetched users and users in the queue with regards to time.

![plot](./plot.py)

Since the current implementation will not propagate through nodes on instances
that are not configured in `config.py`, the fetched data only contains a proportion
of the nodes/edges on the instances.

The job runs about 94 hours and successfully fetched 169699 users' relationship data.
Two requests failed possibly due to network error. 

On average, the program fetchs two users' data per second, i.e.
making four or more requests per second (followers and followings).
The time is mainly bounded by the limit of Mastodon API rate per
user account.

(c) Screen Shots of your Web Crawler’s Command lines or GUIs

(d) Write a summary report on your design and measurement results.

## Implementation details

The program will fetch data for the initial user and add its followers
and followings to the queue to be fetched. It will also check whether
the follower/following has already been fetched or in the queue list.

The data is stored as key-value pairs with Berkeley DB through
Python's shelve interface. For the purpose of this programming exercise,
I only stored the unique identifier of one user's followers and followings
for minimal storage size.

I have also implemented methods to restore the state of the application
from the database in case of a program crash. In this way, the program
can be robust and the data will be secure.

## Possible improvements

Currently the application performance is dominated by api rate limit.
It may be improved with:

- Configure more instances to fetch and more accounts to use. Then
  use multiple threads (one thread for one instance/account) to make the
  requests.
  It will require a thread-safe job queue implementation (e.g. Python's queue module).
