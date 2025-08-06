from django.db import models

class Proyecto(models.Model):
    numero = models.IntegerField(null=True, blank=True)  
    codigo = models.CharField(max_length=50, unique=True)
    tipo_epi_api = models.CharField(max_length=20, null=True, blank=True)  
    area = models.CharField(max_length=20, null=True, blank=True)  
    nombre = models.CharField(max_length=255)
    estado = models.CharField(max_length=100, null=True, blank=True, default="Pendiente")
    ppto_total = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    ppto_gaf_2025 = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    identificado_2025 = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    proyectado_p6_2025 = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    ejecutado = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

class FlujoCaja(models.Model):
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE)

    tipo = models.CharField(max_length=20, choices=[
        ('PROG.', 'Programado'),
        ('PROG.P6', 'Programado P6'),
        ('REAL', 'Real')
    ])

    anio = models.IntegerField(default=2025)

    enero = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    febrero = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    marzo = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    abril = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    mayo = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    junio = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    julio = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    agosto = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    septiembre = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    octubre = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    noviembre = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    diciembre = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def total(self):
        return sum([
            self.enero, self.febrero, self.marzo, self.abril, self.mayo, self.junio,
            self.julio, self.agosto, self.septiembre, self.octubre, self.noviembre, self.diciembre
        ])
    
    def __str__(self):
        return f"{self.proyecto.codigo} - {self.tipo} - {self.anio}"

    
    def total(self):
        return sum([
            self.enero, self.febrero, self.marzo, self.abril, self.mayo, self.junio,
            self.julio, self.agosto, self.septiembre, self.octubre, self.noviembre, self.diciembre
        ])
