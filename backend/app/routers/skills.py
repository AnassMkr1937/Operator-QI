from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.base import new_uuid
from app.models.skill import Skill
from app.schemas.skill import SkillCreate, SkillRead, SkillUpdate

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("", response_model=list[SkillRead])
def list_skills(
    operator_id: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[Skill]:
    q = db.query(Skill)
    if operator_id:
        q = q.filter(Skill.operator_id == operator_id)
    return q.offset(skip).limit(limit).all()


@router.post("", response_model=SkillRead, status_code=status.HTTP_201_CREATED)
def create_skill(payload: SkillCreate, db: Session = Depends(get_db)) -> Skill:
    skill = Skill(id=new_uuid(), **payload.model_dump())
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


@router.get("/{skill_id}", response_model=SkillRead)
def get_skill(skill_id: str, db: Session = Depends(get_db)) -> Skill:
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found.")
    return skill


@router.patch("/{skill_id}", response_model=SkillRead)
def update_skill(
    skill_id: str, payload: SkillUpdate, db: Session = Depends(get_db)
) -> Skill:
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(skill, field, value)
    db.commit()
    db.refresh(skill)
    return skill


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_skill(skill_id: str, db: Session = Depends(get_db)) -> None:
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found.")
    db.delete(skill)
    db.commit()
