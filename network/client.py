import asyncio
import json
import queue
import threading
import websockets

class AsyncWebSocketClient:
    def __init__(self, uri):
        self.uri = uri
        self.incoming = queue.Queue()
        self.outgoing = queue.Queue()
        self._thread = None
        self._loop = None
        self._stop_event = threading.Event()

    def start(self):
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._main())

    async def _main(self):
        try:
            async with websockets.connect(self.uri) as ws:
                listen_task = asyncio.create_task(self._listen(ws))
                send_task = asyncio.create_task(self._send(ws))
                await asyncio.get_event_loop().run_in_executor(None, self._stop_event.wait)
                for task in (listen_task, send_task):
                    task.cancel()
                await asyncio.gather(listen_task, send_task, return_exceptions=True)
        except Exception as e:
            print(f"Connection error: {e}")

    async def _listen(self, ws):
        try:
            async for raw in ws:
                msg = json.loads(raw)
                self.incoming.put(msg)
        except asyncio.CancelledError:
            pass

    async def _send(self, ws):
        try:
            while True:
                msg = await asyncio.get_event_loop().run_in_executor(None, self.outgoing.get)
                if msg is None:
                    while not self.outgoing.empty():
                        pending = self.outgoing.get_nowait()
                        if pending is not None:
                            await ws.send(json.dumps(pending))
                    break
                await ws.send(json.dumps(msg))
        except asyncio.CancelledError:
            pass

    def send(self, data):
        """Положить сообщение в очередь на отправку."""
        self.outgoing.put(data)

    def get_messages(self):
        """Извлечь все накопившиеся входящие сообщения."""
        msgs = []
        while not self.incoming.empty():
            msgs.append(self.incoming.get_nowait())
        return msgs

    def close(self):
        """Корректно закрыть соединение и остановить поток."""
        self.outgoing.put(None) 