## Image Used

docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:4-management

### Management Console: 
    URL:    http://localhost:15672/

**Default Credentials**
    username:   guest
    password:   guest

## Terminology 

**Producer**: Sender of messages.

**Queue**: Postbox. Essentially, a large message buffer. Many producers can send messages to one queue. Many consumers can recieve messages from one queue.

**Consumer**: Reviver of messages. 

## Programs

### 1.0 Hello World
print("Hello World!") of Messaging. 

#### Programs
**send.py**
- Connect to RabbitMQ server
- Declare a queue
- Send a message to the queue
- Close the connection

**recieve.py**
- Connect to RabbitMQ server
- Declare a queue (idempotent function) - Safe practice to declare it in both producer and consumer with the same name. 
- Declare the callback function
- Setup basic_consume
- Start consuming

``` bash
sudo rabbitmqcli list_queues

# windows
rabbitmqcli.bat list_queues
```

### 2.0 Work Queues
Distribute a time consuming task between multiple workers. 
This ensures we avoid doing a time consuming task immidiately, blocking other tasks. 

Messages are delivered in a round robin order - this ensures that on average each worker get the same number of messages. 
The current program sleeps based on the number of dots present in the senders message. 
Try running 2 workers, and constantly send messages from the sender. [3 total terminals]


**MESSAGE ACKNOWLEDGEMENT**
Currently, as soon as the RabbitMQ server sends a message to a consumer, it marks it for deletion. Now, if a worker is unable to complete the task, or goes down, the message it was processing is lost. All messages with the workers that goes down are lost. 

We don't want this behavior, if a worker goes down, we want to send the task to another worker. 
The auto_ack=True flag helps handle this. An ack is sent back by the consumer to rabbitMQ to tell that the message has been recieved, processed, and can be deleted. A timeout of 30 mins is set as default. 

#### Proper Acknoledgement 
``` python
def callback(ch, method, properties, body):
    print(f" [x] Received {body.decode()}")
    time.sleep(body.count(b'.') )
    print(" [x] Done")
    ch.basic_ack(delivery_tag = method.delivery_tag)
```

We must use the same channel that recieved the delivery. 

**PROBLEM**
If we miss the basic_ack, rabbitMQ will eat more and more memory as it will not be able to release any un-acked messages. 
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

We use **channel.basic_qos(prefetch_count=1)**. This tells RabbutMQ to not giv emore than one message to a worker at a time, i.e. don't give new work, until the previous work has been acknoledged, instead dispatch it to the next available worker. 


#### Programs
**send_new_task.py**
- Establish connection
- Declare a durable queue
- Send a persistant message
- Close the connection

**recieve_worker.py**
- Establish connection
- Declare a durable queue
- Add basic acknoledgement in the callback method
- Add fair dispatch - prefetch = 1
- Basic consume to call the callback method
- Start consuming

### 3.0 PUBLISHER SUBSCRIBERS

Messages are broadcasted to all recievers. 

#### Exchanges 

Performs a simple function - 
- Recieved messages from a producer
- Pushes the messages to a queue

But it must know 

    




