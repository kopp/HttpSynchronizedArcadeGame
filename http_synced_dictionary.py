from threading import Thread
import requests
from queue import SimpleQueue, Empty
from time import sleep


class HttpSyncedDictionary:
    """
    Contains a dictionary that can be updated and queried locally.
    The updates are sent to a HTTP server, as reply, the current dictionary
    known to the HTTP server is expected.  This is used to update the
    local dictionary.

    In effect, the dictionary can be synchronized across multiple instances
    all using the same server.

    The synchronization happens in a separate thread and is limited by the
    time needed for HTTP POST send/receive.
    """

    def __init__(self, server_url, keys_to_filter=[]):
        """
        :param keys_to_filter: Iterable of keys in the synchronized dictionary.
            In order to not overwrite the values which are produced locally and
            thus more accurate locally than on the server, provide the keys to
            those values here.  Values from the remote server for those keys will
            be ignored.
        """
        self.data = {}
        self.inbox = SimpleQueue()

        self.server_url = server_url
        self.keys_to_filter = keys_to_filter

        self.thread = Thread(target=self._thread_function)
        self.daemon = True
        self.is_thread_running = False

    def _thread_function(self):
        while self.is_thread_running:
            new_data = {}
            while not self.inbox.empty():  # only use latest queue element
                new_data = self.inbox.get_nowait()
            response = requests.post(self.server_url, json=new_data)
            if response.ok:
                remote_status = response.json()
                for key in self.keys_to_filter:
                    remote_status.pop(key, None)
                self.data.update(remote_status)

    def start(self):
        if not self.is_thread_running:
            self.is_thread_running = True
            self.thread.start()

    def stop(self):
        self.is_thread_running = False
        self.thread.join()

    def update(self, dictionary):
        self.data.update(dictionary)
        self.inbox.put(dictionary)

    def get(self, key=None, default_value=None):
        if key is not None:
            return self.data.get(key, default_value)
        else:
            return self.data


if __name__ == "__main__":

    import pprint
    import os
    identifier = "game-{}".format(os.getpid())

    status = HttpSyncedDictionary("http://localhost:5000/update", keys_to_filter=[identifier])
    status.start()

    print("This is game {}".format(identifier))
    for i in range(10):
        status.update(
            {
                identifier: {
                    "value": i,
                },
            },
        )
        sleep(1)
        pprint.pprint(status.get())

    status.stop()