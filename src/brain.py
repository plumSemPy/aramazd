from py2neo import Graph, Node, Relationship
import redis

class Brain(object):
    """
    Record and remember.

    Every piece of information is saved in redis and the redis
    key is passed to neo4j.
    """
    def __init__(self):
       self.__redis = redis.StrictRedis(host='redis', port=6379, db=0)
       graph = Graph("http://neo4j:password@neo4j:7474/db/data/")
       self.__tx = graph.begin()

    def record(self, name, type_, information, file_location, neighbor=None, link=None):
        """Record the `information` with the `name` as redis key.

           The type_ is the neo4j Node type. E.g. `Visual`.
           TODO: Enum type_ values
           name: name of the key shared between neo4j and redis
           type_: the type of this information
           information: what should be saved in redis
           file_location: what should be saved in neo4J
           neighbor: a node this should associate with
           link: the strength between this and `neighbor`
        """
        shared_name = "{0}: {1}".format(type_, name)
        self.__redis.set(shared_name, information)
        node = Node(type_, redis_key=shared_name, file_location=file_location)
        self.__tx.create(node)
        if neighbor:
            relationship = Relationship(node, "ASSOCIATED WITH", neighbor, strength=link)
            self.__tx.create(relationship)
        self.__tx.commit()

    def lookup_by(self, type_):
        results = []
        for key in self.__redis.scan_iter("{}*".format(type_)):
            results.append({'key': key, 'value': self.__redis.get(key)})
        return results

    def find_neighbor(self, conditions):
        command = """
            MATCH (n) WHERE (n.{0}='{1}')
            RETURN n;
        """.format(conditions[0], conditions[1])
        return self.__tx.run(command)

