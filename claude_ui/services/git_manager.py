import logging
import os
import shutil
import uuid
from pathlib import Path
from typing import List, Optional

import git
from git import Repo, GitCommandError

from claude_ui.config import settings
from claude_ui.models.database import Worktree, Project
from claude_ui.core.database import get_db_context

logger = logging.getLogger(__name__)


class GitManager:
    """Manages git operations and worktrees"""
    
    def __init__(self):
        self.worktree_base = settings.default_worktree_base
        self.worktree_base.mkdir(parents=True, exist_ok=True)
    
    async def create_worktree(
        self,
        project: Project,
        branch_name: str,
        worktree_name: Optional[str] = None,
    ) -> Worktree:
        """Create a new git worktree for a project"""
        # Open the main repository
        try:
            repo = Repo(project.path)
        except Exception as e:
            raise ValueError(f"Invalid git repository at {project.path}: {e}")
        
        # Generate worktree name if not provided
        if not worktree_name:
            worktree_name = f"{project.name}-{branch_name}-{uuid.uuid4().hex[:8]}"
        
        # Create worktree path
        worktree_path = self.worktree_base / project.id / worktree_name
        worktree_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Check if branch exists
            if branch_name not in [ref.name for ref in repo.refs]:
                # Create new branch
                repo.create_head(branch_name)
            
            # Create worktree
            repo.git.worktree("add", str(worktree_path), branch_name)
            
            # Create database record
            worktree_id = str(uuid.uuid4())
            async with get_db_context() as db:
                worktree = Worktree(
                    id=worktree_id,
                    project_id=project.id,
                    name=worktree_name,
                    branch=branch_name,
                    path=str(worktree_path),
                )
                db.add(worktree)
                await db.commit()
                await db.refresh(worktree)
            
            logger.info(f"Created worktree {worktree_name} for project {project.name}")
            return worktree
            
        except GitCommandError as e:
            logger.error(f"Failed to create worktree: {e}")
            # Clean up if worktree was partially created
            if worktree_path.exists():
                shutil.rmtree(worktree_path)
            raise ValueError(f"Failed to create worktree: {e}")
    
    async def remove_worktree(self, worktree: Worktree) -> None:
        """Remove a git worktree"""
        # Get project
        async with get_db_context() as db:
            project = await db.get(Project, worktree.project_id)
            if not project:
                raise ValueError("Project not found")
        
        try:
            # Open the main repository
            repo = Repo(project.path)
            
            # Remove worktree
            repo.git.worktree("remove", worktree.path, force=True)
            
            # Clean up directory if it still exists
            worktree_path = Path(worktree.path)
            if worktree_path.exists():
                shutil.rmtree(worktree_path)
            
            # Remove from database
            async with get_db_context() as db:
                worktree_db = await db.get(Worktree, worktree.id)
                if worktree_db:
                    await db.delete(worktree_db)
                    await db.commit()
            
            logger.info(f"Removed worktree {worktree.name}")
            
        except GitCommandError as e:
            logger.error(f"Failed to remove worktree: {e}")
            raise ValueError(f"Failed to remove worktree: {e}")
    
    async def list_worktrees(self, project: Project) -> List[dict]:
        """List all worktrees for a project"""
        try:
            repo = Repo(project.path)
            worktrees = []
            
            # Get worktree list from git
            worktree_output = repo.git.worktree("list", "--porcelain")
            
            current_worktree = {}
            for line in worktree_output.split("\n"):
                if not line:
                    if current_worktree:
                        worktrees.append(current_worktree)
                        current_worktree = {}
                elif line.startswith("worktree "):
                    current_worktree["path"] = line[9:]
                elif line.startswith("HEAD "):
                    current_worktree["head"] = line[5:]
                elif line.startswith("branch "):
                    current_worktree["branch"] = line[7:]
            
            if current_worktree:
                worktrees.append(current_worktree)
            
            return worktrees
            
        except GitCommandError as e:
            logger.error(f"Failed to list worktrees: {e}")
            return []
    
    async def get_branch_list(self, project: Project) -> List[str]:
        """Get list of branches for a project"""
        try:
            repo = Repo(project.path)
            return [ref.name for ref in repo.refs if "refs/heads/" in ref.path]
        except Exception as e:
            logger.error(f"Failed to get branch list: {e}")
            return []
    
    async def create_branch(
        self,
        project: Project,
        branch_name: str,
        from_branch: Optional[str] = None,
    ) -> None:
        """Create a new branch in the project"""
        try:
            repo = Repo(project.path)
            
            # Use default branch if from_branch not specified
            if not from_branch:
                from_branch = project.default_branch
            
            # Create new branch
            source = repo.refs[from_branch] if from_branch in repo.refs else repo.head
            repo.create_head(branch_name, source)
            
            logger.info(f"Created branch {branch_name} from {from_branch}")
            
        except GitCommandError as e:
            logger.error(f"Failed to create branch: {e}")
            raise ValueError(f"Failed to create branch: {e}")
    
    async def get_git_status(self, path: str) -> dict:
        """Get git status for a repository or worktree"""
        try:
            repo = Repo(path)
            
            status = {
                "branch": repo.active_branch.name if not repo.head.is_detached else "detached",
                "clean": not repo.is_dirty(),
                "modified": [item.a_path for item in repo.index.diff(None)],
                "untracked": repo.untracked_files,
                "staged": [item.a_path for item in repo.index.diff("HEAD")],
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get git status: {e}")
            return {
                "error": str(e),
                "branch": "unknown",
                "clean": False,
                "modified": [],
                "untracked": [],
                "staged": [],
            }