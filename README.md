# 🐇 RabbitMQ Tutorial

> A hands-on guide to learning RabbitMQ message queuing concepts through practical Python examples.

![RabbitMQ](https://img.shields.io/badge/RabbitMQ-FF6600?style=for-the-badge&logo=rabbitmq&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

---

## 📑 Table of Contents

- [Quick Start](#-quick-start)
- [Terminology](#-terminology)
- [Tutorials](#-tutorials)
  - [1. Hello World](#1-hello-world)
  - [2. Work Queues](#2-work-queues)
  - [3. Publisher/Subscribers](#3-publishersubscribers)
  - [4. Routing](#4-routing)
  - [5. Topics](#5-topics)
  - [6. RPC](#6-rpc)

---

## 🚀 Quick Start

### Run RabbitMQ with Docker

```bash
docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:4-management
```

### Management Console

| Property     | Value                                              |
| ------------ | -------------------------------------------------- |
| **URL**      | [http://localhost:15672/](http://localhost:15672/) |
| **Username** | `guest`                                            |
| **Password** | `guest`                                            |

---

## 📖 Terminology

| Term         | Description                                                                                                                     |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------- |
| **Producer** | Sender of messages                                                                                                              |
| **Queue**    | A message buffer (like a postbox). Many producers can send messages to one queue, and many consumers can receive from one queue |
| **Consumer** | Receiver of messages                                                                                                            |

---

## 📚 Tutorials

### 1. Hello World

> The `print("Hello World!")` of messaging.

#### Programs

| File         | Description                                                                         |
| ------------ | ----------------------------------------------------------------------------------- |
| `send.py`    | Connect to RabbitMQ → Declare queue → Send message → Close connection               |
| `receive.py` | Connect to RabbitMQ → Declare queue (idempotent) → Setup callback → Start consuming |

#### Useful Commands

```bash
# Linux/Mac
sudo rabbitmqctl list_queues

# Windows
rabbitmqctl.bat list_queues
```

---

### 2. Work Queues

> Distribute time-consuming tasks between multiple workers to avoid blocking.

Messages are delivered in **round-robin** order, ensuring each worker gets approximately the same number of messages.

💡 **Try it:** Run 2 workers in separate terminals, then send messages from a third terminal to see the distribution.

#### Message Acknowledgement

By default, RabbitMQ marks messages for deletion immediately after sending. This is problematic if a worker crashes.

To prevent message loss:
- Set `auto_ack=False`
- Manually acknowledge messages after processing

```python
def callback(ch, method, properties, body):
    print(f" [x] Received {body.decode()}")
    time.sleep(body.count(b'.'))
    print(" [x] Done")
    ch.basic_ack(delivery_tag=method.delivery_tag)
```

> ⚠️ **Warning:** Missing `basic_ack` causes memory leaks as unacknowledged messages pile up.

**Debug unacknowledged messages:**

```bash
# Linux/Mac
sudo rabbitmqctl list_queues name messages_ready messages_unacknowledged

# Windows
rabbitmqctl.bat list_queues name messages_ready messages_unacknowledged
```

#### Message Durability

Acknowledgements protect against worker failure, but not server crashes. To handle server restarts:

**1. Mark the queue as durable:**

```python
channel.queue_declare(queue='hello', durable=True)
```

**2. Mark messages as persistent:**

```python
channel.basic_publish(
    exchange='',
    routing_key="hello",
    body=message,
    properties=pika.BasicProperties(
        delivery_mode=pika.DeliveryMode.Persistent
    )
)
```

> 📝 **Note:** Existing queues cannot be made durable—you must recreate them.

#### Fair Dispatch

Round-robin doesn't account for task complexity. Use **prefetch** to prevent overloading workers:

```python
channel.basic_qos(prefetch_count=1)
```

This ensures a worker only receives a new message after acknowledging the previous one.

#### Programs

| File                | Description                                                                    |
| ------------------- | ------------------------------------------------------------------------------ |
| `send_new_task.py`  | Establish connection → Declare durable queue → Send persistent message         |
| `receive_worker.py` | Declare durable queue → Setup acknowledgement → Enable fair dispatch → Consume |

---

### 3. Publisher/Subscribers

> Broadcast messages to all receivers using the **Fanout** exchange.

#### Exchanges

Exchanges receive messages from producers and push them to queues. They decide:
- Append to one queue
- Append to many queues
- Discard the message

**Exchange Type: Fanout** — Broadcasts all messages to all bound queues.

```bash
sudo rabbitmqctl list_exchanges
```

```python
channel.basic_publish(exchange="logs", routing_key="", body=message)
```

#### Temporary Queues

Create an auto-named, exclusive queue that deletes when the connection closes:

```python
result = channel.queue_declare(queue='', exclusive=True)
```

#### Programs

| File             | Description                                                            |
| ---------------- | ---------------------------------------------------------------------- |
| `send_log.py`    | Connect → Declare fanout exchange → Publish message                    |
| `receive_log.py` | Connect → Declare fanout exchange → Create temp queue → Bind → Consume |

> 📝 **Note:** Messages published before a consumer connects are lost.

---

### 4. Routing

> Subscribe only to a **subset** of messages using **Direct** exchanges.

Unlike fanout, direct exchanges route messages based on `binding_key` matching the `routing_key`.

**How it works:**
1. Publisher sends a message with a `routing_key`
2. Exchange matches it against queue `binding_key`s
3. Message is delivered to matching queues

#### Programs

| File              | Description                                                        |
| ----------------- | ------------------------------------------------------------------ |
| `send_logs.py`    | Connect → Declare exchange → Publish with routing key              |
| `receive_logs.py` | Connect → Declare exchange → Bind queue with routing key → Consume |

---

### 5. Topics

> Filter messages based on **multiple criteria** using **Topic** exchanges.

Topic routing keys must be dot-delimited words (e.g., `stock.usd.nyse`, `quick.orange.rabbit`).

#### Special Wildcards

| Pattern    | Matches            |
| ---------- | ------------------ |
| `*` (star) | Exactly one word   |
| `#` (hash) | Zero or more words |

#### Programs

| File              | Description                                                           |
| ----------------- | --------------------------------------------------------------------- |
| `send_logs.py`    | Connect → Declare topic exchange → Publish with topic routing key     |
| `receive_logs.py` | Connect → Declare topic exchange → Bind with topic patterns → Consume |

---

### 6. RPC

> Run a function on a remote computer and wait for results.

Build a client and a scalable RPC server using RabbitMQ.

#### Client Interface

Create a simple client class exposing a `call` method for remote procedure calls.

> ⚠️ **Best Practices for RPC:**
> - Make it obvious which calls are local vs. remote
> - Document your system thoroughly
> - Handle error cases gracefully
> - Consider using **async pipelines** for better scalability 