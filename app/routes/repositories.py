from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.git_repository import GitRepository
from app.schemas.schemas import RepositoryCreate, RepositoryResponse

router = APIRouter(prefix="/api/repositories", tags=["repositories"])


@router.get("")
def list_repositories(db: Session = Depends(get_db)):
    repos = db.query(GitRepository).order_by(GitRepository.id).all()
    return [RepositoryResponse.from_orm_model(r) for r in repos]


@router.post("", status_code=201)
def create_repository(data: RepositoryCreate, db: Session = Depends(get_db)):
    repo = GitRepository(name=data.name, local_path=data.localPath)
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return RepositoryResponse.from_orm_model(repo)


@router.delete("/{repo_id}", status_code=204)
def delete_repository(repo_id: int, db: Session = Depends(get_db)):
    repo = db.query(GitRepository).filter(GitRepository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="仓库不存在")
    db.delete(repo)
    db.commit()
