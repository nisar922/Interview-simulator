import asyncio

import models 
from db import engine, init_db

async def main():
    await init_db()
    print("Table ban gayi")
    await engine.dispose()

asyncio.run(main())    