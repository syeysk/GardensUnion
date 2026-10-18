from django.db import models


class Link(models.Model):
    left_code = models.PositiveIntegerField('Код модели')
    left_id = models.PositiveIntegerField('ID сущности')
    right_code = models.PositiveIntegerField('Код модели')
    right_id = models.PositiveIntegerField('ID сущности')

    class Model:
        verbose_name = 'Связи'
        verbose_name_plural = 'Связь'
        constraints = [
            models.UniqueConstraint(
                fields=['left_code', 'left_id', 'right_code', 'right_id'],
                name='unique_connection',
            )
        ]
