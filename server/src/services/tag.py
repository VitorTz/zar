from src.schemas.urls import (
    UrlTagCreate, 
    UrlTag, 
    UrlTagUpdate, 
    UrlTagDelete, 
    UrlTagRelationCreate, 
    UrlTagRelationDelete, 
    UrlTagId, 
    URLResponse
)
from src.schemas.pagination import Pagination
from src.schemas.user import User
from src.tables import tag as tags_table
from src.tables import urls as urls_table
from asyncpg.exceptions import CheckViolationError, UniqueViolationError
from asyncpg import Connection
from fastapi.responses import Response
from fastapi.exceptions import HTTPException
from fastapi import status, Request
from typing import Optional
from src import util


async def get_user_tags(user: User, limit: int, offset: int, conn: Connection) -> Pagination[UrlTag]:
    return await tags_table.get_user_tags(user, limit, offset, conn)


async def create_tag(user: User, tag: UrlTagCreate, conn: Connection) -> UrlTag:
    try:
        return await tags_table.create_tag(user, tag, conn)
    except UniqueViolationError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tag already exists!")
    except CheckViolationError as e:
        detail = str(e)
        if "chk_color_hex" in detail:
            detail = "Invalid color"
        elif "chk_name_length" in detail:
            detail = "Tag name is too long"
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


async def update_tag(user: User, tag: UrlTagUpdate, conn: Connection) -> UrlTag:
    if not await tags_table.user_has_access_to_tag(user.id, tag.id, conn):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="This tag doesn't exist or you don't have access to this URL.")
    
    try:
        updated_tag: Optional[UrlTag] = await tags_table.update_tag(user, tag, conn)        
    except UniqueViolationError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tag already exists!")
    except CheckViolationError as e:
        detail = str(e)
        if "chk_color_hex" in detail:
            detail = "Invalid color"
        elif "chk_name_length" in detail:
            detail = "Tag name is too long"
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

    if updated_tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag não encontrada!")
    return updated_tag


async def delete_tag(user: User, tag: UrlTagDelete, conn: Connection):
    if not await tags_table.user_has_access_to_tag(user.id, tag.id, conn):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="This tag doesn't exist or you don't have access to this URL.")
    await tags_table.delete_user_tag(user.id, tag.id, conn)


async def get_urls_from_tag(request: Request, user: User, tag: UrlTagId, limit: int, offset: int, conn: Connection) -> Pagination[URLResponse]:
    base_url = util.extract_base_url(request)
    if not await tags_table.user_has_access_to_tag(user.id, tag.id, conn):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="This tag doesn't exist or you don't have access to this URL.")
    return await tags_table.get_tag_urls(base_url, tag.id, limit, offset, conn)


async def create_tag_relation(user: User, tag: UrlTagRelationCreate, conn: Connection):        
    if not await urls_table.user_has_access_to_url(user.id, tag.tag_id, conn):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="This tag doesn't exist or you don't have access to this URL.")
    
    await tags_table.create_tag_relation(tag.url_id, tag.tag_id, conn)
    return Response(status_code=status.HTTP_201_CREATED)


async def delete_tag_relation(user: User, tag: UrlTagRelationDelete, conn: Connection):
    if not await urls_table.user_has_access_to_url(user.id, tag.tag_id, conn):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="This tag doesn't exist or you don't have access to this URL.")
    await tags_table.delete_tag_relation(tag.url_id, tag.tag_id, conn)       


async def clear_tag(user: User, tag: UrlTagId, conn: Connection):
    if not await urls_table.user_has_access_to_url(user.id, tag.id, conn):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="This tag doesn't exist or you don't have access to this URL.")
    await tags_table.clear_tag(tag.id, conn)