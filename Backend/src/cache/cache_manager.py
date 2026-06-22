import json
from typing import Any
import redis.asyncio as aioredis

from src.cache.consistent_hash import ConsistentHashRing
from src.cache.redis_nodes import RedisNode
from src.config import settings

class CacheManager:
    """Coordinates the hash ring and the Redis nodes."""
    
    def __init__(self):
        self.ring: ConsistentHashRing | None = None
        self.nodes: dict[str, RedisNode] = {}
        self.hits = 0
        self.misses = 0
        self._redis_client: aioredis.Redis | None = None

    async def init(self):
        """Initialise the Redis connection and logical nodes."""
        self._redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
        
        node_ids = [f"node-{i}" for i in range(settings.cache_node_count)]
        self.ring = ConsistentHashRing(node_ids, virtual_nodes=settings.cache_vnodes)
        
        for node_id in node_ids:
            self.nodes[node_id] = RedisNode(
                node_id=node_id, 
                client=self._redis_client,
                default_ttl=settings.cache_ttl_seconds
            )

    async def close(self):
        """Close the Redis connection."""
        if self._redis_client:
            await self._redis_client.aclose()

    async def get(self, prefix: str) -> tuple[str, list | None]:
        """Fetch suggestions from the assigned cache node."""
        node_id = self.ring.get_node(prefix)
        node = self.nodes[node_id]
        
        raw = await node.get(prefix)
        if raw is not None:
            self.hits += 1
            return node_id, json.loads(raw)
            
        self.misses += 1
        return node_id, None

    async def set(self, prefix: str, suggestions: list[dict]):
        """Cache suggestions in the assigned cache node."""
        node_id = self.ring.get_node(prefix)
        node = self.nodes[node_id]
        await node.set(prefix, json.dumps(suggestions))

    async def invalidate_prefixes(self, query: str):
        """Invalidate all cached prefixes that the query could match."""
        # For a query "iphone", we need to invalidate "i", "ip", "iph", etc.
        # This ensures that when a user types "i", the cache doesn't serve a stale
        # list that is missing the newly incremented "iphone".
        for i in range(1, len(query) + 1):
            prefix = query[:i]
            node_id = self.ring.get_node(prefix)
            node = self.nodes[node_id]
            # Exact key deletion
            await node.client.delete(f"{node.prefix}{prefix}")

    async def debug_info(self, prefix: str) -> dict:
        """Get debug stats for a specific prefix."""
        if not self.ring:
            return {}
            
        node_id = self.ring.get_node(prefix)
        node = self.nodes[node_id]
        
        raw = await node.get(prefix)
        ttl = await node.client.ttl(f"{node.prefix}{prefix}")
        
        total = max(self.hits + self.misses, 1)
        hit_rate = (self.hits / total) * 100
        
        return {
            "prefix": prefix,
            "cache_node": node_id,
            "hit": raw is not None,
            "ttl_remaining_seconds": ttl if ttl > 0 else None,
            "total_hits": self.hits,
            "total_misses": self.misses,
            "hit_rate": f"{hit_rate:.1f}%"
        }

    async def all_stats(self) -> list[dict]:
        """Get key count stats for all nodes."""
        stats = []
        for node in self.nodes.values():
            s = await node.stats()
            stats.append(s)
            
        total = max(self.hits + self.misses, 1)
        hit_rate = (self.hits / total) * 100
        
        stats.append({
            "total_hits": self.hits,
            "total_misses": self.misses,
            "hit_rate": f"{hit_rate:.1f}%"
        })
        return stats

# Global singleton
cache_manager = CacheManager()
