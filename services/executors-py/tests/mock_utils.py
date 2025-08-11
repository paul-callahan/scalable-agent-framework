import asyncio
from types import SimpleNamespace

from aiokafka.structs import TopicPartition, RecordMetadata


async def prepare_aio_kafka_consumer(mock_consumer):
    mock_aiokafka_consumer = mock_consumer.return_value
    mock_aiokafka_consumer.start.return_value = None
    mock_aiokafka_consumer.stop.return_value = None
    return mock_aiokafka_consumer


async def prepare_aio_kafka_producer(mock_producer):
    mock_aiokafka_producer = mock_producer.return_value
    mock_aiokafka_producer.start.return_value = None
    mock_aiokafka_producer.stop.return_value = None
    # TODO: this may need to be updated
    #fut = asyncio.get_event_loop().create_future()

    x = RecordMetadata(
        topic="my_topic",
        partition=0,
        topic_partition=TopicPartition("my_topic", 0),
        offset=42,
        timestamp=1723160000000,  # any int ms or None
        timestamp_type=1,         # 0=create time, 1=log append time
        log_start_offset=0,
    )
    #fut.set_result(x)
    sn  = SimpleNamespace(
        topic="t", partition=0, offset=123
    )
    mock_aiokafka_producer.send_and_wait.return_value = sn

    return mock_aiokafka_producer



# async def aiter():
#     for m in [b"a", b"b"]:
#         yield m
# consumer.__aiter__.return_value = aiter()