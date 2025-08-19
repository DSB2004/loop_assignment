

from prisma import Prisma

class PrismaClient:
    def __init__(self):
        self.db = Prisma()
        self._connected = False

    async def connect(self):
        if not self._connected:
            await self.db.connect()
            self._connected = True
            print("Connected to Prisma")
        return self.db

    async def disconnect(self):
        if self._connected:
            await self.db.disconnect()
            self._connected = False
            print("Disconnected from Prisma")

    
