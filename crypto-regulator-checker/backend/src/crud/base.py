import logging
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from ..db.base_class import Base

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model
        logger.info(f"Initialized CRUD operations for model: {model.__name__}")

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        try:
            logger.debug(f"Attempting to fetch {self.model.__name__} with id: {id}")
            result = db.query(self.model).filter(self.model.id == id).first()
            if result:
                logger.debug(f"Successfully retrieved {self.model.__name__} with id: {id}")
            else:
                logger.debug(f"No {self.model.__name__} found with id: {id}")
            return result
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching {self.model.__name__} with id {id}: {str(e)}")
            raise

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        try:
            logger.debug(f"Fetching multiple {self.model.__name__} records (skip: {skip}, limit: {limit})")
            results = db.query(self.model).offset(skip).limit(limit).all()
            logger.debug(f"Retrieved {len(results)} {self.model.__name__} records")
            return results
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching multiple {self.model.__name__} records: {str(e)}")
            raise

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        try:
            logger.debug(f"Creating new {self.model.__name__} with data: {obj_in}")
            obj_in_data = jsonable_encoder(obj_in)
            db_obj = self.model(**obj_in_data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            logger.info(f"Successfully created {self.model.__name__} with id: {db_obj.id}")
            return db_obj
        except SQLAlchemyError as e:
            logger.error(f"Database error while creating {self.model.__name__}: {str(e)}")
            db.rollback()
            raise

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        try:
            logger.debug(f"Updating {self.model.__name__} with id: {db_obj.id}")
            obj_data = jsonable_encoder(db_obj)
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.dict(exclude_unset=True)
            
            logger.debug(f"Update data for {self.model.__name__}: {update_data}")
            for field in obj_data:
                if field in update_data:
                    setattr(db_obj, field, update_data[field])
            
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            logger.info(f"Successfully updated {self.model.__name__} with id: {db_obj.id}")
            return db_obj
        except SQLAlchemyError as e:
            logger.error(f"Database error while updating {self.model.__name__} with id {db_obj.id}: {str(e)}")
            db.rollback()
            raise

    def remove(self, db: Session, *, id: int) -> ModelType:
        try:
            logger.debug(f"Attempting to remove {self.model.__name__} with id: {id}")
            obj = db.query(self.model).get(id)
            if obj is None:
                logger.warning(f"Cannot remove {self.model.__name__}: id {id} not found")
                return None
            
            db.delete(obj)
            db.commit()
            logger.info(f"Successfully removed {self.model.__name__} with id: {id}")
            return obj
        except SQLAlchemyError as e:
            logger.error(f"Database error while removing {self.model.__name__} with id {id}: {str(e)}")
            db.rollback()
            raise 