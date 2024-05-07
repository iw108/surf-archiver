import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from aio_pika import DeliveryMode, ExchangeType, Message, connect
from aio_pika.abc import AbstractConnection, AbstractExchange


@dataclass(kw_only=True)
class ExchangeConfig:
    """Exchange config for RabbitMQ"""

    name: str = "surf-data-archive"
    type: ExchangeType = ExchangeType.FANOUT
    routing_key: str = "archiving-complete"


class AbstractPublisher(ABC):

    @abstractmethod
    async def publish(self, message: dict): ...


class AbstractManagedPublisher(ABC):

    @abstractmethod
    async def __aenter__(self) -> AbstractPublisher: ...

    @abstractmethod
    async def __aexit__(self, *args) -> None: ...


class Publisher(AbstractPublisher):

    def __init__(
        self,
        exchange: AbstractExchange,
        exchange_config: ExchangeConfig,
        delivery_mode: DeliveryMode = DeliveryMode.PERSISTENT,
    ):
        self.exchange = exchange
        self.exchange_config = exchange_config
        self.delivery_mode = delivery_mode

    async def publish(self, message: dict):
        message = Message(
            json.dumps(message).encode(),
            delivery_mode=self.delivery_mode,
        )
        await self.exchange.publish(
            message, routing_key=self.exchange_config.routing_key
        )


class ManagedPublisher(AbstractManagedPublisher):

    conn: AbstractConnection

    def __init__(
        self,
        connection_url: str,
        exchange_config: Optional[ExchangeConfig],
    ):
        self.connection_url = connection_url
        self.exchange_config = exchange_config or ExchangeConfig()

    async def __aenter__(self) -> Publisher:
        self.conn = await connect(self.connection_url)
        await self.conn.__aenter__()

        channel = await self.conn.channel()

        exchange = await channel.declare_exchange(
            self.exchange_config.name,
            type=self.exchange_config.type,
        )

        return Publisher(
            exchange=exchange,
            exchange_config=self.exchange_config,
        )

    async def __aexit__(self, *_):
        await self.conn.__aexit__(None, None, None)
