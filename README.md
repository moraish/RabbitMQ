### Image Used

docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:4-management

### Management Console: 
    URL:    http://localhost:15672/

**Default Credentials**
    username:   guest
    password:   guest

### Terminology 

**Producer**: Sender of messages.

**Queue**: Postbox. Essentially, a large message buffer. Many producers can send messages to one queue. Many consumers can receive messages from one queue.

**Consumer**: Receiver of messages. 

### 1.0 Hello World
print("Hello World!") of Messaging. 

#### Programs
**send.py**
- Connect to RabbitMQ server
- Declare a queue
- Send a message to the queue
- Close the connection

**receive.py**
- Connect to RabbitMQ server
- Declare a queue (idempotent function) - Safe practice to declare it in both producer and consumer with the same name. 
- Declare the callback function
- Setup basic_consume
- Start consuming

``` bash
sudo rabbitmqctl list_queues

# windows
rabbitmqctl.bat list_queues
```

### 2.0 Work Queues
Distribute a time consuming task between multiple workers. 
This ensures we avoid doing a time consuming task immediately, blocking other tasks. 

Messages are delivered in a round robin order - this ensures that on average each worker gets the same number of messages. 
The current program sleeps based on the number of dots present in the sender's message. 
Try running 2 workers, and constantly send messages from the sender. [3 total terminals]


**MESSAGE ACKNOWLEDGEMENT**
Currently, as soon as the RabbitMQ server sends a message to a consumer, it marks it for deletion. Now, if a worker is unable to complete the task, or goes down, the message it was processing is lost. All messages with the workers that goes down are lost. 

We don't want this behavior, if a worker goes down, we want to send the task to another worker. 
To prevent message loss, we set `auto_ack=False` and manually acknowledge messages. An ack is sent back by the consumer to RabbitMQ to tell that the message has been received, processed, and can be deleted. A timeout of 30 mins is set as default. 

#### Proper Acknowledgement 
``` python
def callback(ch, method, properties, body):
    print(f" [x] Received {body.decode()}")
    time.sleep(body.count(b'.') )
    print(" [x] Done")
    ch.basic_ack(delivery_tag = method.delivery_tag)
```

We must use the same channel that received the delivery. 

**PROBLEM**
If we miss the basic_ack, RabbitMQ will eat more and more memory as it will not be able to release any un-acked messages. 
Debug: 
``` bash
sudo rabbitmqctl list_queues name messages_ready messages_unacknowledged

# windows
rabbitmqctl.bat list_queues name messages_ready messages_unacknowledged
```

#### RABBIT-MQ SERVER STOPS
Ack will ensure that if a worker stops the messages are not lost. But it does not handle server stopping. 
Solution: 
- Mark the queue as durable. 
``` python
channel.queue_declare(queue='hello', durable=True)

```
- Mark the message as durable.
``` python
channel.basic_publish(exchange='',
                      routing_key="hello",
                      body=message,
                      properties=pika.BasicProperties(
                        delivery_mode = pika.DeliveryMode.Persistent ))
```

This solution is not the safest, but okay for simple cases. 

**NOTE**: We can't change the existing queues and make them durable. We would require re-creating queues. 



#### FAIR DISPATCH
RabbitMQ currently just sends all messages in a round robin fashion. What if all even messages are heavy, and all light messages are odd. This causes one worker to work more.

We use **channel.basic_qos(prefetch_count=1)**. This tells RabbitMQ to not give more than one message to a worker at a time, i.e. don't give new work until the previous work has been acknowledged, instead dispatch it to the next available worker. 


#### Programs
**send_new_task.py**
- Establish connection
- Declare a durable queue
- Send a persistent message
- Close the connection

**receive_worker.py**
- Establish connection
- Declare a durable queue
- Add basic acknowledgement in the callback method
- Add fair dispatch - prefetch = 1
- Basic consume to call the callback method
- Start consuming

### 3.0 PUBLISHER SUBSCRIBERS

Messages are broadcasted to all receivers. 

#### Exchanges 

Performs a simple function - 
- Receives messages from a producer
- Pushes the messages to a queue

But it must know what to do with each message, i.e.
- Should it be appended to a queue
- Should it be appended to many queues
- Should it be discarded

#### Exchange Type 
- Fanout
Broadcasts all messages to all queues

``` bash
sudo rabbitmqctl list_exchanges
```

``` python
channel.basic_publish(exchange="logs",
                        routing_key="", 
                        body=message)

```

#### Temporary Queue

Declare with a random name:

``` python
result = channel.queue_declare(queue='')
```

Queue should be deleted when the consumer connection is closed:

``` python
result = channel.queue_declare(queue='', exclusive=True)

```

#### Programs

**send_log.py**
- Establish connection to RabbitMQ server
- Declare exchange of type fanout
- Send a message to the exchange
- Close the connection


**receive_log.py**
- Establish a connection to RabbitMQ server
- Declare exchange of type fanout
- Declare a temp queue
- Bind the queue to the exchange
- Consume the message



**Note** 
In this case - messages that were produced before the consumer is setup are lost. 

### 4.0 Routing
Now, instead of a receiver getting all the messages, we are going to be subscribing only to a subset of the messages. We do this via bindings. 

Fanout exchanges do not support this behavior. We will instead move to direct exchanges. 
Message goes to the queue whose ```binding_key``` exactly matches the ```routing_key``` of the message. 

- Publisher sends a routing key. 
- Based on this routing key, we send the message to the right queue. 
- The right queue is decided by the binding_key. 

#### Programs
**send_logs.py**
- Connect to Server
- Declare an exchange
- Publish with **Correct** Routing Key
- Close the connection


**receive_logs.py**
- Connect to Server
- Declare exchange
- Declare temp queue
- Bind queue with exchange with the **Correct** Routing Key
- Start Consuming


### 5.0 Topics
Routing improves the system but does not provide flexibility. 
Let's say we want to filter / consume messages based on 2 criteria now - 
- Severity (same as previous example)
- Source

#### Exchange Type = Topic
Must be a list of words delimited by dots. Examples stock.usd.nyse, quick.orange.rabbit
Binding Key, i.e. routing key in the queue binding function must be in the same format.

**Special Cases**
- `*` Star: can substitute for exactly one word
- `#` Hash: can substitute for zero or more words 

#### Programs
**send_logs.py**
- Connect to server
- Declare a topic exchange
- Publish a message with a specific topic
- Close the connection

**receive_logs.py**
- Connect to server
- Declare a topic exchange
- Declare a temp queue and bind to exchange based on specific topics
- start consuming


### 6.0 RPC
Run a function on a different computer and wait for the results. 
We will build a client and a scalable RPC server. 

#### Client Interface
We create a simple client class, which exposes a method named call. 

**Problem with RPC**: If not done properly, RPC code is unmanageable. 
- Ensure it is obvious which RPC call is local, and which is remote.
- Document
- Handle error cases

Better idea is to use Async pipelines. 