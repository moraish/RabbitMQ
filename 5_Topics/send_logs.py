import pika

# connect to server
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# declare a topic exchange
channel.exchange_declare(exchange='topic_logs', exchange_type='topic')

# publish with the correct routing key
routing_key = "anonymous.info"

message = "Hello World!"

# publish the message
channel.basic_publish(exchange='topic_logs',
                      routing_key=routing_key,
                      body=message)

print(f" [x] Sent {message}: {routing_key}")

# close the connection
connection.close()
