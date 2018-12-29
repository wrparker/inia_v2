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


class TreatmentType(enum.Enum):
    DID = "DID"
    NONE = "NONE"
    CIA = "CIA"
    EOD = "EOD"
    LPS = "LPS"

class Dataset(models.Model):
    legacy_id = models.IntegerField()
    name = models.CharField(max_length=100)
    treatment = enum.EnumField(TreatmentType)


class SpeciesType(enum.Enum):
    ''' The values of these enums are based on the NCBI taxonomy ID:
    https://www.ncbi.nlm.nih.gov/Taxonomy
    '''
    UNKNOWN = 'UNKNOWN'
    HOMO_SAPIENS = 'HOMO_SAPIENS'  # Human
    MUS_MUSCULUS = 'MUS_MUSCULUS'    # Mouse https://www.uniprot.org/taxonomy/10090
    RATTUS_NORVEGICUS = 'RATTUS_NORVEGICUS'  # Rat

    labels = {
        HOMO_SAPIENS: 'Human (Homo sapiens)',
        MUS_MUSCULUS: 'Mouse (Mus musculus)',
        RATTUS_NORVEGICUS: 'Rat (Rattus Norvegicus)'
    }


class Homologene(models.Model):
    '''This is basically just a lookup table that is populated by NCBI Homologene Database:
    https://www.ncbi.nlm.nih.gov/homologene
    Items that share the same homlogene_group_id across species are homologenes.
    '''
    homologene_group_id = models.IntegerField()
    gene_symbol = models.CharField(max_length=255)
    created_at = models.DateField(auto_now=True)
    updated_at = models.DateField(auto_now=True)
    species = enum.EnumField(SpeciesType)
    brain = models.BooleanField()  # This is pre-determined by...

class regulationDirection(enum.Enum):
    UP = "UP"
    DOWN = "DOWN"

class IniaGene(models.Model):  # Genes we do through experimentation
    '''IniaGenes are like data points that are collected from an experiment.  You use Homologene to convert across
    species for geneSymbol name.
    There can be multiple hologenes for the SAME species with the SAME group id.... those were CSVs in another app...

    '''


    legacy_id = models.IntegerField()  # From version 1.
    uniqueID = models.CharField(max_length=255)  # This is some NIH variable.  WE should name it something better.
    microarray = models.CharField(max_length=255)
    model = models.CharField(max_length=255)
    phenotype = models.CharField(max_length=255)
    species = enum.EnumField(SpeciesType)  ## TODO: Make sepcies something better
    brain_region = models.CharField(max_length=255)
    paradigm = models.CharField(max_length=255)
    paradigm_duration = models.CharField(max_length=255)
    alcohol = models.BooleanField()
    gene_symbol = models.CharField(max_length=255)
    gene_name = models.CharField(max_length=255)
    p_value = models.FloatField()  # stats
    fdr = models.FloatField()   # false discovery rate
    direction = enum.EnumField(regulationDirection)
    publication = models.ForeignKey(Publication, on_delete=models.PROTECT)
    dataset = models.ForeignKey(Dataset, on_delete=models.PROTECT)
    updated = models.DateTimeField(auto_now=True)


     # some way to do coinverison here?

class GeneAliases(models.Model):
    ''' This model contains the relationship between the allowed gene aliases per IniaGene.  No real hard checks here...
    allow pretty much whatever.
    '''
    symbol = models.CharField(max_length=255)
    IniaGene = models.ForeignKey(IniaGene, on_delete=models.CASCADE)
