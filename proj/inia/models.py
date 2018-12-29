from django.db import models
from django_enumfield import enum

class Species (enum.ENUM):
    ''' The values of these enums are based on the NCBI taxonomy ID:
    https://www.ncbi.nlm.nih.gov/Taxonomy
    '''
    UNKNOWN = -1
    HOMO_SAPIENS = 9606  # Human
    MUS_MUSCULUS = 10090    # Mouse https://www.uniprot.org/taxonomy/10090
    RATTUS_NORVEGICUS = 10116

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
    species = enum.EnumField(Species)
    brain = models.BooleanField()  # This is pre-determined by...

class IniaGene(models.Model):  # Genes we do through experimentation
    '''IniaGenes are like data points that are collected from an experiment.  You use Homologene to convert across
    species for geneSymbol name.
    There can be multiple hologenes for the SAME species with the SAME group id.... those were CSVs in another app...

    '''

    class regulationDirectionChoices(enum.ENUM):
        UP = "UP"
        DOWN = "DOWN"

    legacy_id = models.IntegerField()  # From version 1.
    uniqueID = models.CharField(max_length=255)  # This is some NIH variable.  WE should name it something better.
    microarray = models.CharField(max_length=255)
    model = models.CharField(max_length=255)
    phenotype = models.CharField(max_length=255)
    species = enum.Enumfield(max_length=255)  ## TODO: Make sepcies something better
    brain_region = models.CharField(max_length=255)
    paradigm = models.CharField(max_length=255)
    paradigm_duration = models.CharField(max_length=255)
    alcohol = models.BooleanField()
    gene_symbol = models.CharField(max_length=255)
    gene_name = models.CharField(max_length=255)
    p_value = models.FloatField()  # stats
    fdr = models.FloatField()   # false discovery rate
    direction = enum.EnumField(regulationDirectionChoices)
    publication = models.ForeignKey(Publication)
    dataset = models.ForeignKey(Dataset)
    updated = models.DateTimeField(auto_now=True)


     # some way to do coinverison here?

class GeneAliases(models.Model):
    ''' This model contains the relationship between the allowed gene aliases per IniaGene.  No real hard checks here...
    allow pretty much whatever.
    '''
    symbol = models.CharField(max_length=255)
    IniaGene = models.ForeignKey(IniaGene)

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
    class TreatmentTypes(enum.ENUM):
        # TODO: Maybe expand labels to what these acronyms mean?
        DID = 'DID',
        NONE = 'NONE',
        CIA = 'CIA',
        CHRONIC = 'CHRONIC',
        EOD = 'EOD',
        LPS = 'LPS'

    legacy_id = models.IntegerField()
    name = models.CharField(max_length=100)
    treatment = enum.EnumField(TreatmentTypes)
