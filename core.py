from fastapi import FastAPI,Depends,Form,File,UploadFile, HTTPException
from schemas import Addnotes
from sqlalchemy.orm import Session
from database import SessionLocal,engine,Base,get_session
from models import Item,User
from image  import imagekit
import os
import jwt
from fastapi.middleware.cors import CORSMiddleware
from security import (
    hash_password,
    verify_password,
    create_access_token,
    oauth2_scheme,
    SECRET_KEY,
    ALGORITHM
)


Base.metadata.create_all(bind=engine)
app=FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_session)
):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        username = payload.get("sub")

        if username is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    user = db.query(User).filter(
        User.username == username
    ).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return user
@app.post("/login")
def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_session)
):

    user = db.query(User).filter(
        User.username == username
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    access_token = create_access_token(
        data={"sub": user.username}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.post("/register")
def register(
    username:str=Form(...),
    password:str=Form(...),
    db:Session=Depends(get_session)
):
    existing_user=db.query(User).filter(
        User.username==username
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed_password = hash_password(password)
    new_user=User(
        username=username,
        hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message":"User register successfully"
    }
@app.get("/notes")
def shownotes(session:Session=Depends(get_session)):
    items=session.query(Item).all()
    if  not items:
        return {"message":"Oops! There are no notes"}
        
    else:
        return items

@app.get("/id")
def show_specific_note(noteid:int,session:Session=Depends(get_session)):
    note_id=session.query(Item).filter(Item.id==noteid).first()
    if note_id is None:
        raise HTTPException(status_code=404,detail="Id not found")
    return note_id
        

@app.post("/notes")
async def add(
    title: str = Form(...),
    content: str = Form(...),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_session)
):

    image_url = None
    file_id = None
    file_type = None
    file_name = None

    # Only upload to ImageKit if a file was provided
    if file:
        try:
            file_bytes = await file.read()

            response = imagekit.files.upload(
                file=file_bytes,
                file_name=file.filename
            )

            image_url = getattr(response, "url", None) or response.get("url")
            file_id = getattr(response, "file_id", None) or response.get("file_id")

            if not image_url:
                raise Exception("No URL returned from ImageKit")

            file_type = file.content_type or "unknown"
            file_name = file.filename

        except Exception as e:
            print("ImageKit upload error:", e)
            raise HTTPException(
                status_code=500,
                detail="Image is not uploaded"
            )

    new_item = Item(
        title=title,
        content=content,
        url=image_url,
        imagekit_file_id=file_id,
        file_type=file_type,
        file_name=file_name
    )

    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return {
        "message": "Successfully received notes",
        "URL": image_url
    }

@app.delete("/delete-by-id")
def delete_By_id(id: int, session: Session = Depends(get_session)):
    id_note_delete = session.query(Item).filter(Item.id == id).first()
    if id_note_delete is None:
        raise HTTPException(status_code=404, detail="Id is not there")
    
    # Check if we actually have a file ID saved
    if id_note_delete.imagekit_file_id:
        try:
            # Execute deletion
           imagekit.files.delete(
               id_note_delete.imagekit_file_id
            )
        except Exception as e:
            # This prints the real error (like 404 Not Found) to your backend terminal
            print(f"ImageKit API rejected deletion for ID {id_note_delete.imagekit_file_id}. Error: {e}")
    else:
        print(f"Skipping ImageKit deletion: Item ID {id} has no imagekit_file_id stored.")

    # Always delete the database entry even if the cloud image is missing
    session.delete(id_note_delete)
    session.commit()
    return {"message": "deleted successfully"}



@app.delete("/delete")
def remove(delete_item:str,session:Session=Depends(get_session)):
    titleofnote=session.query(Item).filter(Item.title==delete_item).first()

    if titleofnote is None:
        raise HTTPException(status_code=404,detail="Note not found")

    session.delete(titleofnote)
    session.commit()
    
    return {"message": "Note deleted successfully"}


@app.delete("/delete-all")
def delete_all(session: Session = Depends(get_session)):

    all_items = session.query(Item).all()

    if not all_items:
        return {"message": "Storage is already empty"}

    file_ids_to_delete = [
        item.imagekit_file_id
        for item in all_items
        if item.imagekit_file_id
    ]

    # Delete files from ImageKit
    if file_ids_to_delete:
        try:
            chunk_size = 100

            for i in range(0, len(file_ids_to_delete), chunk_size):
                chunk = file_ids_to_delete[i:i + chunk_size]

                response = imagekit.files.bulk.delete(
                    file_ids=chunk
                )

                print("ImageKit deletion response:", response)

        except Exception as e:
            print("ImageKit deletion failed:", repr(e))

            # IMPORTANT:
            # Don't delete the DB records if ImageKit deletion failed.
            raise HTTPException(
                status_code=500,
                detail="Failed to delete files from ImageKit"
            )

    # Delete database records
    session.query(Item).delete(synchronize_session=False)
    session.commit()

    return {"message": "Storage is cleared"}