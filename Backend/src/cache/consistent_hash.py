from uhashring import HashRing

class ConsistentHashRing:
    """Wrapper around uhashring for mapping keys to logical nodes."""
    
    def __init__(self, nodes: list[str], virtual_nodes: int = 150):
        # uhashring expects a dict of node_name -> weight/vnodes
        # We assign equal vnodes to all nodes.
        nodes_dict = {node: {"vnodes": virtual_nodes} for node in nodes}
        # default hash_fn in uhashring is md5, which is exactly what we want
        self.ring = HashRing(nodes=nodes_dict)
        self.node_set = set(nodes)
        
    def get_node(self, key: str) -> str:
        """Get the node responsible for the given key."""
        if not self.node_set:
            raise ValueError("Hash ring is empty")
        return self.ring.get_node(key)
