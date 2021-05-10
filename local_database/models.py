import datetime
import os
import uuid

from sqlalchemy import PickleType
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    TIMESTAMP,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.types import TypeDecorator, CHAR

engine = create_engine(os.environ.get("DATABASE_URI"), encoding='utf8')
Session = sessionmaker(bind=engine)
Base = declarative_base()


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.
    """
    impl = CHAR

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                # hexstring
                return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value


class FileDB(Base):
    __tablename__ = 'files'
    id = Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    file_name = Column(String, nullable=False)
    field_delimiter = Column(String, nullable=False, server_default=",")
    lock = Column(Boolean, default=False)
    last_fragment_block_size = Column(Integer, default=1024)

    key_ranges = Column(MutableList.as_mutable(PickleType), default=[])
    file_fragments = Column(MutableList.as_mutable(PickleType), default=[])

    created_at = Column(TIMESTAMP, default=datetime.datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.datetime.now, onupdate=datetime.datetime.now)


class Shuffle(Base):
    __tablename__ = 'shuffle'
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(GUID(), ForeignKey("files.id"), nullable=False)
    file = relationship(
        FileDB,
        foreign_keys=file_id,
        primaryjoin=file_id == FileDB.id,
        lazy="joined",
    )
    list_of_min_hashes = Column(MutableList.as_mutable(PickleType), default=[])
    list_of_max_hashes = Column(MutableList.as_mutable(PickleType), default=[])
    data_nodes_processed = Column(Integer, default=0)

    created_at = Column(TIMESTAMP, default=datetime.datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.datetime.now, onupdate=datetime.datetime.now)

# Base.metadata.create_all(engine)
