import redis.asyncio as aioredis
from src.config import settings

class RedisNode:
    """Abstraction for a logical cache node.
    
    Instead of running N Redis instances, we simulate N logical nodes on a single
    Redis instance using key prefixes (e.g. "cache:node-1:key").
    """
    
    def __init__(self, node_id: str, client: aioredis.Redis, default_ttl: int = 300):
        self.node_id = node_id
        self.client = client
        self.default_ttl = default_ttl
        self.prefix = f"cache:{node_id}:"
    
    async def get(self, key: str) -> str | None:
        """Fetch a key belonging to this node."""
        return await self.client.get(f"{self.prefix}{key}")
    
    async def set(self, key: str, value: str, ttl: int | None = None):
        """Set a key in this node with an expiry time."""
        await self.client.setex(
            f"{self.prefix}{key}", 
            ttl or self.default_ttl, 
            value
        )
    
    async def delete_by_pattern(self, pattern: str):
        """Delete all keys in this node that start with the given pattern using SCAN."""
        cursor = 0
        match_pattern = f"{self.prefix}{pattern}*"
        while True:
            cursor, keys = await self.client.scan(cursor, match=match_pattern, count=100)
            if keys:
                await self.client.delete(*keys)
            if cursor == 0:
                break
    
    async def stats(self) -> dict:
        """Count how many keys are currently assigned to this logical node."""
        cursor, count = 0, 0
        while True:
            cursor, batch = await self.client.scan(cursor, match=f"{self.prefix}*", count=1000)
            count += len(batch)
            if cursor == 0:
                break
        return {"node_id": self.node_id, "key_count": count}
