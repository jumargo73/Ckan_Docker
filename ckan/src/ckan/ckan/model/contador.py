from sqlalchemy import Column, Integer, String, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import and_, or_
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict

import ckan.model.meta as meta
import ckan.model.core as core
import ckan.model.types as _types
import ckan.model.domain_object as domain_object
from ckan.model.types import make_uuid



DeclarativeBase = declarative_base(metadata=meta.metadata)


class Contadores(DeclarativeBase,domain_object.DomainObject):

    __tablename__ = 'contadores'

    id = Column(Integer, primary_key=True,autoincrement=True)
    package_Id = Column(String, nullable=False)
    source_Id = Column(String, nullable=False)
    contVistas = Column(Integer, nullable=False,default=0)
    contDownload = Column(Integer, nullable=False,default=0)

    __table_args__ = (
        UniqueConstraint('source_Id', 'package_Id',name='uix_source_package'),
    )

    def __init__(self,  sourceId=None,packageId=None, **kwargs ):
        super().__init__(**kwargs)
        self.sourceId =  sourceId
        self.packageId = packageId

        
        # Garantizar valores por defecto si no vienen
        self.contVistas = kwargs.get("contVistas", 0)
        self.contDownload = kwargs.get("contDownload", 0)
        