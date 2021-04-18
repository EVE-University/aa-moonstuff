from django.db import models
from datetime import timedelta


from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from eveuniverse.models import EveMoon, EveType


# Create your models here.
class Moonstuff(models.Model):

    class Meta:
        managed = False
        default_permissions = (())
        permissions = (
            ('access_moonstuff', 'Allows access to the moonstuff module'),
            ('access_moon_list', 'Allows access to list of all moons.'),
        )


class Material(models.Model):
    evetype = models.ForeignKey(EveType, on_delete=models.CASCADE, related_name='materials')
    material_evetype = models.ForeignKey(EveType, on_delete=models.CASCADE, related_name='from_types')
    quantity = models.IntegerField()

    class Meta:
        default_permissions = (())


class MaterialCheckSum(models.Model):
    checksum = models.CharField(max_length=255, null=True, default=None)

    class Meta:
        default_permissions = (())


class Resource(models.Model):
    ore = models.ForeignKey(EveType, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=11, decimal_places=10)
    moon = models.ForeignKey(EveMoon, on_delete=models.CASCADE, related_name='resources')

    @property
    def rarity(self):
        """
        Determine the rarity of the resource by its group_id. (Default is 0)
        :return:
        """
        rs = {1884: 4, 1920: 8, 1921: 16, 1922: 32, 1923: 64}
        return rs.get(self.ore.eve_group_id, 0)

    class Meta:
        default_permissions = ('add',)


class Refinery(models.Model):
    structure_id = models.BigIntegerField(primary_key=True)
    evetype = models.ForeignKey(EveType, on_delete=models.CASCADE)
    name = models.CharField(null=True, max_length=255)  # Might not actually need this.
    corp = models.ForeignKey(EveCorporationInfo, on_delete=models.CASCADE, related_name='refineries')
    observer = models.BooleanField(default=True)

    def __str__(self):
        if self.name is None:
            return f'Unknown Structure ID{self.structure_id} ({self.evetype.name})'
        return f'{self.name}'

    class Meta:
        default_permissions = (())


class TrackingCharacter(models.Model):
    character = models.ForeignKey(EveCharacter, on_delete=models.CASCADE)
    latest_notification_id = models.BigIntegerField(null=True, default=0)
    last_notification_check = models.DateTimeField(null=True)

    def __str__(self):
        return f'{self.character.character_name}'

    class Meta:
        default_permissions = ('add',)


class Extraction(models.Model):
    start_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    decay_time = models.DateTimeField()
    moon = models.ForeignKey(EveMoon, on_delete=models.CASCADE, related_name='extractions')
    refinery = models.ForeignKey(Refinery, on_delete=models.CASCADE, related_name='extractions')
    corp = models.ForeignKey(EveCorporationInfo, on_delete=models.CASCADE, related_name='extractions')
    cancelled = models.BooleanField(null=False, default=False)
    jackpot = models.BooleanField(default=False)
    active = models.BooleanField(default=False)
    depleted = models.BooleanField(default=False)
    total_volume = models.BigIntegerField(null=True)

    @property
    def despawn(self):
        """
        Returns the latest despawn time. Actual despawn can be up to -3h from returned time depending on when the
            moon drill laser was fired. Actual despawn should never occur after returned time however.
        :return:
        """
        return self.decay_time + timedelta(hours=48)

    class Meta:
        default_permissions = (())
        unique_together = (('start_time', 'moon'),)


class LedgerEntry(models.Model):
    observer = models.ForeignKey(Refinery, on_delete=models.CASCADE, related_name='entries')
    character_id = models.IntegerField()  # There is no guarantee that we will have a character object for this.
    last_updated = models.DateField()
    quantity = models.BigIntegerField()
    recorded_corporation_id = models.IntegerField()
    evetype = models.ForeignKey(EveType, on_delete=models.CASCADE, related_name='ledger_entries')

    class Meta:
        default_permissions = (())
        # For each observer we only want one record per day per character per ore type.
        unique_together = (('observer', 'last_updated', 'character_id', 'evetype'),)
