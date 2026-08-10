from .models import ProjectRole, ProjectUser, Project
from .interfaces import AbstractProjectHandler
from .permissions import ProjectPermissions
from .utils import is_versioned_file
from sqlalchemy import or_, and_
from typing import List
from ..auth.models import User, UserProfile


class ProjectHandler(AbstractProjectHandler):
    def get_push_permission(self, changes: dict):
        if not isinstance(changes, dict):
            return ProjectPermissions.Upload

        if changes.get("added") != [] or changes.get("removed") != []:
            return ProjectPermissions.Upload

        updated_files = changes.get("updated")
        if not isinstance(updated_files, list) or not updated_files:
            return ProjectPermissions.Upload

        editor_update = all(
            isinstance(file_change, dict)
            and isinstance(file_change.get("path"), str)
            and is_versioned_file(file_change["path"])
            and isinstance(file_change.get("diff"), dict)
            and bool(file_change["diff"])
            for file_change in updated_files
        )

        if editor_update:
            return ProjectPermissions.Edit
        else:
            return ProjectPermissions.Upload

    def get_email_receivers(self, project: Project) -> List[User]:
        return (
            User.query.join(UserProfile)
            .outerjoin(ProjectUser, ProjectUser.user_id == User.id)
            .filter(
                or_(
                    and_(
                        ProjectUser.project_id == project.id,
                        ProjectUser.role == ProjectRole.OWNER.value,
                    ),
                    User.is_admin,
                ),
                User.active,
                User.verified_email,
                UserProfile.receive_notifications,
            )
            .all()
        )
