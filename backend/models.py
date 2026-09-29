from sqlalchemy import Column, Integer, String, Boolean, Float, Numeric, DateTime, ForeignKey, Date
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class Source(Base):
    __tablename__ = 'sources'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    type = Column(String(20), nullable=False) # 'airline' or 'ota'
    base_url = Column(String(255))
    robots_ok = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Route(Base):
    __tablename__ = 'routes'
    
    id = Column(String(10), primary_key=True, index=True) # e.g. "DEL-BOM"
    origin = Column(String(3), nullable=False)
    dest = Column(String(3), nullable=False)
    dgca_pax_share = Column(Float)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class RawQuote(Base):
    __tablename__ = 'raw_quotes'
    
    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey('sources.id'))
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    payload_ref = Column(String(255)) # Path to MinIO/S3 object or local file
    status = Column(String(20)) # 'success', 'failed', 'blocked'

class Fare(Base):
    __tablename__ = 'fares'
    
    id = Column(Integer, primary_key=True, index=True)
    raw_quote_id = Column(Integer, ForeignKey('raw_quotes.id'), nullable=True)
    data_mode = Column(String(20), default="fixture") # fixture, synthetic, external, official, live
    source_reference = Column(String(255), nullable=True)
    dataset_version = Column(String(50), nullable=True)
    route_id = Column(String(10), ForeignKey('routes.id'))
    carrier = Column(String(50), nullable=False)
    flight_no = Column(String(20))
    dep_dt = Column(DateTime(timezone=True))
    dep_bucket = Column(String(20))
    lead_days = Column(Integer)
    fare_class = Column(String(20))
    base_fare = Column(Numeric(10, 2))
    taxes = Column(Numeric(10, 2))
    udf = Column(Numeric(10, 2))
    conv_fee = Column(Numeric(10, 2))
    total_fare = Column(Numeric(10, 2))
    source_id = Column(Integer, ForeignKey('sources.id'))
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    is_outlier = Column(Boolean, default=False)
    is_soldout = Column(Boolean, default=False)
    
class Weight(Base):
    __tablename__ = 'weights'
    
    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(20), nullable=False)
    data_mode = Column(String(20), default="fixture")
    source = Column(String(50), default="development_fixture")
    source_reference = Column(String(255), nullable=True)
    dataset_version = Column(String(50), nullable=True)
    methodology = Column(String(50), nullable=True)
    effective_from = Column(DateTime(timezone=True), nullable=True)
    effective_to = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    route_id = Column(String(10), ForeignKey('routes.id'), nullable=True)
    carrier = Column(String(50), nullable=True)
    lead_days = Column(Integer, nullable=True)
    weight = Column(Float, nullable=False)
    
class IndexDaily(Base):
    __tablename__ = 'index_daily'
    
    id = Column(Integer, primary_key=True, index=True)
    data_mode = Column(String(20), default="fixture")
    source_reference = Column(String(255), nullable=True)
    dataset_version = Column(String(50), nullable=True)
    weight_version = Column(String(20), nullable=True)
    methodology_version = Column(String(20), nullable=True)
    date = Column(Date, nullable=False)
    level = Column(String(50))
    variant = Column(String(20))
    route_id = Column(String(10), nullable=True)
    carrier = Column(String(50), nullable=True)
    value = Column(Numeric(10, 2))

class DGCAMonthly(Base):
    __tablename__ = 'dgca_monthly'
    
    id = Column(Integer, primary_key=True, index=True)
    data_mode = Column(String(20), default="fixture")
    source = Column(String(50), default="official")
    source_reference = Column(String(255), nullable=True)
    dataset_version = Column(String(50), nullable=True)
    month = Column(String(7), nullable=False)
    sector = Column(String(10), nullable=False)
    avg_fare = Column(Numeric(10, 2), nullable=False)
