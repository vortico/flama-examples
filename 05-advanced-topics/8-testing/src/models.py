import sqlalchemy


metadata = sqlalchemy.MetaData()
table = sqlalchemy.Table(
    "animal",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("name", sqlalchemy.String, nullable=False),
)
