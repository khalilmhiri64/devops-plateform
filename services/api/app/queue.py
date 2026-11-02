"""Thin wrapper around a Redis list used as a FIFO job queue."""
import json

import redis


class JobQueue:
    def __init__(self, client: redis.Redis, name: str):
        self.client = client
        self.name = name

    def enqueue(self, job_id: str, job_type: str) -> None:
        self.client.lpush(self.name, json.dumps({"id": job_id, "type": job_type}))

    def depth(self) -> int:
        return int(self.client.llen(self.name))

    def ping(self) -> bool:
        try:
            return bool(self.client.ping())
        except redis.RedisError:
            return False
