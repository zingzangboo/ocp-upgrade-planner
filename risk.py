class Risk:

    def __init__(self, name, url, message):
        self._name = name
        self._url = url
        self._message = message

    def name(self):
        return self._name

    def url(self):
        return self._url

    def message(self):
        return self._message
