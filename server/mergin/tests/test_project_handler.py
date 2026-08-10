from ..sync.models import Project, ProjectRole
from .utils import add_user, create_project, create_workspace
from ..sync.project_handler import ProjectHandler
from ..sync.permissions import ProjectPermissions
from ..auth.models import User

from ..app import db


def test_project_permissions(client):
    project_handler = ProjectHandler()
    versioned_diff = {"path": "survey.gpkg", "diff": {"path": "diff"}}
    editor_changes = {
        "added": [],
        "removed": [],
        "updated": [versioned_diff],
    }

    assert (project_handler.get_push_permission(editor_changes) == ProjectPermissions.Edit)

    assert (
        project_handler.get_push_permission(
            {
                "added": [],
                "removed": [],
                "updated": [{"path": "survey.SQLITE",
                             "diff": {"path": "diff"}}],
            }
        ) == ProjectPermissions.Edit
    )

    upload_changes = [
        None,

        {},

        {"added": [], "removed": [], "updated": []},

        {
            "added": [{"path": "new.gpkg"}],
            "removed": [],
            "updated": [versioned_diff],
        },

        {
            "added": [],
            "removed": [{"path": "survey.gpkg"}],
            "updated": [versioned_diff],
        },

        {
            "added": [],
            "removed": [],
            "updated": [{"path": "survey.gpkg"}],
        },

        {
            "added": [],
            "removed": [],
            "updated": [{"path": "project.qgz", "diff": {"path": "diff"}}],
        },

        {
            "added": [],
            "removed": [],
            "updated": [versioned_diff, {"path": "notes.txt", "diff": {"path": "diff"}},],
        },

        {"added": {}, "removed": [], "updated": [versioned_diff]},

        {
            "added": [],
            "removed": [],
            "updated": [{"path": "survey.gpkg", "diff": {}}],
        },

        {"removed": [], "updated": [versioned_diff]},
    ]

    for changes in upload_changes:
        assert (project_handler.get_push_permission(changes) == ProjectPermissions.Upload)


def test_email_receivers(client):
    project_handler = ProjectHandler()
    # test project email receivers (owners and super admins)
    workspace = create_workspace()
    user = add_user()
    project = create_project("test_project", workspace, user)
    project.set_role(user.id, ProjectRole.READER)
    db.session.commit()
    receivers = project_handler.get_email_receivers(project)
    assert len(receivers) == 1

    project.set_role(user.id, ProjectRole.OWNER)
    db.session.commit()
    receivers = project_handler.get_email_receivers(project)
    assert len(receivers) == 2

    user.verified_email = False
    db.session.commit()
    receivers = project_handler.get_email_receivers(project)
    assert len(receivers) == 1

    user.verified_email = True
    user.profile.receive_notifications = False
    db.session.commit()
    receivers = project_handler.get_email_receivers(project)
    assert len(receivers) == 1

    user.profile.receive_notifications = True
    user.active = False
    db.session.commit()
    receivers = project_handler.get_email_receivers(project)
    assert len(receivers) == 1

    admin = User.query.filter(User.username == "mergin").first()
    admin.is_admin = False
    db.session.commit()
    receivers = project_handler.get_email_receivers(project)
    assert len(receivers) == 0
