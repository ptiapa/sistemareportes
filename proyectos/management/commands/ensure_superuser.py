# crea las carpetas si no existen: proyectos/management/commands/
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = "Crea/actualiza un superusuario desde variables de entorno si no existe."

    def handle(self, *args, **kwargs):
        User = get_user_model()
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")

        if not username or not password:
            self.stdout.write(self.style.WARNING(
                "DJANGO_SUPERUSER_USERNAME o DJANGO_SUPERUSER_PASSWORD no definidos; se omite."
            ))
            return

        u, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "is_staff": True, "is_superuser": True},
        )
        if created:
            u.set_password(password)
            u.save()
            self.stdout.write(self.style.SUCCESS(f"Superusuario '{username}' creado."))
        else:
            # opcional: actualizar password/email en cada deploy
            changed = False
            if password:
                u.set_password(password); changed = True
            if email and u.email != email:
                u.email = email; changed = True
            if changed:
                u.save()
                self.stdout.write(self.style.SUCCESS(f"Superusuario '{username}' actualizado."))
            else:
                self.stdout.write("Superusuario ya existe; sin cambios.")
