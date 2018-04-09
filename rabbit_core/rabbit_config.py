class QueueDefinition():
    __slots__ = (
        "name",
        "routing_key"
    )

    def __init__(self,
                 name,
                 routing_key):
        self.name = name
        self.routing_key = routing_key

class Parameters(object):
    __slots__ = (
        'host',
        'username',
        'password',
        'retry_delay',
        "exchange")

    def __init__(self):
        self.host = None
        self.username = None
        self.password = None
        self.retry_delay = None
        self.exchange = None

class RabbitConnectionParameters(Parameters):
    __slots__ = ()

    def __init__(self,
                 host='localhost',
                 username='guest',
                 password='guest',
                 retry_delay=1.0,
                 exchange='hearthstone.changes'):
        super(RabbitConnectionParameters, self).__init__()
        self.host = host
        self.username = username
        self.password = password
        self.retry_delay = retry_delay
        self.exchange = exchange