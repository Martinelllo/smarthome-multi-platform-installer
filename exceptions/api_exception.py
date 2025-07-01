class ServerNotReachableException(Exception):
    def __init__(self, url=None):
        self.url = url
        self.message = F"Server not reachable! {url or ''}"
        super().__init__(self.message)