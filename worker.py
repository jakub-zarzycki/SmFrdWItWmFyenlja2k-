import asyncio
import datetime
import requests

class worker:

    def __init__(self, id, url, interval):

        self.run = True
        self.url = url
        self.history = []
        self.id = id
        self.interval = interval

        self.loop = asyncio.get_event_loop()
        self.task = self.loop.create_task(self.work())

    async def work(self):

        while True:

            response = requests.get(self.url, timeout=5)

            self.history.append({"response":response.text,
                            "duration":response.elapsed.total_seconds(),
                            "created_at":datetime.datetime.now().timestamp()})

            print("request done")

            await asyncio.sleep(self.interval)

    def stop(self):

        self.task.cancel()
