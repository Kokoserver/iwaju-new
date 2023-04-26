import datetime
import typing as t
from uuid import UUID
import sqlalchemy as sa
from pydantic import BaseModel
from fastapi import HTTPException
from db.model import Base
from db.config import async_session
from src.base.enum.sort_type import SortOrder
from src.lib.utils.random_string import random_str

ModelType = t.TypeVar("ModelType", bound=Base)


class BaseRepository(t.Generic[ModelType]):
    def __init__(self, model: t.Type[ModelType]):
        self.model = model
        self.db = async_session()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.db.close()

    def make_slug(self, name: str, random_length: int = 10) -> str:
        slug = f"{name.replace(' ', '-').replace('_', '-')[:30]}-{random_str(random_length).strip().lower()}"
        return slug

    def make_select_from_str(self, select: str = "") -> t.List[str]:
        select = [item.strip() for item in select.split(",") if select is not None]

        return select

    async def get(
        self, id: UUID, load_related: bool = False, expunge: bool = True
    ) -> t.Optional[ModelType]:
        stmt = None
        if load_related:
            stmt = (
                sa.select(self.model)
                .options(sa.orm.selectinload("*"))
                .where(self.model.id == str(id))
            )
            result = await self.db.execute(stmt)
            if result:
                if expunge:
                    self.db.expunge_all()
                return result.scalar()
            return None
        else:
            stmt = sa.select(self.model).where(self.model.id == str(id))
            result = await self.db.execute(stmt)
            if result is None:
                return None
            if expunge:
                self.db.expunge_all()
            return result.scalars().first()

    async def get_by_id(self, id: UUID, expunge: bool = True) -> ModelType:
        stm = sa.select(self.model).where(self.model.id == id)
        get_cat = await self.db.execute(stm)
        if expunge:
            self.db.expunge_all()
        return get_cat.scalar()

    async def get_by_props(
        self,
        prop_name: str,
        prop_values: t.List[str],
        load_related: bool = False,
        expunge: bool = True,
    ) -> t.List[ModelType]:
        prop_column = getattr(self.model, prop_name)
        if isinstance(prop_column.type, (sa.types.Integer, sa.types.Enum)):
            prop_values = [prop_column.type.python_type(v) for v in prop_values]
        elif isinstance(prop_column.type, sa.types.DateTime):
            prop_values = [datetime.datetime.fromisoformat(v) for v in prop_values]
        elif isinstance(prop_column.type, sa.types.Date):
            prop_values = [datetime.datetime.strptime(v, "%Y-%m-%d").date() for v in prop_values]
        elif isinstance(prop_column.type, sa.types.Time):
            prop_values = [datetime.datetime.strptime(v, "%H:%M:%S").time() for v in prop_values]
        elif isinstance(prop_column.type, sa.types.Boolean):
            prop_values = [True if v.lower() == "true" else False for v in prop_values]
        elif isinstance(prop_column.type, sa.types.UUID):
            prop_values = [UUID(v) for v in prop_values]
        stm = sa.select(self.model)
        if load_related:
            stm = stm.options(sa.orm.selectinload("*"))
        stm = sa.select(self.model).where(prop_column.in_(prop_values))
        get_cats = await self.db.execute(stm)
        if expunge:
            self.db.expunge_all()
        return get_cats.scalars().all()

    async def get_by_ids(
        self,
        ids: t.List[UUID],
        load_related: bool = False,
        expunge: bool = True,
    ) -> t.List[ModelType]:
        query = sa.select(self.model)
        if load_related:
            query = query.options(sa.orm.selectinload("*"))
        query = query.where(self.model.id.in_([str(id) for id in ids]))
        results = await self.db.execute(query)
        if expunge:
            self.db.expunge_all()
        return results.scalars().all()

    async def update(
        self, id: UUID, obj: t.Union[dict, BaseModel], expunge: bool = True
    ) -> t.Optional[ModelType]:
        stmt = (
            sa.update(self.model)
            .where(self.model.id == str(id))
            .values(obj.dict() if isinstance(obj, BaseModel) else obj)
            .returning(self.model)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        if expunge:
            self.db.expunge_all()
        return result.scalar_one_or_none()

    async def delete(self, id: UUID, expunge: bool = True) -> t.Optional[ModelType]:
        result = await self.db.execute(sa.select(self.model).where(self.model.id == str(id)))
        row = result.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Object not found")
        stmt = sa.delete(self.model).where(self.model.id == str(id))
        await self.db.execute(stmt)
        await self.db.commit()
        if expunge:
            self.db.expunge_all()
        return row

    async def delete_many(self, ids: t.List[UUID], expunge: bool = True) -> int:
        if not ids:
            return 0
        stmt = sa.delete(self.model).where(self.model.id.in_(ids))
        result = await self.db.execute(stmt)
        await self.db.commit()
        if expunge:
            self.db.expunge_all()
        return result.rowcount

    async def get_count(self, expunge: bool = True) -> t.Optional[int]:
        stm = sa.select(sa.func.count(self.model.id))
        result = await self.db.execute(stm)
        if expunge:
            self.db.expunge_all()
        count = result.scalar()
        return count if count is not None else None

    async def create(self, obj: t.Union[dict, BaseModel], expunge: bool = True) -> ModelType:
        to_create = {}
        if isinstance(obj, BaseModel):
            to_create = obj.dict()
        if isinstance(obj, dict):
            to_create = obj
        if not to_create:
            raise ValueError("Cannot create empty object")
        to_create_filtered = {k: v for k, v in to_create.items() if hasattr(self.model, k)}
        try:
            result = self.model(**to_create_filtered)
            self.db.add(result)
            await self.db.commit()
            await self.db.refresh(result)
            if expunge:
                self.db.expunge_all()
            return result
        except sa.exc.IntegrityError as e:
            await self.db.rollback()
            if "duplicate key" in str(e):
                raise HTTPException(status_code=409, detail="Conflict error")
            else:
                raise e

    async def create_many(
        self, objs: t.List[t.Union[dict, BaseModel]], expunge: bool = True
    ) -> t.List[ModelType]:
        to_create_list: t.List[self.model] = []

        for obj in objs:
            if isinstance(obj, BaseModel):
                new_obj = obj.dict(exclude_unset=True)
                filtered_obj = {
                    key: value for key, value in new_obj.items() if hasattr(self.model, key)
                }
                to_create_list.append(filtered_obj)

            if isinstance(obj, dict):
                filtered_obj = {
                    key: value for key, value in obj.items() if hasattr(self.model, key)
                }
                to_create_list.append(filtered_obj)

        try:
            stmt = sa.insert(self.model).values(to_create_list)
            result = await self.db.execute(stmt)
            await self.db.commit()
            if expunge:
                self.db.expunge_all()
            return result
        except sa.exc.IntegrityError as e:
            await self.db.rollback()
            if "duplicate key" in str(e):
                raise HTTPException(status_code=409, detail="Conflict Error")
            else:
                raise e

    async def get_by_attr(
        self,
        attr: dict,
        first: bool = False,
        load_related: bool = False,
        expunge: bool = True,
    ) -> t.Union[ModelType, t.List[ModelType]]:
        if isinstance(attr, dict):
            # create a new dictionary with only the keys that exist in the model
            valid_keys = [key for key in attr.keys() if hasattr(self.model, key)]
            attr_filtered = {key: attr[key] for key in valid_keys}

            filters = [getattr(self.model, key) == value for key, value in attr_filtered.items()]

            stmt = None
            if load_related:
                stmt = (
                    sa.select(self.model).options(sa.orm.selectinload("*")).where(sa.and_(*filters))
                )
            else:
                stmt = sa.select(self.model).where(sa.and_(*filters))

            results = await self.db.execute(stmt)
            if expunge:
                self.db.expunge_all()
            if first:
                return results.scalar()
            return results.scalars().all()
        raise Exception(f"dictionary is expected, but {type(attr)} is passed")

    async def filter(
        self,
        filter_string: str = None,
        select_columns=None,
        page=1,
        per_page=10,
        sort_by: SortOrder = SortOrder.asc,
        order_by: str = None,
        strict_search: dict = None,
        load_related: bool = False,
        expunge: bool = True,
    ) -> t.Tuple[t.List[ModelType], int]:
        select_obj = sa.select(self.model)
        if select_columns:
            select_columns = self.make_select_from_str(select=select_columns)
        if select_columns:
            relationships = sa.inspect(self.model).relationships
            relationship_names = [rel.key for rel in relationships]
            for column in select_columns:
                if column in relationship_names:
                    select_columns.pop(select_columns.index(column))
        if load_related:
            select_obj = select_obj.options(sa.orm.selectinload("*"))

        if strict_search:
            condition_list = []
            for key, val in strict_search.items():
                if hasattr(self.model, key) and val is not None:
                    condition_list.append(sa.and_(getattr(self.model, key) == val))
            select_obj = select_obj.where(
                sa.and_(
                    *[
                        getattr(self.model, key) == value
                        for key, value in strict_search.items()
                        if value is not None and hasattr(self.model, key)
                    ],
                )
            )

        filter_condition = None
        if filter_string:
            for column in self.model.__table__.c:
                if str(column.type).startswith("VARCHAR"):
                    if filter_condition is None:
                        filter_condition = column.ilike(f"%{filter_string}%")
                    else:
                        filter_condition = filter_condition | column.ilike(f"%{filter_string}%")
            if filter_condition is not None:
                select_obj = select_obj.where(filter_condition)

        if select_columns:
            select_list = [
                getattr(self.model, col) for col in select_columns if hasattr(self.model, col)
            ]

            if select_list:
                select_obj = select_obj.with_only_columns(*select_list)
            else:
                select_obj = select_obj.with_only_columns(*self.model.__table__.c)

        if order_by is not None:
            order_by = self.make_select_from_str(order_by)
            for column in order_by:
                if sort_by == SortOrder.desc and hasattr(self.model, column):
                    select_obj = select_obj.order_by(getattr(self.model, column).desc())
                elif hasattr(self.model, column) and sort_by == SortOrder.asc:
                    select_obj = select_obj.order_by(getattr(self.model, column))

        results = await self.db.execute(select_obj.limit(per_page).offset((page - 1) * per_page))
        if expunge:
            self.db.expunge_all()
        return [row._asdict() for row in results]
