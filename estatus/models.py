from django.db import models

class EstatusSemanal(models.Model):
    prioridad = models.IntegerField(null=True, blank=True)
    codigo_proyecto = models.CharField(max_length=50)
    jefe_proyecto = models.CharField(max_length=50)
    eecc = models.CharField(max_length=50)
    proyecto = models.CharField(max_length=250)
    servicio = models.CharField(max_length=250)
    autor = models.CharField(max_length=50)
    fecha = models.DateField()
    comentario = models.CharField(max_length=2000)

    def __str__(self):
        return f"{self.codigo_proyecto} - {self.fecha}"
