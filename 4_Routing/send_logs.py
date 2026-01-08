import pika

# Connect to RabbitMQ server
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare a direct exchange
channel.exchange_declare(exchange='direct_logs', exchange_type='direct')

# Publish with the correct routing key
severity = "info"
message = "Hello World!"

channel.basic_publish(exchange='direct_logs',
                      routing_key=severity,
                        body=message)

print(f" [x] Sent {message}: {severity}")

# Close the connection
connection.close()