# Web service of a basic payment system

## Run environment

```bash
docker-compose up
```

## Run tests

```bash
docker-compose -f docker-compose.test.yml up
```

## REST API documentation 
```
http://127.0.0.1:8003/docs
```

## Storage
Data is stored in Postgres database (with asyncio support).
Transaction and locking mechanisms guarantee consistency of data. 

Proper wallets are locked before deposit and transfer operation - other requests have to wait until current operation (database transaction) finishes

## Processing mechanism
Requests are processed asynchronously (ASGI) what guaranties high load performance of the API

## Pros and cons of the solution
High load performance can be further improved by introducing queue to store upcoming requests. In this case request doesn't have to wait till changes in the database are done. However in this case we lose feedback about potential database operation failure