import ratelimit


class FakePipe:
    def __init__(self, store):
        self.store = store
        self.ops = []


    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


    def incr(self, key):
        self.ops.append(("incr", key))
        return self

    def expire(self, key, window, nx=False):
        self.ops.append(("expire", key))
        return self


    async def execute(self):
        out = []
        for op, key in self.ops:
            if op == "incr":
                self.store[key] = self.store.get(key, 0) + 1
                out.append(self.store[key])
            else:
                out.append(True)
        return out



class FakeRedis:
    def __init__(self):
        self.store = {}


    def pipeline(self, transaction=True):
        return FakePipe(self.store)



async def test_blocks_after_limit(monkeypatch):
    monkeypatch.setattr(ratelimit, "redis_client", FakeRedis())
    monkeypatch.setattr(ratelimit, "DISABLED", False)
    results = [await ratelimit.allow("k", 3, 60) for _ in range(5)]
    assert results == [True, True, True, False, False]



async def test_keys_are_independent(monkeypatch):
    monkeypatch.setattr(ratelimit, "redis_client", FakeRedis())
    monkeypatch.setattr(ratelimit, "DISABLED", False)
    assert await ratelimit.allow("a", 1, 60) is True
    assert await ratelimit.allow("b", 1, 60) is True
    assert await ratelimit.allow("a", 1, 60) is False