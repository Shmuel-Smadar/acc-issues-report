from django.conf import settings


class ProjectService:
    def __init__(self, client):
        self.client = client

    def list_and_print_projects(self):
        projects = self.client.list_projects_admin()
        if not projects:
            raise RuntimeError("No projects found")

        names = [p.get("name") for p in projects]
        print("DEBUG available projects:", names)

        if settings.TARGET_PROJECT_NAME in names:
            proj = next(p for p in projects if p.get("name") == settings.TARGET_PROJECT_NAME)
            print(f"DEBUG: Found target project {proj.get('name')} (id={proj.get('id')})")
        else:
            raise RuntimeError(
                f"Project '{settings.TARGET_PROJECT_NAME}' not found. Available projects: {names}"
            )

        return names
