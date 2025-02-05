import queue

# Shared queue for storing responses from RabbitMQ consumer
rental_response_cache = queue.Queue()
return_response_cache = queue.Queue()
