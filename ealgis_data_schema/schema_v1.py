import sqlalchemy as db
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import relationship, backref
import datetime


class TableInfo(object):
    "metadata for each table that has been loaded into the system"
    __tablename__ = 'table_info'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), unique=True, index=True)
    metadata_json = db.Column(db.String(2048))

    @declared_attr
    def geometry_source(cls):
        return relationship(
            'GeometrySource',
            backref=backref('table_info'),
            cascade="all",
            uselist=False)

    @declared_attr
    def column_info(cls):
        return relationship(
            'ColumnInfo',
            backref=backref('table_info'),
            cascade="all",
            lazy='dynamic')

    @declared_attr
    def linkages(cls):
        return relationship(
            'GeometryLinkage',
            backref=backref('attribute_table'),
            cascade="all",
            lazy='dynamic')


class ColumnInfo(object):
    "metadata for columns in the tabbles"
    __tablename__ = 'column_info'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), index=True)
    metadata_json = db.Column(db.String(2048))
    __table_args__ = (db.UniqueConstraint('name', 'tableinfo_id'), )

    @declared_attr
    def tableinfo_id(cls):
        return db.Column(db.Integer, db.ForeignKey('table_info.id'), index=True, nullable=False)


class GeometrySourceProjected(object):
    "details of an additional column (on the same table as the source) with the source reprojected to this srid"
    __tablename__ = 'geometry_source_projected'
    id = db.Column(db.Integer, primary_key=True)
    srid = db.Column(db.Integer, nullable=False)
    column = db.Column(db.String(256), nullable=False)

    @declared_attr
    def geometry_source_id(cls):
        return db.Column(db.Integer, db.ForeignKey('geometry_source.id'), index=True, nullable=False)


class GeometrySource(object):
    "table describing sources of geometry information: the table, and the column"
    __tablename__ = 'geometry_source'
    id = db.Column(db.Integer, primary_key=True)
    geometry_type = db.Column(db.String(256), nullable=False)
    column = db.Column(db.String(256), nullable=False)
    srid = db.Column(db.Integer, nullable=False)
    gid = db.Column(db.String(256), nullable=False)

    @declared_attr
    def tableinfo_id(cls):
        return db.Column(db.Integer, db.ForeignKey('table_info.id'), index=True, nullable=False)

    @declared_attr
    def linkages(cls):
        return relationship(
            'GeometryLinkage',
            backref=backref('geometry_source'),
            cascade="all",
            lazy='dynamic')

    @declared_attr
    def reprojections(cls):
        return relationship(
            'GeometrySourceProjected',
            backref=backref('geometry_source'),
            cascade="all",
            lazy='dynamic')

    @declared_attr
    def from_relations(cls):
        return relationship(
            'GeometryRelation',
            backref=backref('geometry_source'),
            cascade="all",
            lazy='dynamic',
            foreign_keys="[GeometryRelation.geo_source_id]")

    @declared_attr
    def with_relations(cls):
        return relationship(
            'GeometryRelation',
            backref=backref('overlaps_geometry_source'),
            cascade="all",
            lazy='dynamic',
            foreign_keys="[GeometryRelation.overlaps_with_id]")

    def __repr__(self):
        return "GeometrySource<%s.%s>" % (self.table_info.name, self.column)

    def srid_column(self, srid):
        if self.srid == srid:
            return self.column
        proj = [t for t in self.geometry_source_projected_collection if t.srid == srid]
        if len(proj) == 1:
            return proj[0].column
        else:
            return None


class GeometryLinkage(object):
    "details of links to tie attribute data to columns in a geometry table"
    __tablename__ = 'geometry_linkage'
    id = db.Column(db.Integer, primary_key=True)
    geo_column = db.Column(db.String(256))

    @declared_attr
    def attr_table_info_id(cls):
        """
        the attribute table, and the column which links a row in our geomtry table with
        a row in the attribute table
        """
        return db.Column(db.Integer, db.ForeignKey('table_info.id'), nullable=False)

    @declared_attr
    def geo_source_id(cls):
        """
        the geometry table, and the column which links a row in our attribute table with
        a row in the geometry table
        """
        return db.Column(db.Integer, db.ForeignKey('geometry_source.id'), index=True, nullable=False)

    attr_column = db.Column(db.String(256))


class EALGISMetadata(object):
    "metadata table for a given set of datasets in a schema"
    __tablename__ = 'ealgis_metadata'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256))
    version = db.Column(db.Float())
    description = db.Column(db.Text())
    date = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)


_schemas = {}


class SchemaStore:
    _schema_classes = [
        EALGISMetadata,
        TableInfo,
        ColumnInfo,
        GeometrySourceProjected,
        GeometrySource,
        GeometryLinkage,
    ]

    def __init__(self):
        self.bases = {}
        self.classes = {}

    def _import_schema(self, schema_name):
        Base = self.bases[schema_name] = declarative_base()
        self.classes[schema_name] = classes = {}
        for cls in self._schema_classes:
            print("register class:", cls)
            classes[cls.__name__] = type(schema_name.replace('_', '').upper() + cls.__name__, (cls, Base), {'__table_args__': {'schema': schema_name}})

    def load_schema(self, schema_name):
        if schema_name not in self.classes:
            self._import_schema(schema_name)
        print(self.classes, self.bases)
        return self.bases[schema_name], self.classes[schema_name]


store = SchemaStore()
