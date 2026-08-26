from __future__ import annotations


class MemoryRedis:
    def __init__(self) -> None:
        self.kv: dict = {}
        self.lists: dict = {}
        self.zsets: dict = {}
        self.hashes: dict = {}
        self.sets: dict = {}

    async def get(self, key: str):
        return self.kv.get(key)

    async def set(self, key: str, value, **_kwargs):
        self.kv[key] = value
        return True

    async def delete(self, *keys):
        n = 0
        for key in keys:
            if key in self.kv:
                del self.kv[key]
                n += 1
            if key in self.hashes:
                del self.hashes[key]
                n += 1
        return n

    async def zadd(self, key: str, mapping: dict):
        self.zsets.setdefault(key, {}).update(mapping)
        return len(mapping)

    async def zincrby(self, key: str, amount, member):
        z = self.zsets.setdefault(key, {})
        member = str(member)
        z[member] = float(z.get(member, 0)) + float(amount)
        return z[member]

    async def lpush(self, key: str, value):
        self.lists.setdefault(key, []).insert(0, value)
        return len(self.lists[key])

    async def lrange(self, key: str, start: int, end: int):
        items = self.lists.get(key, [])
        if end < 0:
            end = len(items) + end
        return items[start : end + 1]

    async def ltrim(self, key: str, start: int, end: int):
        items = self.lists.get(key, [])
        self.lists[key] = items[start : end + 1]
        return True

    async def hset(self, key: str, mapping=None, **kwargs):
        bucket = self.hashes.setdefault(key, {})
        data = dict(mapping or {})
        if "key" in kwargs and "value" in kwargs:
            data[kwargs["key"]] = kwargs["value"]
        bucket.update({str(k): v for k, v in data.items()})
        return len(data)

    async def hget(self, key: str, field: str):
        return self.hashes.get(key, {}).get(str(field))

    async def hgetall(self, key: str):
        return dict(self.hashes.get(key, {}))

    async def hdel(self, key: str, *fields):
        bucket = self.hashes.get(key, {})
        n = 0
        for field in fields:
            if str(field) in bucket:
                del bucket[str(field)]
                n += 1
        return n

    async def sadd(self, key: str, *values):
        s = self.sets.setdefault(key, set())
        before = len(s)
        s.update(str(v) for v in values)
        return len(s) - before

    async def srem(self, key: str, *values):
        s = self.sets.get(key, set())
        n = 0
        for v in values:
            if str(v) in s:
                s.remove(str(v))
                n += 1
        return n

    async def sismember(self, key: str, value) -> bool:
        return str(value) in self.sets.get(key, set())
