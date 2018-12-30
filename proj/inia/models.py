from django.db import models
from django_enumfield import enum


class Publication(models.Model):
    legacy_id = models.IntegerField()
    authors = models.TextField()
    title = models.CharField(max_length=255)
    journal = models.CharField(max_length=255)
    pages = models.CharField(max_length=15)
    date_sub = models.DateTimeField()
    doi = models.CharField(max_length=255)
    url = models.CharField(max_length=255)
    display = models.CharField(max_length=255)
    htmlid = models.CharField(max_length=255) # journal paper htmlid


class Dataset(models.Model):
    TREATMENT_DID = "DID"
    TREATMENT_NONE = "NONE"
    TREATMENT_CIA = "CIA"
    TREATMENT_EOD = "EOD"
    TREATMENT_LPS = "LPS"

    TREATMENT_CHOICES = (
        (TREATMENT_DID, "DID"),
        (TREATMENT_NONE, "NONE"),
        (TREATMENT_CIA, "CIA"),
        (TREATMENT_EOD, "EOD"),
        (TREATMENT_LPS, "LPS"),
    )

    legacy_id = models.IntegerField()
    name = models.CharField(max_length=100)
    treatment = models.CharField(max_length=255, choices=TREATMENT_CHOICES)
    publication = models.ForeignKey(Publication, on_delete=models.PROTECT)


class SpeciesType(object):
    ''' The values of these enums are based on the NCBI taxonomy ID:
    https://www.ncbi.nlm.nih.gov/Taxonomy
    '''
    UNKNOWN = 'UNKNOWN'
    HOMO_SAPIENS = 'HOMO SAPIENS'  # Human tax id: 9606
    MUS_MUSCULUS = 'MUS MUSCULUS'    # Mouse tax id: 10090
    RATTUS_NORVEGICUS = 'RATTUS NORVEGICUS'  # Rat 10116

    SPECIES_CHOICES = (
        (HOMO_SAPIENS, 'HOMO SAPIENS'),
        (MUS_MUSCULUS, 'MUS MUSCULUS'),
        (RATTUS_NORVEGICUS, 'RATTUS NORVEGICUS')
    )

class Homologene(models.Model):
    '''This is basically just a lookup table that is populated by NCBI Homologene Database:
    https://www.ncbi.nlm.nih.gov/homologene
    Items that share the same homlogene_group_id across species are homologenes.
    '''
    homologene_group_id = models.IntegerField(db_index=True)
    gene_symbol = models.CharField(max_length=255)
    created_at = models.DateField(auto_now=True)
    updated_at = models.DateField(auto_now=True)
    species = models.CharField(choices=SpeciesType.SPECIES_CHOICES, max_length=255)
    brain = models.BooleanField()  # This is pre-determined by...

class regulationDirection(enum.Enum):
    UP = "UP"
    DOWN = "DOWN"

class IniaGene(models.Model):  # Genes we do through experimentation
    '''IniaGenes are like data points that are collected from an experiment.  You use Homologene to convert across
    species for geneSymbol name.
    There can be multiple hologenes for the SAME species with the SAME group id.... those were CSVs in another app...

    '''

    DIRECTION_UP = "UP"
    DIRECTION_DOWN = "DOWN"

    DIRECTION_CHOICES = (
        (DIRECTION_UP, "UP"),
        (DIRECTION_DOWN, "DOWN")
    )


    legacy_id = models.IntegerField(db_index=True)  # From version 1.
    uniqueID = models.CharField(max_length=255)  # This is some NIH variable.  WE should name it something better.
    microarray = models.CharField(max_length=255)
    model = models.CharField(max_length=255)
    phenotype = models.CharField(max_length=255)
    species = models.CharField(max_length=255, choices=SpeciesType.SPECIES_CHOICES)
    brain_region = models.CharField(max_length=255)
    paradigm = models.CharField(max_length=255)
    paradigm_duration = models.CharField(max_length=255)
    alcohol = models.BooleanField()
    gene_symbol = models.CharField(max_length=255, blank=True)
    gene_name = models.CharField(max_length=255)
    p_value = models.FloatField(null=True, blank=True)  # stats
    fdr = models.FloatField()   # false discovery rate
    direction = models.CharField(max_length=255, choices=DIRECTION_CHOICES)
    publication = models.ForeignKey(Publication, on_delete=models.PROTECT)
    dataset = models.ForeignKey(Dataset, on_delete=models.PROTECT)
    homologenes = models.ManyToManyField(Homologene)
    updated = models.DateTimeField(auto_now=True)


     # some way to do coinverison here?

class GeneAliases(models.Model):
    ''' This model contains the relationship between the allowed gene aliases per IniaGene.  No real hard checks here...
    allow pretty much whatever.
    '''
    symbol = models.CharField(max_length=255)
    IniaGene = models.ForeignKey(IniaGene, on_delete=models.CASCADE)
