from sqlalchemy import Column, Integer, String, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import and_, or_
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict

import ckan.model.meta as meta
import ckan.model.core as core
import ckan.model.types as _types
import ckan.model.domain_object as domain_object



DeclarativeBase = declarative_base(metadata=meta.metadata)


class ResourceRating(DeclarativeBase,domain_object.DomainObject):

    __tablename__ = 'resource_rating'

    id = Column(Integer, primary_key=True)
    resource_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    rating = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint('resource_id', 'user_id', name='_resource_user_uc'),
    )

    def __init__(self,  resource_id=None, user_id=None, rating=None, **kwargs):
        self.resource_id = resource_id
        self.user_id = user_id
        self.rating = rating